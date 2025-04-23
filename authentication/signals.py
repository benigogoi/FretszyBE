# authentication/signals.py
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.sessions.models import Session
from django.dispatch import receiver
from .session_models import UserSession

@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    if not request or not hasattr(request, 'session') or not request.session.session_key:
        return
    
    # Get or create a session for this user
    UserSession.objects.update_or_create(
        session_key=request.session.session_key,
        defaults={
            'user': user,
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')
        }
    )
    
    # Clean up expired sessions
    UserSession.remove_expired_sessions()

@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    if not request or not hasattr(request, 'session') or not request.session.session_key:
        return
    
    # Delete the user session
    UserSession.objects.filter(session_key=request.session.session_key).delete()

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip