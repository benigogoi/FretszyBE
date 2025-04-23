# authentication/urls.py
from django.urls import path
from .views import (
    GoogleLoginView, RegisterView, LoginView, LogoutView, UserView, active_users,
    GameScoreView, leaderboard  # Add these new views
)

urlpatterns = [
    path('auth/google/', GoogleLoginView.as_view(), name='google-login'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/user/', UserView.as_view(), name='user'),
    path('auth/active-users/', active_users, name='active-users'),
    
    # Game score endpoints
    path('game-scores/', GameScoreView.as_view(), name='game-scores'),
    path('leaderboard/', leaderboard, name='leaderboard'),
]