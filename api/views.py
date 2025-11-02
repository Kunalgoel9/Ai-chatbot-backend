from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import Website, ScrapedPage, ChatSession, Message
from .serializers import (
    WebsiteSerializer, 
    ScrapedPageSerializer, 
    ChatSessionSerializer, 
    MessageSerializer
)
from scraper.tasks import scrape_website_task
from rag.qdrant_service import QdrantService
from rag.gemini_service import GeminiService


class WebsiteViewSet(viewsets.ModelViewSet):
    queryset = Website.objects.all().order_by('-created_at')
    serializer_class = WebsiteSerializer
    
    @action(detail=True, methods=['post'])
    def scrape(self, request, pk=None):
        """
        Trigger scraping for a specific website
        POST /api/websites/{id}/scrape/
        """
        website = self.get_object()
        
        # Check if already scraping
        if website.status == 's':
            return Response(
                {'message': 'Website is already being scraped'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Trigger Celery task
        task = scrape_website_task.delay(website.id)
        
        return Response({
            'message': 'Scraping started',
            'task_id': task.id,
            'website_id': website.id
        }, status=status.HTTP_202_ACCEPTED)


class ScrapedPageViewSet(viewsets.ModelViewSet):
    queryset = ScrapedPage.objects.all().order_by('-created_at')
    serializer_class = ScrapedPageSerializer
    
    def get_queryset(self):
        """
        Optionally filter scraped pages by website
        /api/scraped-pages/?website=1
        """
        queryset = ScrapedPage.objects.all().order_by('-created_at')
        website_id = self.request.query_params.get('website', None)
        if website_id is not None:
            queryset = queryset.filter(website_id=website_id)
        return queryset


class ChatSessionViewSet(viewsets.ModelViewSet):
    queryset = ChatSession.objects.all().order_by('-created_at')
    serializer_class = ChatSessionSerializer
    
    @action(detail=True, methods=['post'])
    def chat(self, request, pk=None):
        """
        Chat with AI about a website
        POST /api/chat-sessions/{id}/chat/
        Body: {"message": "your question"}
        """
        chat_session = self.get_object()
        user_message = request.data.get('message', '')
        
        if not user_message:
            return Response(
                {'error': 'Message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Initialize services
            qdrant = QdrantService()
            gemini = GeminiService()
            
            # Search for relevant context in Qdrant
            search_results = qdrant.search(user_message, limit=3)
            
            # Build context from search results
            context = "\n\n".join([
                f"Source: {result['title']}\nURL: {result['url']}\nContent: {result['content']}"
                for result in search_results
            ])
            
            # Generate response using Gemini
            if context:
                bot_response = gemini.generate_response(user_message, context)
            else:
                bot_response = "I couldn't find relevant information in the scraped content. Please make sure the website has been scraped."
            
            # Save message to database
            message = Message.objects.create(
                session=chat_session,
                user_message=user_message,
                bot_response=bot_response
            )
            
            return Response({
                'user_message': user_message,
                'bot_response': bot_response,
                'sources': search_results
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all().order_by('-timestamp')
    serializer_class = MessageSerializer