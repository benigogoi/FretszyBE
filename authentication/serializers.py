# authentication/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import GameScore

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'photo_url', 'provider', 'date_joined', 'last_login']
        read_only_fields = ['id', 'date_joined', 'last_login']

class GoogleAuthSerializer(serializers.Serializer):
    credential = serializers.CharField(required=True)

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    
    def validate_email(self, value):
        # Normalize email to lowercase
        return value.lower()
    
    def validate_password(self, value):
        # Add password validation if needed
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate_email(self, value):
        # Normalize email to lowercase
        return value.lower()

class GameScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameScore
        fields = ['id', 'user', 'game_type', 'score', 'date_achieved', 'fret_length', 'start_string', 'end_string']
        read_only_fields = ['id', 'date_achieved']

class GameScoreSummarySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = GameScore
        fields = ['score', 'date_achieved', 'fret_length', 'start_string', 'end_string', 'username']