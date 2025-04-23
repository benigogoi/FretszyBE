from django.contrib import admin
from django.urls import path, include
from .views import api_root  # Import the view we created

urlpatterns = [
    path('', api_root, name='api-root'),  # Add this line
    path('admin/', admin.site.urls),
    path('api/', include('authentication.urls')),
]