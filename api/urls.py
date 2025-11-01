
from django.urls import path

from . views import WebsiteViewSet,ChatSessionViewSet,MessageViewSet

from rest_framework.routers import DefaultRouter

router=DefaultRouter()

router.register('websites',viewset=WebsiteViewSet,basename='websites')
router.register('chat-sessions',viewset=ChatSessionViewSet,basename='chat-sessions')
router.register('messages',viewset=MessageViewSet,basename='messages')
urlpatterns = router.urls
