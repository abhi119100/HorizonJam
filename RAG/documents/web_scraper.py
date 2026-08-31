#!/usr/bin/env python3
"""
Music RAG Data Scraper
Comprehensive web scraper for gathering guitar tabs, music theory content, 
and educational materials for RAG system integration.
"""

import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from dotenv import load_dotenv
import json
import os
import time
import logging
from urllib.parse import urljoin, urlparse
import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
import tiktoken
from pathlib import Path
import hashlib
import chromadb
from chromadb.config import Settings
import openai
from playwright.sync_api import sync_playwright
import pdfplumber
import io
import music21
import guitarpro
from pretty_midi import PrettyMIDI
import pandas as pd
import warnings

# Filter XML parsing warnings
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MusicChunk:
    """Data structure for music-related content chunks"""
    source: str
    title: str
    content: str
    metadata: Dict[str, Any]
    chunk_id: str
    token_count: int
    
    def to_dict(self):
        return asdict(self)

class MusicDataScraper:
    """Main scraper class for gathering music education data"""
    
    def __init__(self, output_dir: str = "scraped_data", chunk_size: int = 300):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.chunk_size = chunk_size
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Initialize tokenizer for chunk sizing
        self.tokenizer = tiktoken.get_encoding('cl100k_base')
        
        # Rate limiting
        self.request_delay = 1.0
        self.last_request_time = 0
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(path=str(self.output_dir / "chroma_db"))
        self.collection = self.chroma_client.get_or_create_collection("guitar_tools")
        
        # Scraped data storage
        self.scraped_chunks: List[MusicChunk] = []

    def _rate_limit(self):
        """Implement rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        self.last_request_time = time.time()

    def _make_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Make a rate-limited HTTP request"""
        self._rate_limit()
        try:
            response = self.session.get(url, timeout=10, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None

    def _chunk_text(self, text: str, metadata: Dict) -> List[Dict]:
        """Chunk text into token-sized pieces"""
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        for i in range(0, len(tokens), self.chunk_size):
            chunk_tokens = tokens[i:i + self.chunk_size]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            chunk_id = hashlib.md5(f"{metadata.get('source', '')}{chunk_text}".encode()).hexdigest()
            
            chunks.append({
                'content': chunk_text.strip(),
                'metadata': metadata.copy(),
                'chunk_id': chunk_id,
                'token_count': len(chunk_tokens)
            })
        
        return chunks

    def _sanitize_metadata_for_chromadb(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Convert metadata to ChromaDB compatible format (only str, int, float, bool, None)"""
        sanitized = {}
        for key, value in metadata.items():
            # Skip None values entirely - ChromaDB doesn't handle them well
            if value is None:
                continue
                
            if isinstance(value, (str, int, float, bool)):
                # Only add non-empty strings
                if isinstance(value, str) and value.strip():
                    sanitized[key] = value.strip()
                elif not isinstance(value, str):
                    sanitized[key] = value
            elif isinstance(value, list):
                # Convert lists to comma-separated strings
                if value and all(isinstance(item, (str, int, float)) for item in value):
                    list_str = ", ".join(str(item).strip() for item in value if str(item).strip())
                    if list_str:  # Only add if not empty
                        sanitized[key] = list_str
            elif isinstance(value, dict):
                # Convert dicts to JSON strings
                try:
                    json_str = json.dumps(value)
                    if json_str and json_str != '{}':  # Only add if not empty
                        sanitized[key] = json_str
                except (TypeError, ValueError):
                    # If can't serialize, convert to string
                    dict_str = str(value)
                    if dict_str and dict_str != '{}':
                        sanitized[key] = dict_str
            else:
                # Convert other types to strings, but skip if empty
                str_value = str(value).strip()
                if str_value and str_value.lower() not in ['none', 'null', '']:
                    sanitized[key] = str_value
        
        # Ensure we always have at least source and title
        if 'source' not in sanitized:
            sanitized['source'] = 'unknown'
        if 'title' not in sanitized:
            sanitized['title'] = 'untitled'
            
        return sanitized

    def scrape_ultimate_guitar_tabs(self, song_urls: List[str]) -> List[MusicChunk]:
        """Scrape guitar tabs from Ultimate Guitar"""
        logger.info("Scraping Ultimate Guitar tabs...")
        chunks = []
        
        for url in song_urls:
            try:
                response = self._make_request(url)
                if not response:
                    continue
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract song info
                title_elem = soup.find('h1', class_='t_title')
                artist_elem = soup.find('a', class_='t_author')
                
                title = title_elem.text.strip() if title_elem else "Unknown"
                artist = artist_elem.text.strip() if artist_elem else "Unknown"
                
                # Extract tab content
                tab_content = ""
                pre_tags = soup.find_all('pre')
                for pre in pre_tags:
                    if pre.text.strip():
                        tab_content += pre.text.strip() + "\n\n"
                
                if not tab_content:
                    # Try alternative selectors
                    content_div = soup.find('div', class_='js-tab-content')
                    if content_div:
                        tab_content = content_div.get_text(separator='\n').strip()
                
                if tab_content:
                    metadata = {
                        'source': 'UltimateGuitar',
                        'title': title,
                        'artist': artist,
                        'url': url,
                        'type': 'guitar_tab',
                        'instrument': 'guitar'
                    }
                    
                    # Chunk the content
                    text_chunks = self._chunk_text(tab_content, metadata)
                    for chunk_data in text_chunks:
                        chunk = MusicChunk(
                            source=metadata['source'],
                            title=f"{artist} - {title}",
                            content=chunk_data['content'],
                            metadata=chunk_data['metadata'],
                            chunk_id=chunk_data['chunk_id'],
                            token_count=chunk_data['token_count']
                        )
                        chunks.append(chunk)
                        
                logger.info(f"Scraped {len(text_chunks)} chunks from {title}")
                
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                continue
        
        return chunks

    def scrape_educational_websites(self) -> List[MusicChunk]:
        """Scrape content from comprehensive music education websites"""
        logger.info("Scraping educational music websites...")
        
        self.urls = [
            "https://www.guitarinstitute.com/resources/",
            "https://www.musictheory.net/lessons",
            "https://viva.pressbooks.pub/openmusictheory/",
            "https://iconcollective.edu/basic-music-theory/",
            "https://www.jazzadvice.com/",
            "https://tonesavvy.com/",
            "https://tonedear.com/",
            "https://www.earmaster.com/",
            "https://www.premierguitar.com/",
            "https://www.sweetwater.com/sweetcare/",
            "https://www.guitartricks.com/",
            "https://en.wikipedia.org/wiki/Music_theory"
        ]
        
        chunks = []
        
        for url in self.urls:
            try:
                site_chunks = self._scrape_educational_site(url)
                chunks.extend(site_chunks)
                logger.info(f"Scraped {len(site_chunks)} chunks from {url}")
                
                # Add delay between sites to be respectful
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                continue
        
        return chunks

    def _scrape_educational_site(self, base_url: str) -> List[MusicChunk]:
        """Scrape content from a specific educational site"""
        chunks = []
        site_name = urlparse(base_url).netloc.replace('www.', '')
        
        try:
            # First, get the main page
            response = self._make_request(base_url)
            if not response:
                return chunks
            
            # Check if response is XML and parse accordingly
            content_type = response.headers.get('content-type', '').lower()
            if 'xml' in content_type:
                soup = BeautifulSoup(response.text, 'xml')
            else:
                soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract main content from the landing page
            main_content = self._extract_main_content(soup, site_name)
            if main_content:
                chunks.extend(self._create_chunks_from_content(
                    main_content, base_url, site_name, 'main_page'
                ))
            
            # Find and scrape lesson/article links
            lesson_links = self._find_lesson_links(soup, base_url, site_name)
            
            # Limit to avoid overwhelming the server
            max_links = 20
            for i, (link_url, link_title) in enumerate(lesson_links[:max_links]):
                try:
                    link_chunks = self._scrape_lesson_page(link_url, link_title, site_name)
                    chunks.extend(link_chunks)
                    
                    # Rate limiting between pages
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error scraping lesson {link_url}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error scraping site {base_url}: {e}")
        
        return chunks

    def _extract_main_content(self, soup: BeautifulSoup, site_name: str) -> str:
        """Extract main content from a webpage based on common patterns"""
        content = ""
        
        # Remove unwanted elements
        for elem in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
            elem.decompose()
        
        # Site-specific content extraction
        if 'musictheory.net' in site_name:
            # Music theory net has lessons in specific divs
            lesson_content = soup.find('div', id='content')
            if lesson_content:
                content = lesson_content.get_text(separator='\n').strip()
                
        elif 'guitarinstitute.com' in site_name:
            # Guitar institute resources
            main_content = soup.find('main') or soup.find('div', class_='content')
            if main_content:
                content = main_content.get_text(separator='\n').strip()
                
        elif 'openmusictheory' in site_name:
            # Open music theory book
            content_div = soup.find('div', class_='page-content') or soup.find('main')
            if content_div:
                content = content_div.get_text(separator='\n').strip()
                
        elif 'iconcollective.edu' in site_name:
            # Icon collective
            article = soup.find('article') or soup.find('div', class_='content')
            if article:
                content = article.get_text(separator='\n').strip()
                
        elif 'jazzadvice.com' in site_name:
            # Jazz advice
            post_content = soup.find('div', class_='post-content') or soup.find('article')
            if post_content:
                content = post_content.get_text(separator='\n').strip()
                
        elif 'premierguitar.com' in site_name:
            # Premier guitar
            article = soup.find('article') or soup.find('div', class_='article-body')
            if article:
                content = article.get_text(separator='\n').strip()
                
        elif 'wikipedia.org' in site_name:
            content_div = soup.find('div', id='mw-content-text')
            if content_div:
                # Remove tables, infoboxes, and other non-prose elements
                for table in content_div.find_all(['table', 'div'], class_=['infobox', 'navbox', 'vertical-navbox', 'box-B', 'metadata', 'thumb', 'reference']):
                    table.decompose()
                content = content_div.get_text(separator='\n').strip()
                
        else:
            # Generic content extraction
            main_content = (soup.find('main') or 
                          soup.find('article') or 
                          soup.find('div', class_='content') or
                          soup.find('div', id='content') or
                          soup.find('div', class_='post-content'))
            
            if main_content:
                content = main_content.get_text(separator='\n').strip()
            else:
                # Fallback to body content, excluding headers/footers
                body = soup.find('body')
                if body:
                    # Remove navigation, headers, footers
                    for elem in body.find_all(['nav', 'header', 'footer']):
                        elem.decompose()
                    content = body.get_text(separator='\n').strip()
        
        # Clean up the content
        if content:
            # Remove excessive whitespace
            content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
            content = re.sub(r'[ \t]+', ' ', content)
            content = content.strip()
        
        return content

    def _find_lesson_links(self, soup: BeautifulSoup, base_url: str, site_name: str) -> List[tuple]:
        """Find lesson/article links on the page"""
        links = []
        
        # Look for links that might be lessons or articles
        lesson_keywords = ['lesson', 'tutorial', 'guide', 'chord', 'scale', 'theory', 'exercise', 'technique']
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text().strip()
            
            if not href or not text:
                continue
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                full_url = urljoin(base_url, href)
            elif href.startswith('http'):
                full_url = href
            else:
                continue
            
            # Only include links from the same domain
            if urlparse(full_url).netloc != urlparse(base_url).netloc:
                continue
            
            # Check if the link text suggests it's educational content
            text_lower = text.lower()
            if (any(keyword in text_lower for keyword in lesson_keywords) or
                any(keyword in href.lower() for keyword in lesson_keywords)):
                links.append((full_url, text))
        
        # Remove duplicates
        seen_urls = set()
        unique_links = []
        for url, title in links:
            if url not in seen_urls:
                seen_urls.add(url)
                unique_links.append((url, title))
        
        return unique_links[:50]  # Limit to prevent overwhelming

    def _scrape_lesson_page(self, url: str, title: str, site_name: str) -> List[MusicChunk]:
        """Scrape content from an individual lesson page"""
        chunks = []
        
        try:
            response = self._make_request(url)
            if not response:
                return chunks
            
            # Check if response is XML and parse accordingly
            content_type = response.headers.get('content-type', '').lower()
            if 'xml' in content_type:
                soup = BeautifulSoup(response.text, 'xml')
            else:
                soup = BeautifulSoup(response.text, 'html.parser')
            
            content = self._extract_main_content(soup, site_name)
            
            if content and len(content) > 100:  # Only process substantial content
                chunks.extend(self._create_chunks_from_content(
                    content, url, site_name, 'lesson', title
                ))
                
        except Exception as e:
            logger.error(f"Error scraping lesson page {url}: {e}")
        
        return chunks

    def _create_chunks_from_content(self, content: str, url: str, site_name: str, 
                                  content_type: str, title: str = None) -> List[MusicChunk]:
        """Create MusicChunk objects from content"""
        chunks = []
        
        if not content or len(content) < 50:
            return chunks
        
        # Determine content category based on keywords
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['chord', 'progression', 'harmony']):
            topic = 'chords'
        elif any(word in content_lower for word in ['scale', 'mode', 'key']):
            topic = 'scales'
        elif any(word in content_lower for word in ['rhythm', 'tempo', 'beat']):
            topic = 'rhythm'
        elif any(word in content_lower for word in ['technique', 'fingering', 'exercise']):
            topic = 'technique'
        elif any(word in content_lower for word in ['theory', 'interval', 'note']):
            topic = 'theory'
        else:
            topic = 'general'
        
        # Determine difficulty level
        if any(word in content_lower for word in ['beginner', 'basic', 'introduction', 'start']):
            difficulty = 'beginner'
        elif any(word in content_lower for word in ['advanced', 'expert', 'complex']):
            difficulty = 'advanced' 
        else:
            difficulty = 'intermediate'
        
        metadata = {
            'source': site_name,
            'title': title or f"Content from {site_name}",
            'url': url,
            'type': content_type,
            'topic': topic,
            'difficulty': difficulty,
            'instrument': 'guitar' if 'guitar' in content_lower else 'general'
        }
        
        text_chunks = self._chunk_text(content, metadata)
        for chunk_data in text_chunks:
            chunk = MusicChunk(
                source=site_name,
                title=metadata['title'],
                content=chunk_data['content'],
                metadata=chunk_data['metadata'],
                chunk_id=chunk_data['chunk_id'],
                token_count=chunk_data['token_count']
            )
            chunks.append(chunk)
        
        return chunks

    def scrape_awesome_guitar_resources(self) -> List[MusicChunk]:
        """Scrape resources from awesome-guitar GitHub repository"""
        logger.info("Scraping awesome-guitar resources...")
        
        awesome_guitar_url = "https://raw.githubusercontent.com/sfischer13/awesome-guitar/master/README.md"
        chunks = []
        
        try:
            response = self._make_request(awesome_guitar_url)
            if not response:
                return chunks
            
            # Parse markdown content
            content = response.text
            
            # Extract URLs from the markdown
            url_pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
            matches = re.findall(url_pattern, content)
            
            # Filter for educational resources
            educational_keywords = ['theory', 'lesson', 'tutorial', 'chord', 'scale', 'exercise']
            educational_urls = []
            
            for title, url in matches:
                if any(keyword in title.lower() for keyword in educational_keywords):
                    educational_urls.append((title, url))
            
            # Scrape a subset of these URLs
            for title, url in educational_urls[:10]:  # Limit to 10 to avoid overwhelming
                try:
                    if url.endswith('.pdf'):
                        # Handle PDF files
                        pdf_chunks = self._scrape_pdf(url, title)
                        chunks.extend(pdf_chunks)
                    else:
                        # Handle web pages
                        web_chunks = self._scrape_webpage(url, title, 'awesome-guitar')
                        chunks.extend(web_chunks)
                        
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping awesome-guitar: {e}")
        
        return chunks

    def _scrape_pdf(self, url: str, title: str) -> List[MusicChunk]:
        """Scrape content from PDF files"""
        chunks = []
        try:
            response = self._make_request(url)
            if not response:
                return chunks
            
            pdf_content = io.BytesIO(response.content)
            
            with pdfplumber.open(pdf_content) as pdf:
                text = ''
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n\n'
            
            if text.strip():
                metadata = {
                    'source': 'PDF',
                    'title': title,
                    'url': url,
                    'type': 'educational_material',
                    'format': 'pdf'
                }
                
                text_chunks = self._chunk_text(text, metadata)
                for chunk_data in text_chunks:
                    chunk = MusicChunk(
                        source=metadata['source'],
                        title=title,
                        content=chunk_data['content'],
                        metadata=chunk_data['metadata'],
                        chunk_id=chunk_data['chunk_id'],
                        token_count=chunk_data['token_count']
                    )
                    chunks.append(chunk)
                    
        except Exception as e:
            logger.error(f"Error scraping PDF {url}: {e}")
        
        return chunks

    def _scrape_webpage(self, url: str, title: str, source: str) -> List[MusicChunk]:
        """Scrape content from regular web pages"""
        chunks = []
        try:
            response = self._make_request(url)
            if not response:
                return chunks
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for elem in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                elem.decompose()
            
            # Extract main content
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup.body
            
            if main_content:
                text = main_content.get_text(separator='\n').strip()
                
                # Clean up text
                text = re.sub(r'\n\s*\n', '\n\n', text)  # Remove excessive newlines
                text = re.sub(r'[ \t]+', ' ', text)  # Normalize whitespace
                
                if len(text) > 100:  # Only process if there's substantial content
                    metadata = {
                        'source': source,
                        'title': title,
                        'url': url,
                        'type': 'educational_material',
                        'format': 'webpage'
                    }
                    
                    text_chunks = self._chunk_text(text, metadata)
                    for chunk_data in text_chunks:
                        chunk = MusicChunk(
                            source=metadata['source'],
                            title=title,
                            content=chunk_data['content'],
                            metadata=chunk_data['metadata'],
                            chunk_id=chunk_data['chunk_id'],
                            token_count=chunk_data['token_count']
                        )
                        chunks.append(chunk)
                        
        except Exception as e:
            logger.error(f"Error scraping webpage {url}: {e}")
        
        return chunks

    def scrape_hooktheory_data(self, username: Optional[str] = None, password: Optional[str] = None) -> List[MusicChunk]:
        """Scrape chord progression data from HookTheory API"""
        logger.info("Scraping HookTheory data...")
        
        if not username or not password:
            logger.warning("No HookTheory username/password provided, skipping...")
            return []
        
        chunks = []
        
        # First, authenticate to get the session
        auth_url = "https://api.hooktheory.com/v1/users/auth"
        auth_data = {
            "username": username,
            "password": password
        }
        
        try:
            # Authenticate
            auth_response = self.session.post(auth_url, json=auth_data, timeout=10)
            auth_response.raise_for_status()
            
            # The session should now be authenticated via cookies
            logger.info("Successfully authenticated with HookTheory API")
            
        except requests.RequestException as e:
            logger.error(f"HookTheory authentication failed: {e}")
            return []
        
        # Common chord progressions to fetch
        progressions = [
            "1,5,6,4",  # I-V-vi-IV
            "1,6,4,5",  # I-vi-IV-V
            "6,4,1,5",  # vi-IV-I-V
            "2,5,1",    # ii-V-I
            "1,4,5,1"   # I-IV-V-I
        ]
        
        for progression in progressions:
            try:
                # Use the authenticated session (no Bearer token needed)
                url = f"https://api.hooktheory.com/v1/trends/nodes?cp={progression}"
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                # Process the response data
                for item in data:
                    if 'songs' in item:
                        for song in item['songs']:
                            content = f"Chord progression: {progression}\n"
                            content += f"Song: {song.get('song', 'Unknown')}\n"
                            content += f"Artist: {song.get('artist', 'Unknown')}\n"
                            content += f"Probability: {song.get('probability', 0)}\n"
                            
                            metadata = {
                                'source': 'HookTheory',
                                'title': f"{song.get('artist', 'Unknown')} - {song.get('song', 'Unknown')}",
                                'type': 'chord_progression',
                                'progression': progression,
                                'instrument': 'general'
                            }
                            
                            chunk_id = hashlib.md5(content.encode()).hexdigest()
                            
                            chunk = MusicChunk(
                                source='HookTheory',
                                title=metadata['title'],
                                content=content,
                                metadata=metadata,
                                chunk_id=chunk_id,
                                token_count=len(self.tokenizer.encode(content))
                            )
                            chunks.append(chunk)
                            
            except Exception as e:
                logger.error(f"Error scraping HookTheory progression {progression}: {e}")
                continue
                
            # Rate limiting
            time.sleep(0.5)
        
        return chunks

    def save_chunks_to_json(self, chunks: List[MusicChunk], filename: str):
        """Save chunks to JSON file"""
        output_file = self.output_dir / f"{filename}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump([chunk.to_dict() for chunk in chunks], f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(chunks)} chunks to {output_file}")

    def save_to_chromadb(self, chunks: List[MusicChunk]):
        """Save chunks to ChromaDB with duplicate handling"""
        if not chunks:
            return
        
        documents = [chunk.content for chunk in chunks]
        # Sanitize metadata for ChromaDB compatibility
        metadatas = [self._sanitize_metadata_for_chromadb(chunk.metadata) for chunk in chunks]
        
        # Ensure unique IDs by adding a counter to duplicates
        ids = []
        seen_ids = set()
        
        for chunk in chunks:
            base_id = chunk.chunk_id
            unique_id = base_id
            counter = 1
            
            # If we've seen this ID before, add a counter
            while unique_id in seen_ids:
                unique_id = f"{base_id}_{counter}"
                counter += 1
                
            seen_ids.add(unique_id)
            ids.append(unique_id)
        
        # Add chunks in batches to avoid memory issues
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch_docs = documents[i:i + batch_size]
            batch_metas = metadatas[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            
            try:
                self.collection.add(
                    documents=batch_docs,
                    metadatas=batch_metas,
                    ids=batch_ids
                )
                logger.info(f"Successfully added batch {i//batch_size + 1} to ChromaDB")
            except Exception as e:
                logger.error(f"Error adding batch to ChromaDB: {e}")
                # Try adding items one by one to identify problematic entries
                for j, (doc, meta, id_) in enumerate(zip(batch_docs, batch_metas, batch_ids)):
                    try:
                        self.collection.add(
                            documents=[doc],
                            metadatas=[meta],
                            ids=[id_]
                        )
                    except Exception as item_error:
                        logger.error(f"Error adding individual item {id_}: {item_error}")
                        logger.error(f"Problematic metadata: {meta}")
        
        logger.info(f"Added {len(chunks)} chunks to ChromaDB")

    def run_full_scrape(self, hooktheory_username: Optional[str] = None, hooktheory_password: Optional[str] = None):
    
        logger.info("Starting full scraping pipeline...")
        
        all_chunks = []
        
        # 1. Scrape comprehensive educational websites
        educational_chunks = self.scrape_educational_websites()
        all_chunks.extend(educational_chunks)
        self.save_chunks_to_json(educational_chunks, "educational_websites")
        
        # 2. Scrape Ultimate Guitar tabs (sample URLs for demonstration)
        sample_ug_urls = [
            "https://tabs.ultimate-guitar.com/tab/coldplay/yellow-chords-90007",
            "https://tabs.ultimate-guitar.com/tab/oasis/wonderwall-chords-16956",
            "http://gprotab.net/en/tabs/the-beatles/let-it-be"
        ]
        
        ug_chunks = self.scrape_ultimate_guitar_tabs(sample_ug_urls)
        all_chunks.extend(ug_chunks)
        self.save_chunks_to_json(ug_chunks, "ultimate_guitar_tabs")
        
        # 3. Scrape awesome-guitar resources
        awesome_chunks = self.scrape_awesome_guitar_resources()
        all_chunks.extend(awesome_chunks)
        self.save_chunks_to_json(awesome_chunks, "awesome_guitar_resources")
        
        # 4. Scrape HookTheory (if credentials provided)
        if hooktheory_username and hooktheory_password:
            hook_chunks = self.scrape_hooktheory_data(hooktheory_username, hooktheory_password)
            all_chunks.extend(hook_chunks)
            self.save_chunks_to_json(hook_chunks, "hooktheory_progressions")
        
        # 5. Save all chunks to ChromaDB
        self.save_to_chromadb(all_chunks)
        
        # 6. Save combined dataset
        self.save_chunks_to_json(all_chunks, "complete_music_dataset")
        
        logger.info(f"Scraping complete! Total chunks: {len(all_chunks)}")
        
        # Print summary statistics
        self._print_summary(all_chunks)
        
        return all_chunks

    def _print_summary(self, chunks: List[MusicChunk]):
        """Print summary statistics of scraped data"""
        if not chunks:
            return
        
        df = pd.DataFrame([chunk.to_dict() for chunk in chunks])
        
        print("\n" + "="*50)
        print("SCRAPING SUMMARY")
        print("="*50)
        print(f"Total chunks: {len(chunks)}")
        print(f"Average token count: {df['token_count'].mean():.1f}")
        print(f"Total tokens: {df['token_count'].sum():,}")
        
        print("\nChunks by source:")
        print(df['source'].value_counts())
        
        print("\nChunks by type:")
        if 'type' in df.columns:
            print(df['metadata'].apply(lambda x: x.get('type', 'unknown')).value_counts())
        
        print("="*50)

    def parse_tuxguitar_files(self, gp_filepaths: List[str]) -> List[MusicChunk]:
        """Parse TuxGuitar .gp3/.gp4/.gp5 files using PyGuitarPro and extract tab chunks including string/fret positions."""
        chunks = []
        for filepath in gp_filepaths:
            try:
                if not os.path.exists(filepath):
                    logger.warning(f"TuxGuitar file not found: {filepath}")
                    continue
                    
                # Fix: Use correct guitarpro method
                song = guitarpro.parse(filepath)
                title = song.title or os.path.basename(filepath)
                tempo = song.tempo
                
                for track_idx, track in enumerate(song.tracks):
                    if not track.isPercussionTrack:
                        for measure_num, measure in enumerate(track.measures, 1):
                            for voice_idx, voice in enumerate(measure.voices):
                                for beat_idx, beat in enumerate(voice.beats):
                                    notes = []
                                    string_fret = []
                                    
                                    for note in beat.notes:
                                        if hasattr(note, 'string') and hasattr(note, 'value'):
                                            notes.append(str(note.value))
                                            string_fret.append({
                                                "string": note.string, 
                                                "fret": note.value
                                            })
                                    
                                    chord_name = None
                                    if hasattr(beat, 'effect') and hasattr(beat.effect, 'chord'):
                                        chord_name = beat.effect.chord.name if beat.effect.chord else None
                                    
                                    # Create chunk data - convert lists to strings for ChromaDB compatibility
                                    chunk_dict = {
                                        "source": "TuxGuitar",
                                        "title": title,
                                        "track": track_idx,
                                        "measure": measure_num,
                                        "beat": beat_idx,
                                        "chord": chord_name,
                                        "tempo": tempo,
                                        "notes": ", ".join(notes) if notes else "",  # Convert to string
                                        "string_fret": json.dumps(string_fret),  # Convert to JSON string
                                        "duration": beat.duration.value if hasattr(beat.duration, 'value') else None
                                    }
                                    
                                    chunk_text = json.dumps(chunk_dict)
                                    token_count = len(self.tokenizer.encode(chunk_text))
                                    chunk_id = hashlib.md5(f"{title}{track_idx}{measure_num}{beat_idx}{chunk_text}".encode()).hexdigest()
                                    
                                    chunk = MusicChunk(
                                        source="TuxGuitar",
                                        title=title,
                                        content=chunk_text,
                                        metadata=chunk_dict,
                                        chunk_id=chunk_id,
                                        token_count=token_count
                                    )
                                    chunks.append(chunk)
                                    
            except Exception as e:
                logger.error(f"Error parsing TuxGuitar file {filepath}: {e}")
                continue
                
        return chunks

    def parse_alphatex_files(self, alphatex_filepaths: List[str]) -> List[MusicChunk]:
        """Parse AlphaTab alphaTex files using Node.js script."""
        import subprocess
        chunks = []
        
        for filepath in alphatex_filepaths:
            try:
                if not os.path.exists(filepath):
                    logger.warning(f"AlphaTex file not found: {filepath}")
                    continue
                
                # Check if Node.js script exists
                script_path = "parse_alphatex.js"
                if not os.path.exists(script_path):
                    logger.error(f"Node.js parser script not found: {script_path}")
                    logger.error("Please create the parse_alphatex.js script in your project directory")
                    continue
                
                # Call Node.js script to parse alphaTex and return JSON
                result = subprocess.run(
                    ["node", script_path, filepath],
                    capture_output=True, text=True, timeout=30
                )
                
                if result.returncode == 0:
                    try:
                        data = json.loads(result.stdout)
                        # Expect data to be a list of sections/chunks
                        for chunk_dict in data:
                            chunk_text = json.dumps(chunk_dict)
                            token_count = len(self.tokenizer.encode(chunk_text))
                            chunk_id = hashlib.md5(f"{chunk_dict.get('title','')}{chunk_text}".encode()).hexdigest()
                            
                            chunk = MusicChunk(
                                source="AlphaTab",
                                title=chunk_dict.get("title", os.path.basename(filepath)),
                                content=chunk_text,
                                metadata=chunk_dict,
                                chunk_id=chunk_id,
                                token_count=token_count
                            )
                            chunks.append(chunk)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON output from AlphaTex parser: {e}")
                        logger.error(f"Output was: {result.stdout}")
                else:
                    logger.error(f"AlphaTab parse failed for {filepath}: {result.stderr}")
                    
            except FileNotFoundError:
                logger.error("Node.js not found. Please ensure Node.js is installed and accessible from PATH.")
            except subprocess.TimeoutExpired:
                logger.error(f"AlphaTab parsing timed out for {filepath}")
            except Exception as e:
                logger.error(f"Error parsing AlphaTab file {filepath}: {e}")
                
        return chunks

    def parse_midi_files(self, midi_filepaths: List[str]) -> List[MusicChunk]:
        """Parse MIDI files using music21 for notes and timing."""
        chunks = []
        
        for filepath in midi_filepaths:
            try:
                if not os.path.exists(filepath):
                    logger.warning(f"MIDI file not found: {filepath}")
                    continue
                    
                midi_score = music21.converter.parse(filepath)
                title = os.path.basename(filepath)
                
                # Extract tempo if available
                tempo = None
                # Fix: Use flatten() instead of .flat
                for element in midi_score.flatten():
                    if isinstance(element, music21.tempo.TempoIndication):
                        tempo = element.number
                        break
                
                # Process each part
                for part_idx, part in enumerate(midi_score.parts):
                    measures = part.getElementsByClass('Measure')
                    
                    if not measures:
                        # If no measures, treat the whole part as one section
                        notes = []
                        # Fix: Use flatten() instead of .flat
                        for element in part.flatten().notes:
                            if hasattr(element, 'nameWithOctave'):
                                notes.append(str(element.nameWithOctave))
                            elif hasattr(element, 'pitches'):  # Chord
                                chord_notes = [str(p.nameWithOctave) for p in element.pitches]
                                notes.extend(chord_notes)
                        
                        chunk_dict = {
                            "source": "GuitarTrainer",
                            "title": title,
                            "part": part_idx,
                            "measure": 1,
                            "notes": ", ".join(notes),  # Convert to string for ChromaDB
                            "tempo": tempo
                        }
                        
                        chunk_text = json.dumps(chunk_dict)
                        token_count = len(self.tokenizer.encode(chunk_text))
                        chunk_id = hashlib.md5(f"{title}{part_idx}1{chunk_text}".encode()).hexdigest()
                        
                        chunk = MusicChunk(
                            source="GuitarTrainer",
                            title=title,
                            content=chunk_text,
                            metadata=chunk_dict,
                            chunk_id=chunk_id,
                            token_count=token_count
                        )
                        chunks.append(chunk)
                    else:
                        # Process each measure
                        for measure in measures:
                            measure_number = measure.number if hasattr(measure, 'number') else 1
                            notes = []
                            
                            for element in measure.notes:
                                if hasattr(element, 'nameWithOctave'):
                                    notes.append(str(element.nameWithOctave))
                                elif hasattr(element, 'pitches'):  # Chord
                                    chord_notes = [str(p.nameWithOctave) for p in element.pitches]
                                    notes.extend(chord_notes)
                            
                            if notes:  # Only create chunk if there are notes
                                chunk_dict = {
                                    "source": "GuitarTrainer",
                                    "title": title,
                                    "part": part_idx,
                                    "measure": measure_number,
                                    "notes": ", ".join(notes),  # Convert to string for ChromaDB
                                    "tempo": tempo
                                }
                                
                                chunk_text = json.dumps(chunk_dict)
                                token_count = len(self.tokenizer.encode(chunk_text))
                                chunk_id = hashlib.md5(f"{title}{part_idx}{measure_number}{chunk_text}".encode()).hexdigest()
                                
                                chunk = MusicChunk(
                                    source="GuitarTrainer",
                                    title=title,
                                    content=chunk_text,
                                    metadata=chunk_dict,
                                    chunk_id=chunk_id,
                                    token_count=token_count
                                )
                                chunks.append(chunk)
                                
            except Exception as e:
                logger.error(f"Error parsing MIDI file {filepath}: {e}")
                continue
                
        return chunks

    def parse_freetar_ascii_tabs(self, tab_filepaths: List[str]) -> List[MusicChunk]:
        """Parse freetar ASCII tab files, segment by verse/chorus."""
        chunks = []
        
        for filepath in tab_filepaths:
            try:
                if not os.path.exists(filepath):
                    logger.warning(f"Freetar tab file not found: {filepath}")
                    continue
                    
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Segment by verse/chorus using simple regex
                segments = re.split(r'(Verse|Chorus|Bridge|Solo|Intro|Outro)', content, flags=re.IGNORECASE)
                title = os.path.basename(filepath)
                
                # If content starts with a section, segments[0] will be empty or intro content
                if segments and segments[0].strip():
                    chunk_dict_intro = {
                        "source": "freetar",
                        "title": title,
                        "section": "Intro",
                        "tab": segments[0].strip()
                    }
                    chunk_text_intro = json.dumps(chunk_dict_intro)
                    token_count_intro = len(self.tokenizer.encode(chunk_text_intro))
                    chunk_id_intro = hashlib.md5(f"{title}Intro{chunk_text_intro}".encode()).hexdigest()
                    
                    chunks.append(MusicChunk(
                        source="freetar",
                        title=title,
                        content=chunk_text_intro,
                        metadata=chunk_dict_intro,
                        chunk_id=chunk_id_intro,
                        token_count=token_count_intro
                    ))

                # Process section pairs (section_name, section_content)
                for i in range(1, len(segments), 2):
                    if i < len(segments):
                        section = segments[i].strip()
                        tab_text = segments[i+1].strip() if (i+1) < len(segments) else ""
                        
                        if tab_text:
                            chunk_dict = {
                                "source": "freetar",
                                "title": title,
                                "section": section,
                                "tab": tab_text
                            }
                            chunk_text = json.dumps(chunk_dict)
                            token_count = len(self.tokenizer.encode(chunk_text))
                            chunk_id = hashlib.md5(f"{title}{section}{chunk_text}".encode()).hexdigest()
                            
                            chunk = MusicChunk(
                                source="freetar",
                                title=title,
                                content=chunk_text,
                                metadata=chunk_dict,
                                chunk_id=chunk_id,
                                token_count=token_count
                            )
                            chunks.append(chunk)
                            
            except Exception as e:
                logger.error(f"Error parsing freetar tab {filepath}: {e}")
                continue
                
        return chunks

    def parse_tabs_lite_files(self, filepaths: List[str]) -> List[MusicChunk]:
        """Parse Tabs-Lite offline tab files or custom tab text files."""
        chunks = []
        
        for filepath in filepaths:
            try:
                if not os.path.exists(filepath):
                    logger.warning(f"Tabs-Lite file not found: {filepath}")
                    continue
                    
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Parse basic metadata
                title_match = re.search(r'(?:TITLE|Title):\s*(.*)', content, re.IGNORECASE)
                key_match = re.search(r'(?:KEY|Key):\s*(.*)', content, re.IGNORECASE)
                artist_match = re.search(r'(?:ARTIST|Artist):\s*(.*)', content, re.IGNORECASE)
                
                # Extract chord patterns
                chords_raw = re.findall(r'\|([A-G][b#]?(?:maj|min|dim|aug|sus|add)?\d*)\s*\|', content)
                chords_raw.extend(re.findall(r'\b([A-G][b#]?(?:maj|min|dim|aug|sus|add)?\d*)\b', content))
                
                title = title_match.group(1).strip() if title_match else os.path.basename(filepath)
                key = key_match.group(1).strip() if key_match else "Unknown"
                artist = artist_match.group(1).strip() if artist_match else "Unknown"
                
                # Remove duplicates from chords and convert to string for ChromaDB
                unique_chords = list(set(chords_raw))
                
                chunk_dict = {
                    "source": "Tabs-Lite",
                    "title": title,
                    "artist": artist,
                    "key": key,
                    "chords": ", ".join(unique_chords),  # Convert to string for ChromaDB
                    "content_preview": content[:500] + "..." if len(content) > 500 else content
                }
                
                chunk_text = json.dumps(chunk_dict)
                token_count = len(self.tokenizer.encode(chunk_text))
                chunk_id = hashlib.md5(f"{title}{filepath}{chunk_text}".encode()).hexdigest()
                
                chunk = MusicChunk(
                    source="Tabs-Lite",
                    title=title,
                    content=chunk_text,
                    metadata=chunk_dict,
                    chunk_id=chunk_id,
                    token_count=token_count
                )
                chunks.append(chunk)
                
            except Exception as e:
                logger.error(f"Error parsing Tabs-Lite file {filepath}: {e}")
                continue
                
        return chunks

    def test_ingest_and_query_chromadb(self, chunks: List[MusicChunk], query_text: str):
        """Test ingestion of chunks to ChromaDB and perform a sample query."""
        logger.info(f"Testing ChromaDB ingestion and query with {len(chunks)} chunks...")
        
        # Clear existing collection for a clean test
        try:
            self.chroma_client.delete_collection("guitar_tools")
            self.collection = self.chroma_client.get_or_create_collection("guitar_tools")
            logger.info("ChromaDB collection cleared for test.")
        except Exception as e:
            logger.warning(f"Could not clear ChromaDB collection (might not exist): {e}")

        # Save chunks to ChromaDB
        self.save_to_chromadb(chunks)
        
        # Perform a simple query without embeddings (using built-in similarity)
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=min(3, len(chunks)),
                include=['documents', 'metadatas']
            )
            
            print(f"\n--- ChromaDB Query Results for '{query_text}' ---")
            if results and results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {}
                    print(f"Result {i+1}:")
                    print(f"  Source: {metadata.get('source', 'N/A')}")
                    print(f"  Title: {metadata.get('title', 'N/A')}")
                    print(f"  Content (excerpt): {doc[:200]}...")
                    print("-" * 20)
            else:
                print("No relevant results found.")
                
        except Exception as e:
            logger.error(f"Error during ChromaDB query test: {e}")




def main():
    load_dotenv() 
    
    """Main execution function"""
    # Initialize scraper
    scraper = MusicDataScraper(output_dir="music_rag_data", chunk_size=300)
    
    # Get HookTheory credentials from environment variables
    hooktheory_username = os.getenv('HOOKTHEORY_USERNAME')
    hooktheory_password = os.getenv('HOOKTHEORY_PASSWORD')
    
    # Create a 'samples' directory if it doesn't exist
    Path("samples").mkdir(exist_ok=True)

    # --- Phase 1: TuxGuitar, freetar, and Tabs-Lite ---
    logger.info("--- Phase 1: Processing local tab files ---")
    
    # File paths - UPDATE THESE WITH YOUR ACTUAL FILES
    tuxguitar_files = [
        "samples/sample.gp3",  # Download from TuxGuitar examples or Songsterr
        # Add more .gp3, .gp4, .gp5 files as needed
    ]
    
    freetar_tabs = [
        "samples/tab1.txt",  # Create or download ASCII tabs
        # Add more tab files as needed
    ]
    
    tabs_lite_files = [
        "samples/sample_chords.txt",  # Create simple chord/tab files
        # Add more tab files as needed
    ]
    
    guitar_trainer_midi_files = [
        "samples/sample.mid",  # Download MIDI files from sources mentioned above
        # Add more MIDI files as needed
    ]
    
    alphatex_files = [
        "samples/alphatab_sample.atx",  # Create AlphaTex files using the format shown above
        # Add more AlphaTex files as needed
    ]

    all_files = tuxguitar_files + freetar_tabs + tabs_lite_files + guitar_trainer_midi_files + alphatex_files
    for filepath in all_files:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            logger.info(f"File exists: {filepath} ({size} bytes)")
        else:
            logger.warning(f"File missing: {filepath}")

    # Parse all file types with individual reporting
    logger.info("Parsing TuxGuitar files...")
    tux_chunks = scraper.parse_tuxguitar_files(tuxguitar_files)
    logger.info(f"TuxGuitar chunks: {len(tux_chunks)}")
    
    logger.info("Parsing freetar tabs...")
    freetar_chunks = scraper.parse_freetar_ascii_tabs(freetar_tabs)
    logger.info(f"Freetar chunks: {len(freetar_chunks)}")
    
    logger.info("Parsing tabs-lite files...")
    tabs_lite_chunks = scraper.parse_tabs_lite_files(tabs_lite_files)
    logger.info(f"Tabs-lite chunks: {len(tabs_lite_chunks)}")
    
    logger.info("Parsing MIDI files...")
    midi_chunks = scraper.parse_midi_files(guitar_trainer_midi_files)
    logger.info(f"MIDI chunks: {len(midi_chunks)}")
    
    logger.info("Parsing AlphaTex files...")
    alphatex_chunks = scraper.parse_alphatex_files(alphatex_files)
    logger.info(f"AlphaTex chunks: {len(alphatex_chunks)}")

    all_phase1_chunks = tux_chunks + freetar_chunks + tabs_lite_chunks + midi_chunks + alphatex_chunks
    
    logger.info(f"Phase 1 total chunks: {len(all_phase1_chunks)}")
    logger.info(f"Breakdown: TuxGuitar={len(tux_chunks)}, Freetar={len(freetar_chunks)}, TabsLite={len(tabs_lite_chunks)}, MIDI={len(midi_chunks)}, AlphaTex={len(alphatex_chunks)}")

    all_phase1_chunks = tux_chunks + freetar_chunks + tabs_lite_chunks + midi_chunks + alphatex_chunks
    
    if all_phase1_chunks:
        scraper.save_chunks_to_json(all_phase1_chunks, "phase1_local_file_chunks")
        # Test ingest and query with Phase 1 chunks
        scraper.test_ingest_and_query_chromadb(all_phase1_chunks, query_text="guitar chords and progressions")
    else:
        logger.warning("No chunks generated in Phase 1 (local files). Check if sample files exist and are valid.")

    # --- Phase 2: Web Scraping and API Data ---
    logger.info("--- Phase 2: Web Scraping and API Data ---")


    web_chunks = scraper.run_full_scrape(
        hooktheory_username=hooktheory_username,
        hooktheory_password=hooktheory_password
    )
    
    # Combine all chunks
    all_chunks = all_phase1_chunks + web_chunks
    
    print(f"\nScraping completed successfully!")
    print(f"Data saved to: {scraper.output_dir}")
    print(f"Phase 1 (local files): {len(all_phase1_chunks)} chunks")
    print(f"Phase 2 (web scraping): {len(web_chunks)} chunks") 
    print(f"Total chunks collected: {len(all_chunks)}")



if __name__ == "__main__":
    main()