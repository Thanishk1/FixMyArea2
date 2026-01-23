from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """Extended user profile with role information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_authority = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - {'Authority' if self.is_authority else 'Reporter'}"
