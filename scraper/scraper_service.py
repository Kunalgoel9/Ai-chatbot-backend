import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
from typing import List, Dict
import logging
import time

logger = logging.getLogger(__name__)


class WebScraper:
    """
    Service to scrape websites and extract content
    """
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def is_sitemap(self, url: str) -> bool:
        """Check if URL is an XML sitemap"""
        return url.endswith('.xml') or 'sitemap' in url.lower()
    
    def get_urls_from_sitemap(self, sitemap_url: str) -> List[str]:
        """
        Extract URLs from XML sitemap
        Handles nested sitemaps (sitemap index)
        """
        urls = []
        try:
            response = self.session.get(sitemap_url, timeout=10)
            response.raise_for_status()
            
            # Parse XML properly
            root = ET.fromstring(response.content)
            
            # Get namespace from root tag
            namespace = ''
            if '}' in root.tag:
                namespace = root.tag.split('}')[0] + '}'
            
            # Try to find <loc> tags (actual page URLs)
            loc_tags = root.findall(f'.//{namespace}loc')
            
            for loc in loc_tags:
                url = loc.text.strip()
                
                # Check if this is a nested sitemap
                if self.is_sitemap(url):
                    logger.info(f"Found nested sitemap: {url}")
                    # Recursively get URLs from nested sitemap
                    nested_urls = self.get_urls_from_sitemap(url)
                    urls.extend(nested_urls)
                else:
                    # It's a regular page URL
                    urls.append(url)
            
            logger.info(f"Extracted {len(urls)} URLs from sitemap: {sitemap_url}")
            return urls
            
        except Exception as e:
            logger.error(f"Error parsing sitemap {sitemap_url}: {e}")
            return []
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
    
    def scrape_page(self, url: str) -> Dict[str, str]:
        """
        Scrape a single page and extract title and content
        Returns: dict with 'url', 'title', 'content'
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse with lxml for HTML (not XML)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title = title.get_text().strip() if title else url
            
            # Remove unwanted tags
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 
                           'iframe', 'noscript', 'form', 'button']):
                tag.decompose()
            
            # Try to find main content area
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            
            if main_content:
                # Extract text from main content
                content = main_content.get_text(separator=' ', strip=True)
            else:
                # Fallback: get all text
                content = soup.get_text(separator=' ', strip=True)
            
            # Clean the content
            content = self.clean_text(content)
            
            # Limit content length (important for embeddings and free tier)
            content = content[:10000]  # Limit to 10k characters
            
            logger.info(f"Successfully scraped: {title} ({len(content)} chars)")
            
            return {
                'url': url,
                'title': title,
                'content': content
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {
                'url': url,
                'title': '',
                'content': ''
            }
    
    def scrape_website(self, max_pages: int = 10) -> List[Dict[str, str]]:
        """
        Scrape website - either from sitemap or main page
        Returns: list of scraped pages
        
        Args:
            max_pages: Maximum number of pages to scrape (default 10 for free tier)
        """
        pages = []
        
        if self.is_sitemap(self.base_url):
            logger.info(f"Detected sitemap URL: {self.base_url}")
            
            # Get all URLs from sitemap
            urls = self.get_urls_from_sitemap(self.base_url)
            
            if not urls:
                logger.warning("No URLs found in sitemap")
                return pages
            
            # Limit number of pages for free tier
            urls = urls[:max_pages]
            logger.info(f"Will scrape {len(urls)} pages (limited to {max_pages})")
            
            # Scrape each URL
            for i, url in enumerate(urls, 1):
                logger.info(f"Scraping page {i}/{len(urls)}: {url}")
                
                page_data = self.scrape_page(url)
                
                # Only add if content exists
                if page_data['content']:
                    pages.append(page_data)
                
                # Small delay to be polite to the server
                time.sleep(0.5)
        else:
            logger.info(f"Scraping single page: {self.base_url}")
            # Just scrape the main page
            page_data = self.scrape_page(self.base_url)
            if page_data['content']:
                pages.append(page_data)
        
        logger.info(f"Total pages successfully scraped: {len(pages)}")
        return pages