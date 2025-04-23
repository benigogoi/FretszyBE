# authentication/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    # Fields from AbstractUser: username, email, first_name, last_name, is_staff, is_active, date_joined
    
    # Custom fields
    photo_url = models.URLField(max_length=500, blank=True, null=True)
    provider = models.CharField(max_length=20, default='email', 
                               choices=[('google', 'Google'), ('facebook', 'Facebook'), ('email', 'Email')])
    last_login = models.DateTimeField(_('last login'), blank=True, null=True)
    
    def __str__(self):
        return self.email

class GameScore(models.Model):
    """Model to store game scores for users"""
    GAME_TYPES = [
        ('fretboard', 'Fretboard Note Finder'),
        # Add other game types as needed
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_scores')
    game_type = models.CharField(max_length=50, choices=GAME_TYPES)
    score = models.IntegerField()
    date_achieved = models.DateTimeField(auto_now_add=True)
    
    # Game configuration (for fretboard game)
    fret_length = models.IntegerField(default=12)
    start_string = models.IntegerField(default=6)
    end_string = models.IntegerField(default=1)
    
    class Meta:
        # Get the highest score for each user and game type
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'game_type', 'fret_length', 'start_string', 'end_string'],
                name='unique_game_config'
            )
        ]
        ordering = ['-score', '-date_achieved']
    
    def __str__(self):
        return f"{self.user.username} - {self.game_type} - {self.score}"