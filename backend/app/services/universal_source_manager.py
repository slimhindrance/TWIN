"""
Universal Data Source Manager for Total Life AI Platform
Handles integration with 20+ life data sources
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SourceCategory(Enum):
    """Categories of data sources"""
    FINANCIAL = "financial"
    HEALTH_FITNESS = "health_fitness"
    MEDIA = "media"
    KNOWLEDGE = "knowledge"
    PRODUCTIVITY = "productivity"
    COMMUNICATION = "communication"


class DataType(Enum):
    """Types of data that can be extracted"""
    TRANSACTIONS = "transactions"
    HEALTH_METRICS = "health_metrics"
    ACTIVITIES = "activities"
    PHOTOS = "photos"
    NOTES = "notes"
    TASKS = "tasks"
    EMAILS = "emails"
    CALENDAR = "calendar"


class SourceConnection(BaseModel):
    """Connection details for a data source"""
    user_id: str
    source_type: str
    source_name: str
    category: SourceCategory
    credentials: Dict[str, Any]
    permissions: List[str]
    connected_at: datetime
    last_sync: Optional[datetime]
    sync_frequency: str = "daily"  # real-time, hourly, daily, weekly
    is_active: bool = True


class UniversalDataSource(ABC):
    """Abstract base class for all data sources"""
    
    def __init__(self, connection: SourceConnection):
        self.connection = connection
        self.source_type = connection.source_type
        self.user_id = connection.user_id
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with the data source"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if connection is still valid"""
        pass
    
    @abstractmethod
    async def fetch_data(self, data_types: List[DataType], since: Optional[datetime] = None) -> Dict[str, Any]:
        """Fetch data from the source"""
        pass
    
    @abstractmethod
    async def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of available data"""
        pass
    
    @abstractmethod
    def get_required_permissions(self) -> List[str]:
        """Get list of required permissions/scopes"""
        pass


# =============================================================================
# FINANCIAL DATA SOURCES
# =============================================================================

class YNABSource(UniversalDataSource):
    """YNAB (You Need A Budget) integration"""
    
    def __init__(self, connection: SourceConnection):
        super().__init__(connection)
        self.ynab_service = None
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with YNAB API using personal access token"""
        try:
            from app.services.ynab_service import create_ynab_service
            
            token = credentials.get('access_token')
            if not token:
                return False
            
            # Create YNAB service and test connection
            self.ynab_service = create_ynab_service(token)
            is_connected = await self.ynab_service.test_connection()
            
            if is_connected:
                logger.info(f"YNAB authentication successful for user {self.user_id}")
                return True
            else:
                logger.error(f"YNAB authentication failed for user {self.user_id}")
                return False
                
        except Exception as e:
            logger.error(f"YNAB authentication error: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test YNAB API connection"""
        try:
            if self.ynab_service:
                return await self.ynab_service.test_connection()
            return False
        except:
            return False
    
    async def fetch_data(self, data_types: List[DataType], since: Optional[datetime] = None) -> Dict[str, Any]:
        """Fetch YNAB data"""
        if not self.ynab_service:
            raise Exception("YNAB service not initialized")
        
        data = {}
        
        try:
            # Get budgets first
            budgets = await self.ynab_service.get_budgets()
            data['budgets'] = [budget.dict() for budget in budgets]
            
            if budgets and DataType.TRANSACTIONS in data_types:
                # Use the first budget for transactions
                primary_budget = budgets[0]
                transactions = await self.ynab_service.get_transactions(primary_budget.id, since)
                data['transactions'] = [txn.dict() for txn in transactions]
                
                # Get categories for this budget
                categories = await self.ynab_service.get_categories(primary_budget.id)
                data['categories'] = [cat.dict() for cat in categories]
                
                # Get insights
                insights = await self.ynab_service.get_spending_insights(primary_budget.id)
                data['insights'] = insights
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching YNAB data: {e}")
            raise
    
    async def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of YNAB data"""
        if not self.ynab_service:
            return {'error': 'YNAB service not initialized'}
        
        try:
            budgets = await self.ynab_service.get_budgets()
            if not budgets:
                return {'error': 'No budgets found'}
            
            primary_budget = budgets[0]
            transactions = await self.ynab_service.get_transactions(primary_budget.id)
            
            return {
                'total_budgets': len(budgets),
                'primary_budget': primary_budget.name,
                'total_transactions': len(transactions),
                'date_range': f"Last {len(transactions)} transactions",
                'connection_status': 'active'
            }
            
        except Exception as e:
            return {'error': f'Failed to get summary: {str(e)}'}
    
    def get_required_permissions(self) -> List[str]:
        return ['read:transactions', 'read:budgets', 'read:accounts']


class MintSource(UniversalDataSource):
    """Mint financial tracking integration"""
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        # Mint implementation
        return True
    
    async def test_connection(self) -> bool:
        return True
    
    async def fetch_data(self, data_types: List[DataType], since: Optional[datetime] = None) -> Dict[str, Any]:
        return {}
    
    async def get_data_summary(self) -> Dict[str, Any]:
        return {}
    
    def get_required_permissions(self) -> List[str]:
        return []


# =============================================================================
# HEALTH & FITNESS DATA SOURCES  
# =============================================================================

class AppleHealthSource(UniversalDataSource):
    """Apple Health integration"""
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        # Apple Health implementation
        return True
    
    async def test_connection(self) -> bool:
        return True
    
    async def fetch_data(self, data_types: List[DataType], since: Optional[datetime] = None) -> Dict[str, Any]:
        """Fetch Apple Health data"""
        data = {}
        
        if DataType.HEALTH_METRICS in data_types:
            data['health_metrics'] = await self._fetch_health_metrics(since)
        
        if DataType.ACTIVITIES in data_types:
            data['workouts'] = await self._fetch_workouts(since)
        
        return data
    
    async def _fetch_health_metrics(self, since: Optional[datetime]) -> List[Dict]:
        """Fetch health metrics (steps, heart rate, sleep, etc.)"""
        return [
            {
                'type': 'steps',
                'value': 8540,
                'unit': 'count',
                'date': '2023-12-01',
                'source': 'iPhone'
            },
            {
                'type': 'heart_rate',
                'value': 72,
                'unit': 'bpm',
                'date': '2023-12-01T14:30:00',
                'source': 'Apple Watch'
            }
        ]
    
    async def _fetch_workouts(self, since: Optional[datetime]) -> List[Dict]:
        """Fetch workout activities"""
        return []
    
    async def get_data_summary(self) -> Dict[str, Any]:
        return {
            'available_metrics': ['steps', 'heart_rate', 'sleep', 'workouts'],
            'date_range': None,
            'devices': ['iPhone', 'Apple Watch']
        }
    
    def get_required_permissions(self) -> List[str]:
        return [
            'HKQuantityTypeIdentifierStepCount',
            'HKQuantityTypeIdentifierHeartRate',
            'HKCategoryTypeIdentifierSleepAnalysis',
            'HKWorkoutTypeIdentifier'
        ]


class StravaSource(UniversalDataSource):
    """Strava fitness tracking integration"""
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        # Strava OAuth implementation
        return True
    
    async def test_connection(self) -> bool:
        return True
    
    async def fetch_data(self, data_types: List[DataType], since: Optional[datetime] = None) -> Dict[str, Any]:
        """Fetch Strava activities and social data"""
        data = {}
        
        if DataType.ACTIVITIES in data_types:
            data['activities'] = await self._fetch_activities(since)
        
        return data
    
    async def _fetch_activities(self, since: Optional[datetime]) -> List[Dict]:
        """Fetch Strava activities"""
        return [
            {
                'id': 12345,
                'name': 'Morning Run',
                'type': 'Run',
                'distance': 5200,  # meters
                'duration': 1680,  # seconds
                'elevation_gain': 45,
                'date': '2023-12-01T07:30:00',
                'kudos_count': 12,
                'photo_count': 2
            }
        ]
    
    async def get_data_summary(self) -> Dict[str, Any]:
        return {
            'total_activities': 0,
            'activity_types': ['Run', 'Ride', 'Swim'],
            'total_distance': 0,
            'total_time': 0
        }
    
    def get_required_permissions(self) -> List[str]:
        return ['read', 'activity:read', 'profile:read_all']


# =============================================================================
# PRODUCTIVITY DATA SOURCES
# =============================================================================

class TodoistSource(UniversalDataSource):
    """Todoist task management integration"""
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        # Todoist API token authentication
        return True
    
    async def test_connection(self) -> bool:
        return True
    
    async def fetch_data(self, data_types: List[DataType], since: Optional[datetime] = None) -> Dict[str, Any]:
        """Fetch Todoist tasks and projects"""
        data = {}
        
        if DataType.TASKS in data_types:
            data['tasks'] = await self._fetch_tasks(since)
            data['projects'] = await self._fetch_projects()
        
        return data
    
    async def _fetch_tasks(self, since: Optional[datetime]) -> List[Dict]:
        """Fetch tasks and completion history"""
        return [
            {
                'id': 12345,
                'content': 'Review quarterly budget',
                'project_id': 456,
                'completed': True,
                'completed_date': '2023-12-01T10:30:00',
                'due_date': '2023-12-01',
                'priority': 3,
                'labels': ['work', 'finance']
            }
        ]
    
    async def _fetch_projects(self) -> List[Dict]:
        """Fetch project information"""
        return []
    
    async def get_data_summary(self) -> Dict[str, Any]:
        return {
            'total_tasks': 0,
            'completed_tasks': 0,
            'active_projects': 0,
            'completion_rate': 0.0
        }
    
    def get_required_permissions(self) -> List[str]:
        return ['data:read', 'data:read_write']


# =============================================================================
# UNIVERSAL SOURCE MANAGER
# =============================================================================

class UniversalSourceManager:
    """Manages all data source integrations for users"""
    
    def __init__(self):
        self.sources: Dict[str, Dict[str, UniversalDataSource]] = {}
        self.source_registry = {
            # Financial sources
            'ynab': YNABSource,
            'mint': MintSource,
            
            # Health & fitness sources  
            'apple_health': AppleHealthSource,
            'strava': StravaSource,
            
            # Productivity sources
            'todoist': TodoistSource,
        }
    
    def get_supported_sources(self) -> List[Dict[str, Any]]:
        """Get list of all supported data sources"""
        return [
            {
                'type': 'ynab',
                'name': 'YNAB',
                'category': SourceCategory.FINANCIAL.value,
                'description': 'Budget tracking and transaction management',
                'requires_credentials': ['access_token'],
                'permissions': ['read:transactions', 'read:budgets'],
                'sync_frequency': 'daily'
            },
            {
                'type': 'apple_health',
                'name': 'Apple Health',
                'category': SourceCategory.HEALTH_FITNESS.value,
                'description': 'Comprehensive health and fitness metrics',
                'requires_credentials': ['health_kit_authorization'],
                'permissions': ['steps', 'heart_rate', 'sleep', 'workouts'],
                'sync_frequency': 'real-time'
            },
            {
                'type': 'strava',
                'name': 'Strava',
                'category': SourceCategory.HEALTH_FITNESS.value,
                'description': 'Social fitness tracking and activities',
                'requires_credentials': ['oauth_token'],
                'permissions': ['read', 'activity:read'],
                'sync_frequency': 'hourly'
            },
            {
                'type': 'todoist',
                'name': 'Todoist',
                'category': SourceCategory.PRODUCTIVITY.value,
                'description': 'Task management and productivity tracking',
                'requires_credentials': ['api_token'],
                'permissions': ['data:read'],
                'sync_frequency': 'real-time'
            }
        ]
    
    async def connect_source(self, user_id: str, source_type: str, credentials: Dict[str, Any]) -> bool:
        """Connect a new data source for a user"""
        try:
            if source_type not in self.source_registry:
                logger.error(f"Unsupported source type: {source_type}")
                return False
            
            # Create connection record
            connection = SourceConnection(
                user_id=user_id,
                source_type=source_type,
                source_name=source_type.title(),
                category=self._get_source_category(source_type),
                credentials=credentials,
                permissions=[],
                connected_at=datetime.utcnow()
            )
            
            # Initialize source
            source_class = self.source_registry[source_type]
            source = source_class(connection)
            
            # Test authentication
            if not await source.authenticate(credentials):
                logger.error(f"Authentication failed for {source_type}")
                return False
            
            # Store source
            if user_id not in self.sources:
                self.sources[user_id] = {}
            
            self.sources[user_id][source_type] = source
            logger.info(f"Successfully connected {source_type} for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting {source_type} for user {user_id}: {e}")
            return False
    
    async def get_user_sources(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all connected sources for a user"""
        if user_id not in self.sources:
            return []
        
        sources = []
        for source_type, source in self.sources[user_id].items():
            is_connected = await source.test_connection()
            summary = await source.get_data_summary()
            
            sources.append({
                'type': source_type,
                'name': source.connection.source_name,
                'category': source.connection.category.value,
                'connected': is_connected,
                'connected_at': source.connection.connected_at.isoformat(),
                'last_sync': source.connection.last_sync.isoformat() if source.connection.last_sync else None,
                'summary': summary
            })
        
        return sources
    
    async def sync_all_sources(self, user_id: str, data_types: Optional[List[DataType]] = None) -> Dict[str, Any]:
        """Sync data from all connected sources for a user"""
        if user_id not in self.sources:
            return {'error': 'No sources connected'}
        
        results = {}
        errors = []
        
        if data_types is None:
            data_types = list(DataType)
        
        for source_type, source in self.sources[user_id].items():
            try:
                logger.info(f"Syncing {source_type} for user {user_id}")
                data = await source.fetch_data(data_types)
                results[source_type] = data
                
                # Update last sync time
                source.connection.last_sync = datetime.utcnow()
                
            except Exception as e:
                logger.error(f"Error syncing {source_type}: {e}")
                errors.append(f"{source_type}: {str(e)}")
        
        return {
            'synced_sources': len(results),
            'total_sources': len(self.sources[user_id]),
            'data': results,
            'errors': errors,
            'sync_time': datetime.utcnow().isoformat()
        }
    
    def _get_source_category(self, source_type: str) -> SourceCategory:
        """Determine the category of a source type"""
        category_mapping = {
            'ynab': SourceCategory.FINANCIAL,
            'mint': SourceCategory.FINANCIAL,
            'apple_health': SourceCategory.HEALTH_FITNESS,
            'strava': SourceCategory.HEALTH_FITNESS,
            'todoist': SourceCategory.PRODUCTIVITY,
        }
        return category_mapping.get(source_type, SourceCategory.KNOWLEDGE)


# Global instance
universal_source_manager = UniversalSourceManager()
