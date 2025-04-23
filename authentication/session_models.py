from django.db import models
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        
    def __str__(self):
        return f"{self.user.username} - {self.last_activity}"
    
    @classmethod
    def remove_expired_sessions(cls):
        """Remove UserSession records that have expired sessions"""
        active_sessions = Session.objects.filter(expire_date__gt=timezone.now())
        active_keys = active_sessions.values_list('session_key', flat=True)
        cls.objects.exclude(session_key__in=active_keys).delete()