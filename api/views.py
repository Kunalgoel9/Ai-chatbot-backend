from django.shortcuts import render
from . serializers import WebsiteSerializer,ChatSessionSerializer,MessageSerializer
from . models import Website,ChatSession,Message
from rest_framework.viewsets import ModelViewSet,GenericViewSet
# Create your views here.


class WebsiteViewSet(ModelViewSet):
    queryset = Website.objects.all().order_by('-created_at')
    serializer_class = WebsiteSerializer


class ChatSessionViewSet(ModelViewSet):
    queryset = ChatSession.objects.all().order_by('-created_at')
    serializer_class = ChatSessionSerializer


class MessageViewSet(ModelViewSet):
    queryset = Message.objects.all().order_by('-timestamp')
    serializer_class = MessageSerializer

      

