"""
URL configuration for zam_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from myapp.views import list_commodities, commodity_history
from myapp.auth_views import (
    SendVerificationView, VerifyCodeView, LoginView, RegisterView,
    CreateAccountView, VerifyAndCreateAccountView, PasswordLoginView
)

# Simple test view for connectivity testing
def test_connection(request):
    return JsonResponse({
        'status': 'success',
        'message': 'Connection successful!',
        'client_ip': request.META.get('REMOTE_ADDR', 'unknown')
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('commodities/', list_commodities, name='list_commodities'),
    path('commodities/<int:commodity_id>/history/', commodity_history, name='commodity_history'),

    # Test endpoint for connectivity
    path('api/test-connection/', test_connection, name='test_connection'),

    # Authentication URLs
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/send-verification/', SendVerificationView.as_view(), name='send_verification'),
    path('auth/verify-code/', VerifyCodeView.as_view(), name='verify_code'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/password-login/', PasswordLoginView.as_view(), name='password_login'),

    # New Account Creation URLs
    path('auth/create-account/', CreateAccountView.as_view(), name='create_account'),
    path('auth/verify-and-create/', VerifyAndCreateAccountView.as_view(), name='verify_and_create'),

    # Include all core URLs
    path('', include('myapp.urls')),
]
