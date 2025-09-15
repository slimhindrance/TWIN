"""
Obsidian vault parser for extracting and processing markdown files.
"""
import os
import re
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

import frontmatter
import markdown
from markdown.extensions import codehilite, fenced_code, tables, toc

logger = logging.getLogger(__name__)


class ObsidianParser:
    """Parser for Obsidian vault files."""
    
    def __init__(self, vault_path: str):
        """Initialize the parser with vault path."""
        self.vault_path = Path(vault_path)
        self.md = markdown.Markdown(
            extensions=[
                'codehilite',
                'fenced_code',
                'tables',
                'toc',
                'attr_list',
                'def_list'
            ]
        )
    
    def is_valid_vault(self) -> bool:
        """Check if the path is a valid Obsidian vault."""
        try:
            return (
                self.vault_path.exists() and
                self.vault_path.is_dir() and
                any(f.suffix == '.md' for f in self.vault_path.rglob('*.md'))
            )
        except Exception as e:
            logger.error(f"Error checking vault validity: {e}")
            return False
    
    def get_all_markdown_files(self) -> List[Path]:
        """Get all markdown files in the vault."""
        try:
            # Exclude common Obsidian system folders
            excluded_patterns = {
                '.obsidian',
                '.trash',
                'node_modules',
                '.git'
            }
            
            markdown_files = []
            for md_file in self.vault_path.rglob('*.md'):
                # Check if file is in excluded directory
                if any(excluded in md_file.parts for excluded in excluded_patterns):
                    continue
                markdown_files.append(md_file)
            
            logger.info(f"Found {len(markdown_files)} markdown files in vault")
            return markdown_files
            
        except Exception as e:
            logger.error(f"Error getting markdown files: {e}")
            return []
    
    def extract_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """Extract frontmatter and content from markdown."""
        try:
            post = frontmatter.loads(content)
            return post.metadata, post.content
        except Exception as e:
            logger.warning(f"Failed to parse frontmatter: {e}")
            return {}, content
    
    def extract_wikilinks(self, content: str) -> List[str]:
        """Extract Obsidian wikilinks [[link]] from content."""
        wikilink_pattern = r'\[\[([^\]]+)\]\]'
        return re.findall(wikilink_pattern, content)
    
    def extract_tags(self, content: str, frontmatter_tags: List[str] = None) -> List[str]:
        """Extract tags from content and frontmatter."""
        tags = set()
        
        # Add frontmatter tags
        if frontmatter_tags:
            if isinstance(frontmatter_tags, str):
                tags.add(frontmatter_tags)
            elif isinstance(frontmatter_tags, list):
                tags.update(frontmatter_tags)
        
        # Extract inline tags (#tag)
        tag_pattern = r'#([a-zA-Z0-9_/-]+)'
        inline_tags = re.findall(tag_pattern, content)
        tags.update(inline_tags)
        
        return list(tags)
    
    def extract_headings(self, content: str) -> List[Dict[str, Any]]:
        """Extract markdown headings from content."""
        heading_pattern = r'^(#{1,6})\s+(.+)$'
        headings = []
        
        for i, line in enumerate(content.split('\n')):
            match = re.match(heading_pattern, line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append({
                    'level': level,
                    'text': text,
                    'line_number': i + 1
                })
        
        return headings
    
    def chunk_content(self, content: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split content into overlapping chunks."""
        if not content or len(content) <= chunk_size:
            return [content] if content else []
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Try to break at a sentence boundary
            if end < len(content):
                # Look for sentence endings near the chunk boundary
                for i in range(end, max(end - 100, start), -1):
                    if content[i] in '.!?':
                        end = i + 1
                        break
                else:
                    # Look for word boundaries
                    for i in range(end, max(end - 50, start), -1):
                        if content[i].isspace():
                            end = i
                            break
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = max(start + chunk_size - overlap, end)
        
        return chunks
    
    def parse_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse a single markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if not content.strip():
                logger.warning(f"Empty file: {file_path}")
                return None
            
            # Extract frontmatter and content
            frontmatter_data, markdown_content = self.extract_frontmatter(content)
            
            # Get file stats
            stat = file_path.stat()
            
            # Extract various elements
            wikilinks = self.extract_wikilinks(markdown_content)
            tags = self.extract_tags(
                markdown_content, 
                frontmatter_data.get('tags', [])
            )
            headings = self.extract_headings(markdown_content)
            
            # Convert markdown to plain text for better searchability
            plain_text = self.md.convert(markdown_content)
            # Remove HTML tags for cleaner text
            plain_text = re.sub(r'<[^>]+>', '', plain_text)
            
            # Build metadata
            metadata = {
                'title': frontmatter_data.get('title', file_path.stem),
                'source': str(file_path.relative_to(self.vault_path)),
                'absolute_path': str(file_path),
                'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'size_bytes': stat.st_size,
                'tags': tags,
                'wikilinks': wikilinks,
                'headings': [h['text'] for h in headings],
                'heading_count': len(headings),
                'frontmatter': frontmatter_data,
                'type': 'obsidian_note'
            }
            
            return {
                'content': markdown_content,
                'plain_text': plain_text,
                'metadata': metadata,
                'chunks': self.chunk_content(plain_text)
            }
            
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return None
    
    def parse_vault(self) -> List[Dict[str, Any]]:
        """Parse entire vault and return all documents."""
        if not self.is_valid_vault():
            logger.error(f"Invalid vault path: {self.vault_path}")
            return []
        
        documents = []
        files = self.get_all_markdown_files()
        
        for file_path in files:
            parsed_doc = self.parse_file(file_path)
            if parsed_doc:
                documents.append(parsed_doc)
        
        logger.info(f"Successfully parsed {len(documents)} documents from vault")
        return documents
    
    def get_file_modification_time(self, file_path: Path) -> datetime:
        """Get file modification time."""
        try:
            return datetime.fromtimestamp(file_path.stat().st_mtime)
        except Exception as e:
            logger.error(f"Error getting modification time for {file_path}: {e}")
            return datetime.min
