from django.http import JsonResponse

def api_root(request):
    return JsonResponse({
        'message': 'Welcome to Guitar Games API',
        'version': '1.0',
        'endpoints': {
            'auth': '/api/auth/'
        }
    })