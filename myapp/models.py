from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# Create your models here.
class Location(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Location"
        verbose_name_plural = "Locations"
        ordering = ['name']

    def __str__(self):
        return self.name
class Commodity(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Commodity"
        verbose_name_plural = "Commodities"

    def __str__(self):
        return self.name


class PriceEntry(models.Model):
    commodity = models.ForeignKey(Commodity, on_delete=models.CASCADE, related_name='prices')
    date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='price_entries')

    class Meta:
        verbose_name = "Price Entry"
        verbose_name_plural = "Price Entries"

    def __str__(self):
        return f"{self.commodity.name} - {self.location.name} - {self.date} - {self.price}"


class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('The Phone Number field must be set')

        user = self.model(
            phone_number=phone_number,
            **extra_fields
        )
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('email'):
            raise ValueError('Superuser must have an email address')
        if not extra_fields.get('full_name'):
            raise ValueError('Superuser must have a full name')

        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    full_name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    preferred_commodity = models.ForeignKey('Commodity', on_delete=models.SET_NULL, null=True, blank=True)

    # Add related_name to fix the clash
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='myapp_user_groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='myapp_user_permissions'
    )

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone_number
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    preferred_commodity = models.ForeignKey('Commodity', on_delete=models.SET_NULL, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['email', 'full_name']

    objects = UserManager()

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"

class PhoneVerification(models.Model):
    phone_number = models.CharField(max_length=15)
    verification_sid = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Verification for {self.phone_number}"
