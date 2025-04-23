# authentication/views.py
import json
from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from google.oauth2 import id_token
from google.auth.transport import requests

from .serializers import (
    UserSerializer, 
    GoogleAuthSerializer, 
    RegisterSerializer, 
    LoginSerializer,
    GameScoreSerializer,
    GameScoreSummarySerializer
)
from .session_models import UserSession
from .models import GameScore

User = get_user_model()

class GoogleLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = GoogleAuthSerializer

    def post(self, request):
        print("Received Google login request")
        
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            print(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        credential = serializer.validated_data.get('credential')
        print(f"Credential received: {credential[:20]}...")  # Log part of the credential for debugging
        
        try:
            # Verify the Google token
            print(f"Verifying token with client ID: {settings.GOOGLE_OAUTH2_CLIENT_ID}")
            idinfo = id_token.verify_oauth2_token(
                credential, requests.Request(), settings.GOOGLE_OAUTH2_CLIENT_ID)
            
            print(f"Token verified. User info: {idinfo.get('email')}")
            
            # Check if token is valid for our audience (client ID)
            if idinfo['aud'] != settings.GOOGLE_OAUTH2_CLIENT_ID:
                raise ValueError('Invalid audience')
            
            # Get user details from the token
            email = idinfo.get('email')
            if not email:
                return Response({'error': 'Email not found in token'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if the email is verified by Google
            if not idinfo.get('email_verified', False):
                return Response({'error': 'Email not verified by Google'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract user information
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            photo_url = idinfo.get('picture', '')
            
            # Create username from email
            username = email.split('@')[0]
            
            # Try to find existing user by email
            try:
                user = User.objects.get(email=email)
                # Update existing user info
                user.first_name = first_name
                user.last_name = last_name
                user.photo_url = photo_url
                user.provider = 'google'
                user.save()
                print(f"Updated existing user: {user.email}")
            except User.DoesNotExist:
                # Create new user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    photo_url=photo_url,
                    provider='google',
                    # Don't set password for social auth users
                )
                print(f"Created new user: {user.email}")
            
            # Generate or get token for the user
            token, created = Token.objects.get_or_create(user=user)
            
            # Prepare user data for response
            user_serializer = UserSerializer(user)
            
            # Return token and user data
            return Response({
                'token': token.key,
                'user': user_serializer.data
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            print(f"Google token verification error: {str(e)}")
            return Response({'error': f'Invalid token: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return Response({'error': f'Server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Create new user with validated data
        user_data = serializer.validated_data
        
        # Create username from email
        username = user_data['email'].split('@')[0]
        
        # Check if user with this email already exists
        if User.objects.filter(email=user_data['email']).exists():
            return Response({'error': 'User with this email already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=user_data['email'],
            password=user_data['password'],
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', ''),
            provider='email'
        )
        
        # Generate token for the user
        token, created = Token.objects.get_or_create(user=user)
        
        # Prepare user data for response
        user_serializer = UserSerializer(user)
        
        # Return token and user data
        return Response({
            'token': token.key,
            'user': user_serializer.data
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        # Try to get user by email first
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Authenticate with username and password
        user = authenticate(username=username, password=password)
        
        if user:
            # Generate token for the user
            token, created = Token.objects.get_or_create(user=user)
            
            # Prepare user data for response
            user_serializer = UserSerializer(user)
            
            # Return token and user data
            return Response({
                'token': token.key,
                'user': user_serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    def post(self, request):
        # Delete the user's token to logout
        if request.user.is_authenticated:
            Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_200_OK)

class UserView(APIView):
    def get(self, request):
        # Get current user's data
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def active_users(request):
    """
    Get a list of currently active users
    """
    # Get sessions active in the last 15 minutes
    threshold = timezone.now() - timezone.timedelta(minutes=15)
    active_sessions = UserSession.objects.filter(last_activity__gt=threshold)
    
    # Get unique users from these sessions
    users = [session.user for session in active_sessions]
    unique_users = list({user.id: user for user in users}.values())
    
    serializer = UserSerializer(unique_users, many=True)
    return Response({
        'active_users_count': len(unique_users),
        'users': serializer.data
    })

# GameScore views
class GameScoreView(APIView):
    """
    API endpoint for managing user game scores
    """
    def get(self, request):
        """Get the user's best score for a specific game with specific configuration"""
        user = request.user
        game_type = request.query_params.get('game_type', 'fretboard')
        
        # Convert parameters to integers to ensure proper comparison
        try:
            fret_length = int(request.query_params.get('fret_length', 12))
            start_string = int(request.query_params.get('start_string', 6))
            end_string = int(request.query_params.get('end_string', 1))
        except ValueError:
            # Handle case where parameters can't be converted to int
            return Response({
                'error': 'Invalid numeric parameters'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get current score from query parameters (for first-time players)
        current_score = request.query_params.get('current_score', None)
        if current_score is not None:
            try:
                current_score = int(current_score)
            except ValueError:
                current_score = 0
        
        try:
            # Get the best score for this game configuration
            best_score = GameScore.objects.filter(
                user=user,
                game_type=game_type,
                fret_length=fret_length,
                start_string=start_string,
                end_string=end_string
            ).order_by('-score').first()
            
            # Debugging
            print(f"Best score query for {user.username}: game_type={game_type}, fret_length={fret_length}, strings={start_string}-{end_string}")
            if best_score:
                print(f"Found best score: {best_score.score}, date: {best_score.date_achieved}")
            else:
                print("No scores found in database for this configuration")
            
            # For testing, you can set a default best score if none exists
            # Uncomment this to override with a test score (for debugging)
            # if not best_score:
            #    return Response({
            #        'score': 15,  # Hardcoded test score
            #        'date_achieved': timezone.now().isoformat(),
            #        'fret_length': fret_length,
            #        'start_string': start_string,
            #        'end_string': end_string,
            #        'username': user.username
            #    })
            
            if best_score:
                serializer = GameScoreSummarySerializer(best_score)
                return Response(serializer.data)
            else:
                # For first-time players, use the current score (if provided)
                score_value = current_score if current_score is not None else 0
                
                return Response({
                    'score': score_value,
                    'date_achieved': timezone.now().isoformat() if score_value > 0 else None,
                    'fret_length': fret_length,
                    'start_string': start_string,
                    'end_string': end_string,
                    'username': user.username
                })
                
        except Exception as e:
            print(f"Error in GameScoreView.get: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Save a new game score"""
        # Add the user to the data
        data = request.data.copy()
        data['user'] = request.user.id
        
        # Debug output
        print(f"GameScoreView.post: Received data: {data}")
        
        # Ensure numeric fields are integers
        for field in ['fret_length', 'start_string', 'end_string', 'score']:
            if field in data:
                try:
                    data[field] = int(data[field])
                except (ValueError, TypeError):
                    print(f"Invalid value for field {field}: {data.get(field)}")
                    return Response({
                        'error': f'Invalid value for {field}'
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if a record with this configuration already exists
        try:
            existing_score = GameScore.objects.get(
                user=request.user,
                game_type=data.get('game_type', 'fretboard'),
                fret_length=data.get('fret_length', 12),
                start_string=data.get('start_string', 6),
                end_string=data.get('end_string', 1)
            )
            
            print(f"Found existing score: {existing_score.score}")
            
            # Only update if the new score is higher
            if data['score'] > existing_score.score:
                existing_score.score = data['score']
                existing_score.date_achieved = timezone.now()  # Update timestamp to current time
                existing_score.save()
                print(f"Updated score to: {existing_score.score}")
                serializer = GameScoreSerializer(existing_score)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                # Return the existing score if it's higher
                print(f"Keeping existing higher score: {existing_score.score}")
                serializer = GameScoreSerializer(existing_score)
                return Response(serializer.data, status=status.HTTP_200_OK)
                
        except GameScore.DoesNotExist:
            # Create a new score record
            print("No existing score found. Creating new record.")
            serializer = GameScoreSerializer(data=data)
            if serializer.is_valid():
                new_score = serializer.save()
                print(f"Created new score record: {new_score.score}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            print(f"Serializer validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error in GameScoreView.post: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def leaderboard(request):
    """Get the leaderboard for a specific game"""
    game_type = request.query_params.get('game_type', 'fretboard')
    fret_length = request.query_params.get('fret_length', 12)
    start_string = request.query_params.get('start_string', 6)
    end_string = request.query_params.get('end_string', 1)
    limit = int(request.query_params.get('limit', 10))
    
    # Get the top scores
    top_scores = GameScore.objects.filter(
        game_type=game_type,
        fret_length=fret_length,
        start_string=start_string,
        end_string=end_string
    ).order_by('-score')[:limit]
    
    serializer = GameScoreSummarySerializer(top_scores, many=True)
    return Response(serializer.data)