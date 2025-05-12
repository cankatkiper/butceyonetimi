# Create your models here.

from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.utils import timezone
from decimal import Decimal

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    financial_info_completed = models.BooleanField(default=False)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    def __str__(self):
        return self.email

class PasswordResetToken(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - {self.token}"

class Category(models.Model):
    CATEGORY_TYPES = [
        ('gelir', 'Gelir'),
        ('gider', 'Gider'),
    ]
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=5, choices=CATEGORY_TYPES)
    icon = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Kategoriler"

class Transaction(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='transactions')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.CharField(max_length=200, blank=True, null=True)
    date = models.DateField(default=timezone.now)
    is_regular = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.category.name} - {self.amount}"
    
    class Meta:
        ordering = ['-date']

class SavingGoal(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='saving_goals')
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=15, decimal_places=2)
    current_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    target_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def progress_percentage(self):
        if self.target_amount == 0:
            return 0
        return (self.current_amount / self.target_amount) * 100
    
    def __str__(self):
        return f"{self.name} ({self.progress_percentage():.2f}%)"

class PurchaseGoal(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='purchase_goals')
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=15, decimal_places=2)
    trigger_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    is_notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def can_purchase(self, user_total_amount):
        return (self.price / user_total_amount) * 100 <= self.trigger_percentage
    
    def __str__(self):
        return f"{self.name} ({self.price})"

class SpendingLimit(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='spending_limits')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    period = models.CharField(max_length=10, choices=[
        ('daily', 'Günlük'),
        ('weekly', 'Haftalık'),
        ('monthly', 'Aylık'),
    ], default='monthly')
    start_date = models.DateField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.username} - {self.category.name} - {self.amount} ({self.get_period_display()})"
    
    def current_spending(self):
        if self.period == 'daily':
            today = timezone.now().date()
            transactions = Transaction.objects.filter(
                user=self.user,
                category=self.category,
                date=today
            )
        elif self.period == 'weekly':
            today = timezone.now().date()
            start_of_week = today - timezone.timedelta(days=today.weekday())
            end_of_week = start_of_week + timezone.timedelta(days=6)
            transactions = Transaction.objects.filter(
                user=self.user,
                category=self.category,
                date__range=[start_of_week, end_of_week]
            )
        elif self.period == 'monthly':
            today = timezone.now().date()
            transactions = Transaction.objects.filter(
                user=self.user,
                category=self.category,
                date__year=today.year,
                date__month=today.month
            )
        else:
            return Decimal(0)
        
        return sum(t.amount for t in transactions)
    
    def is_exceeded(self):
        return self.current_spending() > self.amount


