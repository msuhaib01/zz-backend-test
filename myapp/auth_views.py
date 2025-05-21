import os
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from twilio.rest import Client
from .models import User, PhoneVerification
from .serializers import UserSerializer, PhoneVerificationSerializer, VerifyCodeSerializer, LoginSerializer, UserRegistrationSerializer

# Initialize Twilio client
twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
verify_service_sid = settings.TWILIO_VERIFY_SERVICE_SID

class SendVerificationView(APIView):
    """
    Send a verification code to the provided phone number
    """
    def post(self, request):
        serializer = PhoneVerificationSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            
            try:
                # Send verification code via Twilio
                verification = twilio_client.verify.v2.services(verify_service_sid) \
                    .verifications.create(to=phone_number, channel="sms")
                
                # Store verification SID
                phone_verification, created = PhoneVerification.objects.update_or_create(
                    phone_number=phone_number,
                    defaults={'verification_sid': verification.sid}
                )
                
                return Response({
                    'message': 'Verification code sent successfully',
                    'phone_number': phone_number,
                    'status': verification.status
                })
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyCodeView(APIView):
    """
    Verify the code sent to the phone number and register/login the user
    """
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            code = serializer.validated_data['code']
            
            try:
                # Verify the code with Twilio
                verification_check = twilio_client.verify.v2.services(verify_service_sid) \
                    .verification_checks.create(to=phone_number, code=code)
                
                if verification_check.status == "approved":
                    # Check if user exists, if not create a new one
                    user, created = User.objects.get_or_create(
                        phone_number=phone_number,
                        defaults={'is_verified': True}
                    )
                    
                    if not created:
                        user.is_verified = True
                        user.save()
                    
                    # Generate or get auth token
                    token, _ = Token.objects.get_or_create(user=user)
                    
                    return Response({
                        'message': 'Phone number verified successfully',
                        'user': UserSerializer(user).data,
                        'token': token.key,
                        'is_new_user': created
                    })
                else:
                    return Response({
                        'error': 'Invalid verification code',
                        'status': verification_check.status
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    """
    Login with phone number (sends verification code)
    """
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            
            # Check if user exists
            user = User.objects.filter(phone_number=phone_number).first()
            if not user:
                return Response({
                    'error': 'User with this phone number does not exist',
                    'phone_number': phone_number
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Send verification code
            try:
                verification = twilio_client.verify.v2.services(verify_service_sid) \
                    .verifications.create(to=phone_number, channel="sms")
                
                # Store verification SID
                phone_verification, created = PhoneVerification.objects.update_or_create(
                    phone_number=phone_number,
                    defaults={'verification_sid': verification.sid}
                )
                
                return Response({
                    'message': 'Verification code sent successfully',
                    'phone_number': phone_number,
                    'status': verification.status
                })
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(APIView):
    """
    Register a new user with full details
    """
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate auth token
            token, _ = Token.objects.get_or_create(user=user)
            
            return Response({
                'message': 'User registered successfully',
                'user': UserSerializer(user).data,
                'token': token.key
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreateAccountView(APIView):
    """
    Complete account creation flow:
    1. Send verification code
    2. Verify code and create account
    """
    def post(self, request):
        # Step 1: Send verification code
        phone_serializer = PhoneVerificationSerializer(data=request.data)
        if not phone_serializer.is_valid():
            return Response(phone_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        phone_number = phone_serializer.validated_data['phone_number']
        
        # Check if user already exists
        if User.objects.filter(phone_number=phone_number).exists():
            return Response({
                'error': 'User with this phone number already exists',
                'phone_number': phone_number
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Send verification code via Twilio
            verification = twilio_client.verify.v2.services(verify_service_sid) \
                .verifications.create(to=phone_number, channel="sms")
            
            # Store verification SID
            phone_verification, created = PhoneVerification.objects.update_or_create(
                phone_number=phone_number,
                defaults={'verification_sid': verification.sid}
            )
            
            return Response({
                'message': 'Verification code sent successfully',
                'phone_number': phone_number,
                'status': verification.status,
                'next_step': 'verify_code'
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class VerifyAndCreateAccountView(APIView):
    """
    Verify code and create account with full details
    """
    def post(self, request):
        # Verify code first
        verify_serializer = VerifyCodeSerializer(data=request.data)
        if not verify_serializer.is_valid():
            return Response(verify_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        phone_number = verify_serializer.validated_data['phone_number']
        code = verify_serializer.validated_data['code']
        
        try:
            # Verify the code with Twilio
            verification_check = twilio_client.verify.v2.services(verify_service_sid) \
                .verification_checks.create(to=phone_number, code=code)
            
            if verification_check.status == "approved":
                # Create user with full details
                user_serializer = UserRegistrationSerializer(data=request.data)
                if user_serializer.is_valid():
                    user = user_serializer.save(is_verified=True)
                    
                    # Generate auth token
                    token, _ = Token.objects.get_or_create(user=user)
                    
                    return Response({
                        'message': 'Account created successfully',
                        'user': UserSerializer(user).data,
                        'token': token.key
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'error': 'Invalid verification code',
                    'status': verification_check.status
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class PasswordLoginView(APIView):
    """
    Login with phone number and password
    """
    def post(self, request):
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')
        
        if not phone_number or not password:
            return Response({
                'error': 'Phone number and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Find user by phone number
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({
                'error': 'User with this phone number does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
            
        # Check password
        if not user.check_password(password):
            return Response({
                'error': 'Invalid password'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        # Generate or get auth token
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response({
            'message': 'Login successful',
            'user': UserSerializer(user).data,
            'token': token.key
        }) 