from django.db import models
from django.utils import timezone
from django.conf import settings

class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    text = models.TextField() 
    
    created_date = models.DateTimeField(default=timezone.now)
    published_date = models.DateTimeField(blank=True, null=True)
    
    image = models.ImageField(upload_to='blog_image/%Y/%m/%d/', blank=True, null=True)

    confidence = models.CharField(max_length=10, blank=True, null=True)
    bbox = models.CharField(max_length=100, blank=True, null=True)

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.title
    
class AnalysisReport(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    summary = models.TextField()
    
    # Generic charts (Pie/Bar)
    plot_urls = models.TextField(help_text="Comma-separated URLs") 
    
    # [NEW] Structured data for Re-ID groups (JSON String)
    # Example: [{"id": 1, "count": 3, "url": "http..."}, ...]
    people_data = models.TextField(default="[]", help_text="JSON list of person groups") 

    class Meta:
        ordering = ['-created_at']