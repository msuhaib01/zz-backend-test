from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Commodity, PriceEntry, PhoneVerification
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from datetime import date

User = get_user_model()

class ModelTests(TestCase):
    def setUp(self):
        self.commodity = Commodity.objects.create(name="Wheat")
        self.user = User.objects.create_user(
            phone_number="+1234567890",
            email="test@example.com",
            full_name="Test User"
        )
        
    def test_commodity_creation(self):
        """Test commodity model creation"""
        self.assertEqual(str(self.commodity), "Wheat")
        
    def test_price_entry_creation(self):
        """Test price entry model creation"""
        price_entry = PriceEntry.objects.create(
            commodity=self.commodity,
            date=date.today(),
            price=Decimal("100.50")
        )
        self.assertEqual(str(price_entry), f"Wheat - {date.today()} - 100.50")
        
    def test_user_creation(self):
        """Test user model creation"""
        self.assertEqual(str(self.user), "Test User (+1234567890)")
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        
    def test_phone_verification_creation(self):
        """Test phone verification model creation"""
        verification = PhoneVerification.objects.create(
            phone_number="+1234567890",
            verification_sid="test_sid"
        )
        self.assertEqual(str(verification), "Verification for +1234567890")

class APITests(APITestCase):
    def setUp(self):
        self.client = Client()
        self.commodity = Commodity.objects.create(name="Wheat")
        self.user = User.objects.create_user(
            phone_number="+1234567890",
            email="test@example.com",
            full_name="Test User"
        )
        
    def test_commodity_list_api(self):
        """Test commodity list API endpoint"""
        response = self.client.get('/commodities/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(isinstance(response.json(), list))
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['name'], "Wheat")
        
    def test_commodity_history_api(self):
        """Test commodity history API endpoint"""
        # Create a price entry
        PriceEntry.objects.create(
            commodity=self.commodity,
            date=date.today(),
            price=Decimal("100.50")
        )
        
        response = self.client.get(f'/commodities/{self.commodity.id}/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['commodity_name'], "Wheat")
        self.assertEqual(len(response.json()['data']), 1)
        
    def test_send_verification(self):
        """Test sending verification code"""
        response = self.client.post('/auth/send-verification/', {
            'phone_number': '+923058760414'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['message'], 'Verification code sent successfully')
        
    def test_register_user(self):
        """Test user registration"""
        response = self.client.post('/auth/register/', {
            'phone_number': '+1987654321',
            'email': 'new@example.com',
            'full_name': 'New User',
            'password': 'newpass123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        
    def test_login(self):
        """Test login (sends verification code)"""
        # First, send verification code
        response = self.client.post('/auth/send-verification/', {
            'phone_number': '+923058760414'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # # Then verify the code (using a mock code for testing)
        # response = self.client.post('/auth/verify-code/', {
        #     'phone_number': '+1234567890',
        #     'code': '123456'
        # }, format='json')
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertIn('token', response.json())
