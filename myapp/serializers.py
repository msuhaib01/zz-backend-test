from rest_framework import serializers
from .models import User, PhoneVerification

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['full_name', 'phone_number', 'email', 'password', 'preferred_commodity']
        extra_kwargs = {
            'password': {'write_only': True},
            'preferred_commodity': {'required': False}
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'phone_number', 'email', 'preferred_commodity', 'is_verified', 'date_joined']
        read_only_fields = ['is_verified', 'date_joined']
        
class PhoneVerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    
class VerifyCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=10)
    
class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=10, required=False) 