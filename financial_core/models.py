from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal

class BaseModel(models.Model):
    """Tüm modeller için temel model"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class FinancialCategory(models.Model):
    """Kategori modeli - Gelir/Gider kategorileri için"""
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
        verbose_name = "Financial Category"
        verbose_name_plural = "Financial Categories"
        abstract = True

class AbstractTransaction(BaseModel):
    """İşlem modeli - Gelir/Gider işlemleri için temel model"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="%(app_label)s_%(class)s")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.CharField(max_length=200, blank=True, null=True)
    date = models.DateField(default=timezone.now)
    is_regular = models.BooleanField(default=False)
    
    class Meta:
        abstract = True
        ordering = ['-date']

class AbstractSpendingLimit(BaseModel):
    """Harcama Limiti modeli - kategorilere göre harcama limitlemesi için"""
    PERIOD_CHOICES = [
        ('daily', 'Günlük'),
        ('weekly', 'Haftalık'),
        ('monthly', 'Aylık'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="%(app_label)s_%(class)s")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='monthly')
    start_date = models.DateField(default=timezone.now)
    
    class Meta:
        abstract = True
        
class AbstractSavingGoal(BaseModel):
    """Tasarruf hedefi modeli - tasarruf hedefleri için"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="%(app_label)s_%(class)s")
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=15, decimal_places=2)
    current_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    target_date = models.DateField()
    
    def progress_percentage(self):
        if self.target_amount == 0:
            return 0
        return (self.current_amount / self.target_amount) * 100
    
    class Meta:
        abstract = True
