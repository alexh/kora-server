# from django.db import models

# class ProductIdea(models.Model):
#     timestamp = models.DateTimeField(auto_now_add=True)
#     idea = models.TextField()
#     customer_email = models.EmailField(null=True, blank=True)
#     customer_phone = models.CharField(max_length=20, null=True, blank=True)
    
#     class Meta:
#         ordering = ['-timestamp'] 

#     def __str__(self):
#         return f"Product idea from {self.customer_email or 'anonymous'}"


# class Issue(models.Model):
#     SEVERITY_CHOICES = [
#         ('LOW', 'Low'),
#         ('MEDIUM', 'Medium'),
#         ('HIGH', 'High'),
#         ('CRITICAL', 'Critical'),
#     ]
    
#     description = models.TextField()
#     severity = models.CharField(max_length=8, choices=SEVERITY_CHOICES, default='MEDIUM')
#     customer_email = models.EmailField(null=True, blank=True)
#     customer_phone = models.CharField(max_length=20, null=True, blank=True)
#     timestamp = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering = ['-timestamp']

#     def __str__(self):
#         return f"{self.severity} issue: {self.description[:50]}"
