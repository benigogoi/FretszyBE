# authentication/admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.sessions.models import Session
from .models import GameScore

User = get_user_model()

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'provider', 'is_online', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'provider')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'photo_url')}),
        (_('Authentication'), {'fields': ('provider',)}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    def is_online(self, user):
        """Check if the user is currently online"""
        # Consider a user online if their last_login is within the last 15 minutes
        if not user.last_login:
            return False
            
        return user.last_login >= timezone.now() - timezone.timedelta(minutes=15)
    
    is_online.boolean = True
    is_online.short_description = 'Online'
    
    def get_queryset(self, request):
        # Add the count of online users to the admin context
        qs = super().get_queryset(request)
        
        # Calculate online users (last login within 15 minutes)
        fifteen_minutes_ago = timezone.now() - timezone.timedelta(minutes=15)
        online_count = qs.filter(last_login__gte=fifteen_minutes_ago).count()
        
        # Store the online count for use in the changelist template
        request.online_users_count = online_count
        
        return qs
    
    def changelist_view(self, request, extra_context=None):
        # Add online users count to the changelist context
        extra_context = extra_context or {}
        
        # Get the online count (either from request or calculate it)
        if hasattr(request, 'online_users_count'):
            extra_context['online_users_count'] = request.online_users_count
        else:
            fifteen_minutes_ago = timezone.now() - timezone.timedelta(minutes=15)
            online_count = User.objects.filter(last_login__gte=fifteen_minutes_ago).count()
            extra_context['online_users_count'] = online_count
            
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(GameScore)
class GameScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'game_type', 'score', 'date_achieved', 'fret_length', 'start_string', 'end_string')
    list_filter = ('game_type', 'date_achieved')
    search_fields = ('user__username', 'user__email')
    ordering = ('-score', '-date_achieved')