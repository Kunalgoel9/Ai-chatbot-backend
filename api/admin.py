from django.contrib import admin
from . models import Website,ChatSession,Message,ScrapedPage
# Register your models here.


@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display=['url','title','total_pages','status','created_at','updated_at']
    list_per_page=10

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display=['website','session_id','created_at']
    list_per_page=10
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display=['session','user_message','bot_response','timestamp']
    list_per_page=10
@admin.register(ScrapedPage)
class ScrapedPageAdmin(admin.ModelAdmin):
    list_display=['website','url','title','content','vector_id','created_at']
    list_per_page=10

