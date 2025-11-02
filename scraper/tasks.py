from celery import shared_task
from api.models import Website, ScrapedPage
from .scraper_service import WebScraper
from rag.qdrant_service import QdrantService
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def scrape_website_task(self, website_id: int):
    """
    Celery task to scrape a website and store in Qdrant
    """
    try:
        # Get the website object
        website = Website.objects.get(id=website_id)
        logger.info(f"Starting scrape for website: {website.url}")
        
        # Update status to scraping
        website.status = 's'  # STATUS_SCRAPING
        website.save()
        
        # Initialize scraper and Qdrant
        scraper = WebScraper(website.url)
        qdrant = QdrantService()
        
        # Scrape the website (limit to 10 pages for free tier)
        pages = scraper.scrape_website(max_pages=10)
        
        if not pages:
            logger.warning(f"No pages scraped for {website.url}")
            website.status = 'f'
            website.save()
            return {
                'status': 'error',
                'message': 'No pages were scraped',
                'website_id': website_id
            }
        
        # Save scraped pages to database AND Qdrant
        for page_data in pages:
            # Create database entry
            scraped_page = ScrapedPage.objects.create(
                website=website,
                url=page_data['url'],
                title=page_data['title'],
                content=page_data['content']
            )
            
            # Store in Qdrant vector DB
            try:
                vector_id = qdrant.add_document(
                    page_id=scraped_page.id,
                    url=page_data['url'],
                    title=page_data['title'],
                    content=page_data['content']
                )
                
                # Update scraped_page with vector_id
                scraped_page.vector_id = vector_id
                scraped_page.save()
                
                logger.info(f"Stored in Qdrant: {page_data['title']}")
            except Exception as e:
                logger.error(f"Failed to store in Qdrant: {e}")
        
        # Update website status
        website.status = 'c'  # STATUS_COMPLETE
        website.total_pages = len(pages)
        website.updated_at = timezone.now()
        website.save()
        
        logger.info(f"Successfully scraped {len(pages)} pages for {website.url}")
        
        return {
            'status': 'success',
            'pages_scraped': len(pages),
            'website_id': website_id
        }
        
    except Website.DoesNotExist:
        logger.error(f"Website with id {website_id} not found")
        return {'status': 'error', 'message': 'Website not found'}
        
    except Exception as e:
        logger.error(f"Error in scrape_website_task: {str(e)}", exc_info=True)
        # Update status to failed
        try:
            website = Website.objects.get(id=website_id)
            website.status = 'f'  # STATUS_FAILED
            website.save()
        except:
            pass
        
        return {'status': 'error', 'message': str(e)}