"""
YNAB (You Need A Budget) API Integration Service
Handles connection to YNAB API and data retrieval
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import aiohttp
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class YNABTransaction(BaseModel):
    """YNAB transaction model"""
    id: str
    date: str
    amount: float  # In dollars (converted from milliunits)
    payee: Optional[str]
    category: Optional[str]
    account: str
    cleared: bool
    memo: Optional[str] = None
    budget_id: str


class YNABBudget(BaseModel):
    """YNAB budget model"""
    id: str
    name: str
    currency_format: Dict[str, Any]
    date_format: Dict[str, Any]
    first_month: str
    last_month: str


class YNABCategory(BaseModel):
    """YNAB category model"""
    id: str
    name: str
    category_group_id: str
    category_group_name: str
    budgeted: float
    activity: float
    balance: float


class YNABService:
    """Service for interacting with YNAB API"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.youneedabudget.com/v1"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
    
    async def test_connection(self) -> bool:
        """Test the YNAB API connection"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/user",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        logger.info("YNAB connection test successful")
                        return True
                    else:
                        logger.error(f"YNAB connection test failed: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"YNAB connection test error: {e}")
            return False
    
    async def get_budgets(self) -> List[YNABBudget]:
        """Get all budgets from YNAB"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/budgets",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        budgets = []
                        for budget_data in data["data"]["budgets"]:
                            budgets.append(YNABBudget(**budget_data))
                        return budgets
                    else:
                        logger.error(f"Failed to get budgets: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error getting budgets: {e}")
            return []
    
    async def get_transactions(self, budget_id: str, since_date: Optional[datetime] = None) -> List[YNABTransaction]:
        """Get transactions from a specific budget"""
        try:
            url = f"{self.base_url}/budgets/{budget_id}/transactions"
            params = {}
            
            if since_date:
                params["since_date"] = since_date.strftime("%Y-%m-%d")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        transactions = []
                        
                        for txn_data in data["data"]["transactions"]:
                            # Convert milliunits to dollars
                            amount_dollars = txn_data["amount"] / 1000.0
                            
                            # Get account and category names
                            account_name = await self._get_account_name(budget_id, txn_data["account_id"])
                            category_name = await self._get_category_name(budget_id, txn_data["category_id"]) if txn_data.get("category_id") else None
                            
                            transaction = YNABTransaction(
                                id=txn_data["id"],
                                date=txn_data["date"],
                                amount=amount_dollars,
                                payee=txn_data.get("payee_name"),
                                category=category_name,
                                account=account_name,
                                cleared=txn_data["cleared"] == "cleared",
                                memo=txn_data.get("memo"),
                                budget_id=budget_id
                            )
                            transactions.append(transaction)
                        
                        return transactions
                    else:
                        logger.error(f"Failed to get transactions: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error getting transactions: {e}")
            return []
    
    async def get_categories(self, budget_id: str) -> List[YNABCategory]:
        """Get budget categories"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/budgets/{budget_id}/categories",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        categories = []
                        
                        for group in data["data"]["category_groups"]:
                            group_name = group["name"]
                            for cat_data in group.get("categories", []):
                                category = YNABCategory(
                                    id=cat_data["id"],
                                    name=cat_data["name"],
                                    category_group_id=group["id"],
                                    category_group_name=group_name,
                                    budgeted=cat_data["budgeted"] / 1000.0,
                                    activity=cat_data["activity"] / 1000.0,
                                    balance=cat_data["balance"] / 1000.0
                                )
                                categories.append(category)
                        
                        return categories
                    else:
                        logger.error(f"Failed to get categories: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    async def _get_account_name(self, budget_id: str, account_id: str) -> str:
        """Get account name by ID (with caching)"""
        try:
            # In a real implementation, you'd cache this
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/budgets/{budget_id}/accounts/{account_id}",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["data"]["account"]["name"]
                    return "Unknown Account"
        except:
            return "Unknown Account"
    
    async def _get_category_name(self, budget_id: str, category_id: str) -> str:
        """Get category name by ID (with caching)"""
        try:
            # In a real implementation, you'd cache this
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/budgets/{budget_id}/categories/{category_id}",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["data"]["category"]["name"]
                    return "Unknown Category"
        except:
            return "Unknown Category"
    
    async def get_spending_insights(self, budget_id: str, days: int = 30) -> Dict[str, Any]:
        """Generate spending insights for the last N days"""
        try:
            since_date = datetime.now() - timedelta(days=days)
            transactions = await self.get_transactions(budget_id, since_date)
            
            if not transactions:
                return {"error": "No transactions found"}
            
            # Analyze spending patterns
            spending_by_category = {}
            total_spending = 0
            spending_transactions = []
            
            for txn in transactions:
                if txn.amount < 0:  # Spending (negative in YNAB)
                    amount = abs(txn.amount)
                    total_spending += amount
                    spending_transactions.append(txn)
                    
                    category = txn.category or "Uncategorized"
                    spending_by_category[category] = spending_by_category.get(category, 0) + amount
            
            # Top spending categories
            top_categories = sorted(spending_by_category.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Daily averages
            daily_average = total_spending / days if days > 0 else 0
            
            return {
                "period_days": days,
                "total_spending": total_spending,
                "daily_average": daily_average,
                "transaction_count": len(spending_transactions),
                "categories": {
                    "total_categories": len(spending_by_category),
                    "top_categories": [
                        {
                            "name": cat,
                            "amount": amount,
                            "percentage": round(amount/total_spending*100, 1)
                        }
                        for cat, amount in top_categories
                    ]
                },
                "insights": [
                    f"You spent ${total_spending:.2f} over the last {days} days",
                    f"That's an average of ${daily_average:.2f} per day",
                    f"Your top spending category is {top_categories[0][0] if top_categories else 'Unknown'}",
                    f"You had {len(spending_transactions)} spending transactions"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error generating spending insights: {e}")
            return {"error": f"Failed to generate insights: {str(e)}"}


# Factory function for creating YNAB service instances
def create_ynab_service(access_token: str) -> YNABService:
    """Create a new YNAB service instance"""
    return YNABService(access_token)
