from django.db import models
from uuid import uuid4

class Website(models.Model):
    STATUS_PENDING = "p"
    STATUS_SCRAPING = "s"
    STATUS_COMPLETE = "c"
    STATUS_FAILED = "f"
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SCRAPING, 'Scraping'),
        (STATUS_COMPLETE, 'Complete'),
        (STATUS_FAILED, 'Failed')
    ]
    url = models.URLField(unique=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    total_pages = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title if self.title else self.url


class ScrapedPage(models.Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='pages')
    url = models.CharField(max_length=500)
    title = models.CharField(max_length=255, null=True, blank=True)
    content = models.TextField()
    vector_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title if self.title else self.url


class ChatSession(models.Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='chat_sessions')
    session_id = models.UUIDField(unique=True, default=uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.website} - {self.session_id}"


class Message(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    user_message = models.TextField()
    bot_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user_message[:50]  # First 50 characters
    
    class Meta:
        ordering = ['-timestamp']