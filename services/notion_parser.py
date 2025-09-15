"""
Notion integration for Digital Twin
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from notion_client import Client
from notion_client.errors import NotionClientError

from services.knowledge_source import KnowledgeSource

logger = logging.getLogger(__name__)


class NotionParser(KnowledgeSource):
    """Parser for Notion workspaces."""
    
    def __init__(self):
        """Initialize the Notion parser."""
        self.client: Optional[Client] = None
        self.user_id: Optional[str] = None
    
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with user's Notion API token."""
        try:
            api_token = credentials.get('notion_api_token')
            if not api_token:
                logger.error("No Notion API token provided")
                return False
            
            self.client = Client(auth=api_token)
            
            # Test the connection by getting user info
            user_info = self.client.users.me()
            self.user_id = user_info.get('id')
            
            logger.info(f"Successfully authenticated with Notion for user {self.user_id}")
            return True
            
        except NotionClientError as e:
            logger.error(f"Notion authentication failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during Notion authentication: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test if Notion connection is working."""
        if not self.client:
            return False
        
        try:
            self.client.users.me()
            return True
        except NotionClientError:
            return False
        except Exception:
            return False
    
    async def fetch_all_documents(self) -> List[Dict[str, Any]]:
        """Fetch all accessible pages from Notion."""
        if not self.client:
            raise ValueError("Not authenticated with Notion")
        
        documents = []
        has_more = True
        start_cursor = None
        
        try:
            while has_more:
                # Search for all pages user has access to
                search_params = {
                    "filter": {
                        "property": "object",
                        "value": "page"
                    },
                    "page_size": 100
                }
                
                if start_cursor:
                    search_params["start_cursor"] = start_cursor
                
                results = self.client.search(search_params)
                
                for page in results.get('results', []):
                    try:
                        parsed_doc = self.parse_document(page)
                        if parsed_doc:
                            documents.append(parsed_doc)
                    except Exception as e:
                        logger.error(f"Error parsing Notion page {page.get('id')}: {e}")
                        continue
                
                has_more = results.get('has_more', False)
                start_cursor = results.get('next_cursor')
            
            logger.info(f"Fetched {len(documents)} documents from Notion")
            return documents
            
        except NotionClientError as e:
            logger.error(f"Error fetching Notion documents: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching Notion documents: {e}")
            return []
    
    async def get_document_count(self) -> int:
        """Get total number of accessible Notion pages."""
        if not self.client:
            return 0
            
        try:
            results = self.client.search({
                "filter": {
                    "property": "object", 
                    "value": "page"
                },
                "page_size": 1  # We just want the count
            })
            
            # Note: Notion API doesn't return total count directly
            # This is an approximation - for exact count we'd need to paginate through all
            return len(results.get('results', []))
            
        except NotionClientError:
            return 0
        except Exception:
            return 0
    
    def parse_document(self, page: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a Notion page into standard document format."""
        try:
            page_id = page.get('id')
            if not page_id:
                return None
            
            # Get page content
            content = self._extract_page_content(page_id)
            if not content.strip():
                logger.debug(f"Empty content for Notion page {page_id}")
                return None
            
            # Extract metadata
            properties = page.get('properties', {})
            title = self._extract_title(properties, page)
            tags = self._extract_tags(properties)
            
            created_time = page.get('created_time')
            last_edited = page.get('last_edited_time')
            
            # Build metadata following same structure as Obsidian
            metadata = {
                'title': title or 'Untitled Notion Page',
                'source': f"notion/{title or page_id}",
                'notion_page_id': page_id,
                'created_at': created_time,
                'modified_at': last_edited,
                'tags': tags,
                'url': page.get('url', ''),
                'type': 'notion_page',
                'parent_id': self._get_parent_id(page.get('parent')),
                'properties': properties,
                'archived': page.get('archived', False)
            }
            
            # Chunk content same way as Obsidian
            chunks = self.chunk_content(content)
            
            return {
                'content': content,
                'plain_text': content,  # Already plain text from extraction
                'metadata': metadata,
                'chunks': chunks
            }
            
        except Exception as e:
            logger.error(f"Error parsing Notion page {page.get('id')}: {e}")
            return None
    
    def _extract_page_content(self, page_id: str) -> str:
        """Extract text content from a Notion page."""
        try:
            content_parts = []
            has_more = True
            start_cursor = None
            
            while has_more:
                params = {"page_size": 100}
                if start_cursor:
                    params["start_cursor"] = start_cursor
                    
                blocks = self.client.blocks.children.list(page_id, **params)
                
                for block in blocks.get('results', []):
                    text = self._extract_block_text(block)
                    if text:
                        content_parts.append(text)
                
                has_more = blocks.get('has_more', False)
                start_cursor = blocks.get('next_cursor')
            
            return '\n\n'.join(content_parts)
            
        except NotionClientError as e:
            logger.error(f"Error extracting content from Notion page {page_id}: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error extracting Notion page content: {e}")
            return ""
    
    def _extract_block_text(self, block: Dict[str, Any]) -> str:
        """Extract text from a Notion block."""
        block_type = block.get('type')
        
        # Handle different block types
        text_blocks = ['paragraph', 'heading_1', 'heading_2', 'heading_3', 
                      'bulleted_list_item', 'numbered_list_item', 'quote', 'callout']
        
        if block_type in text_blocks:
            block_content = block.get(block_type, {})
            rich_text = block_content.get('rich_text', [])
            text = ''.join([text_obj.get('plain_text', '') for text_obj in rich_text])
            
            # Add formatting for headings
            if block_type.startswith('heading_'):
                level = block_type[-1]
                text = '#' * int(level) + ' ' + text
                
            return text
        
        elif block_type == 'code':
            code_content = block.get('code', {})
            rich_text = code_content.get('rich_text', [])
            code_text = ''.join([text_obj.get('plain_text', '') for text_obj in rich_text])
            language = code_content.get('language', '')
            return f'```{language}\n{code_text}\n```'
        
        elif block_type == 'divider':
            return '---'
        
        elif block_type == 'table_of_contents':
            return '[Table of Contents]'
        
        # For unsupported block types, return empty string
        return ""
    
    def _extract_title(self, properties: Dict[str, Any], page: Dict[str, Any]) -> Optional[str]:
        """Extract title from Notion page properties or page object."""
        # First try to get from properties
        for prop_name, prop_data in properties.items():
            if prop_data.get('type') == 'title':
                title_array = prop_data.get('title', [])
                title = ''.join([t.get('plain_text', '') for t in title_array])
                if title:
                    return title
        
        # Fallback to checking if there's a parent with a title
        parent = page.get('parent', {})
        if parent.get('type') == 'page_id':
            return f"Subpage of {parent.get('page_id', 'Unknown')}"
        
        return None
    
    def _extract_tags(self, properties: Dict[str, Any]) -> List[str]:
        """Extract tags from Notion page properties."""
        tags = []
        
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get('type')
            
            # Multi-select properties (common for tags)
            if prop_type == 'multi_select':
                multi_select = prop_data.get('multi_select', [])
                tags.extend([tag.get('name', '') for tag in multi_select if tag.get('name')])
            
            # Select properties  
            elif prop_type == 'select':
                select = prop_data.get('select')
                if select and select.get('name'):
                    tags.append(select.get('name'))
            
            # Status properties (new Notion feature)
            elif prop_type == 'status':
                status = prop_data.get('status')
                if status and status.get('name'):
                    tags.append(f"status:{status.get('name')}")
        
        return [tag for tag in tags if tag]
    
    def _get_parent_id(self, parent: Dict[str, Any]) -> Optional[str]:
        """Extract parent ID from parent object."""
        if not parent:
            return None
            
        parent_type = parent.get('type')
        if parent_type == 'page_id':
            return parent.get('page_id')
        elif parent_type == 'database_id':
            return parent.get('database_id')
        elif parent_type == 'workspace':
            return 'workspace'
        
        return None
