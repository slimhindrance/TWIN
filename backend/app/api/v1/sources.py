"""
API endpoints for managing data sources (enhanced for Total Life AI Platform)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.auth import get_current_active_user
from app.models.user import User
from app.services.universal_source_manager import universal_source_manager, DataType

router = APIRouter()


class SourceConnectionRequest(BaseModel):
    """Request model for connecting a new data source"""
    source_type: str
    credentials: Dict[str, Any]
    permissions: Optional[List[str]] = []


class SourceResponse(BaseModel):
    """Response model for source information"""
    type: str
    name: str
    category: str
    connected: bool
    connected_at: Optional[str]
    last_sync: Optional[str]
    summary: Dict[str, Any]


class SyncRequest(BaseModel):
    """Request model for syncing data sources"""
    source_types: Optional[List[str]] = None
    data_types: Optional[List[str]] = None


@router.get("/supported", response_model=List[Dict[str, Any]])
async def get_supported_sources():
    """Get list of all supported data sources"""
    try:
        sources = universal_source_manager.get_supported_sources()
        return sources
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get supported sources: {str(e)}"
        )


@router.post("/connect")
async def connect_source(
    request: SourceConnectionRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Connect a new data source for the current user"""
    try:
        success = await universal_source_manager.connect_source(
            user_id=current_user.id,
            source_type=request.source_type,
            credentials=request.credentials
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect {request.source_type}. Check credentials and try again."
            )
        
        return {
            "message": f"Successfully connected {request.source_type}",
            "source_type": request.source_type,
            "connected_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error connecting source: {str(e)}"
        )


@router.get("/", response_model=List[SourceResponse])
async def get_user_sources(
    current_user: User = Depends(get_current_active_user)
):
    """Get all connected sources for the current user"""
    try:
        sources = await universal_source_manager.get_user_sources(current_user.id)
        return [SourceResponse(**source) for source in sources]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sources: {str(e)}"
        )


@router.post("/sync")
async def sync_sources(
    request: SyncRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Sync data from connected sources"""
    try:
        # Convert string data types to enum
        data_types = None
        if request.data_types:
            data_types = [DataType(dt) for dt in request.data_types if dt in DataType._value2member_map_]
        
        result = await universal_source_manager.sync_all_sources(
            user_id=current_user.id,
            data_types=data_types
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.delete("/{source_type}")
async def disconnect_source(
    source_type: str,
    current_user: User = Depends(get_current_active_user)
):
    """Disconnect a data source"""
    try:
        # For now, just remove from memory
        # In production, would also revoke OAuth tokens
        if current_user.id in universal_source_manager.sources:
            if source_type in universal_source_manager.sources[current_user.id]:
                del universal_source_manager.sources[current_user.id][source_type]
                return {"message": f"Successfully disconnected {source_type}"}
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_type} not found or not connected"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error disconnecting source: {str(e)}"
        )


# =============================================================================
# YNAB SPECIFIC ENDPOINTS
# =============================================================================

class YNABConnectionRequest(BaseModel):
    """YNAB connection request"""
    access_token: str


@router.post("/ynab/connect")
async def connect_ynab(
    request: YNABConnectionRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Connect YNAB account using personal access token"""
    try:
        success = await universal_source_manager.connect_source(
            user_id=current_user.id,
            source_type="ynab",
            credentials={"access_token": request.access_token}
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to connect YNAB. Please check your access token and try again."
            )
        
        # Perform initial sync
        sync_result = await universal_source_manager.sync_all_sources(
            user_id=current_user.id,
            data_types=[DataType.TRANSACTIONS]
        )
        
        return {
            "message": "Successfully connected YNAB",
            "connection_status": "active",
            "sync_result": sync_result,
            "next_steps": [
                "Your YNAB data is now being processed",
                "You can query your budget and spending patterns",
                "Financial insights will be available shortly"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"YNAB connection error: {str(e)}"
        )


@router.get("/ynab/budgets")
async def get_ynab_budgets(
    current_user: User = Depends(get_current_active_user)
):
    """Get YNAB budget information"""
    try:
        if current_user.id not in universal_source_manager.sources:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No data sources connected"
            )
        
        if "ynab" not in universal_source_manager.sources[current_user.id]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="YNAB not connected. Please connect your YNAB account first."
            )
        
        ynab_source = universal_source_manager.sources[current_user.id]["ynab"]
        data = await ynab_source.fetch_data([DataType.TRANSACTIONS])
        
        return {
            "budgets": data.get("budgets", []),
            "categories": data.get("categories", []),
            "summary": await ynab_source.get_data_summary()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get YNAB budgets: {str(e)}"
        )


@router.get("/ynab/transactions")
async def get_ynab_transactions(
    current_user: User = Depends(get_current_active_user),
    limit: int = 100
):
    """Get recent YNAB transactions"""
    try:
        if current_user.id not in universal_source_manager.sources or \
           "ynab" not in universal_source_manager.sources[current_user.id]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="YNAB not connected"
            )
        
        ynab_source = universal_source_manager.sources[current_user.id]["ynab"]
        data = await ynab_source.fetch_data([DataType.TRANSACTIONS])
        
        transactions = data.get("transactions", [])[:limit]
        
        return {
            "transactions": transactions,
            "total_count": len(data.get("transactions", [])),
            "returned_count": len(transactions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get YNAB transactions: {str(e)}"
        )


@router.get("/ynab/insights")
async def get_ynab_insights(
    current_user: User = Depends(get_current_active_user)
):
    """Get AI-powered financial insights from YNAB data"""
    try:
        if current_user.id not in universal_source_manager.sources or \
           "ynab" not in universal_source_manager.sources[current_user.id]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="YNAB not connected"
            )
        
        ynab_source = universal_source_manager.sources[current_user.id]["ynab"]
        data = await ynab_source.fetch_data([DataType.TRANSACTIONS])
        transactions = data.get("transactions", [])
        
        # Generate basic financial insights
        insights = _generate_financial_insights(transactions)
        
        return {
            "insights": insights,
            "data_period": "All available data",
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insights: {str(e)}"
        )


def _generate_financial_insights(transactions: List[Dict]) -> Dict[str, Any]:
    """Generate basic financial insights from transaction data"""
    if not transactions:
        return {"message": "No transaction data available for analysis"}
    
    # Basic analysis
    total_spending = sum(abs(t["amount"]) for t in transactions if t["amount"] < 0)
    total_income = sum(t["amount"] for t in transactions if t["amount"] > 0)
    
    # Category analysis
    category_spending = {}
    for transaction in transactions:
        if transaction["amount"] < 0:  # Only spending
            category = transaction.get("category", "Uncategorized")
            category_spending[category] = category_spending.get(category, 0) + abs(transaction["amount"])
    
    # Top spending categories
    top_categories = sorted(category_spending.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "total_spending": total_spending,
        "total_income": total_income,
        "net_cash_flow": total_income - total_spending,
        "transaction_count": len(transactions),
        "top_spending_categories": [
            {"category": cat, "amount": amount, "percentage": round(amount/total_spending*100, 1)}
            for cat, amount in top_categories
        ],
        "insights": [
            f"You've had {len(transactions)} transactions analyzed",
            f"Your top spending category is {top_categories[0][0] if top_categories else 'Unknown'}",
            f"Net cash flow: {'Positive' if total_income > total_spending else 'Negative'}",
            "Connect more data sources for deeper insights across your entire life!"
        ]
    }