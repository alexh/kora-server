from django.db import models

class ProductIdea(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    idea = models.TextField()
    customer_email = models.EmailField(null=True, blank=True)
    customer_phone = models.CharField(max_length=20, null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp'] 