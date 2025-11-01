
from rest_framework import serializers
from . models import Website,ScrapedPage,ChatSession,Message

class WebsiteSerializer(serializers.ModelSerializer):
    class Meta:
        model=Website
        fields=['url','title','total_pages','status','created_at','updated_at']

class ScrapedPageSerializer(serializers.ModelSerializer):
    class Meta:
        model=ScrapedPage
        fields=['website','url','title','content','vector_id','created_at']

class MessageSerializer (serializers.ModelSerializer):
    class Meta:
        model=Message
        fields=['session','user_message','bot_response','timestamp']

class ChatSessionSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    class Meta:
        model=ChatSession
        fields=['website','session_id','created_at','messages']

