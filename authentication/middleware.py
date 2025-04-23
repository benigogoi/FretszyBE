# authentication/middleware.py
from django.utils import timezone

class UpdateLastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Update last_login for authenticated users
        if request.user.is_authenticated:
            # Using update to avoid triggering signal handlers
            request.user.__class__.objects.filter(pk=request.user.pk).update(
                last_login=timezone.now()
            )
            
        return response