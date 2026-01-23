from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class IssueCategory(models.Model):
    """Categories of civic issues"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='📋', help_text="Emoji or icon identifier")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Issue Categories"


class Issue(models.Model):
    """A civic issue reported by a user"""
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_issues')
    category = models.ForeignKey(IssueCategory, on_delete=models.PROTECT, related_name='issues')
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='issues/')
    
    # Location data
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_text = models.CharField(max_length=500, blank=True, help_text="Human-readable location")
    
    # Assignment
    assigned_authority = models.ForeignKey('authorities.Authority', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_issues')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    def get_absolute_url(self):
        return reverse('issues:detail', kwargs={'pk': self.pk})
    
    class Meta:
        ordering = ['-created_at']


class IssueUpdate(models.Model):
    """Status updates posted by authorities"""
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='updates')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='issue_updates')
    status = models.CharField(max_length=20, choices=Issue.STATUS_CHOICES)
    notes = models.TextField(help_text="Measures taken, actions, etc.")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Update for {self.issue.title} by {self.author.email}"
    
    class Meta:
        ordering = ['-created_at']
