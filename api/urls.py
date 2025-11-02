from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import WebsiteViewSet, ScrapedPageViewSet, ChatSessionViewSet, MessageViewSet

router = DefaultRouter()
router.register('websites', WebsiteViewSet, basename='websites')
router.register('scraped-pages', ScrapedPageViewSet, basename='scraped-pages')
router.register('chat-sessions', ChatSessionViewSet, basename='chat-sessions')
router.register('messages', MessageViewSet, basename='messages')

urlpatterns = router.urls