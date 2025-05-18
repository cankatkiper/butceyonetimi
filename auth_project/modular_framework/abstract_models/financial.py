"""
Finansal İşlemler için Soyut Model Sınıfları

Bu modül, finansal işlemlerle ilgili tüm soyut model sınıflarını içerir.
Kategori, İşlem, Harcama Limiti ve Tasarruf Hedefi gibi finansal modeller için
temel sınıflar burada tanımlanır.
"""
from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from .base import BaseModel

class FinancialCategory(models.Model):
    """
    Kategori modeli - Gelir/Gider kategorileri için
    
    Attributes:
        name (CharField): Kategori adı
        type (CharField): Kategori türü ('gelir' veya 'gider')
        icon (CharField, optional): Kategori için ikon adı
    """
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
    """
    İşlem modeli - Gelir/Gider işlemleri için temel model
    
    Attributes:
        user (ForeignKey): İşlemi yapan kullanıcı
        amount (DecimalField): İşlem tutarı
        description (CharField, optional): İşlem açıklaması 
        date (DateField): İşlem tarihi
        is_regular (BooleanField): Düzenli bir işlem mi
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="%(app_label)s_%(class)s")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.CharField(max_length=200, blank=True, null=True)
    date = models.DateField(default=timezone.now)
    is_regular = models.BooleanField(default=False)
    
    class Meta:
        abstract = True
        ordering = ['-date']

class AbstractSpendingLimit(BaseModel):
    """
    Harcama Limiti modeli - kategorilere göre harcama limitlemesi için
    
    Attributes:
        user (ForeignKey): Limiti tanımlayan kullanıcı
        amount (DecimalField): Limit tutarı
        period (CharField): Limit dönemi ('daily', 'weekly', 'monthly')
        start_date (DateField): Limit başlangıç tarihi
    """
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
    """
    Tasarruf hedefi modeli - tasarruf hedefleri için
    
    Attributes:
        user (ForeignKey): Hedefi tanımlayan kullanıcı
        name (CharField): Hedef adı
        target_amount (DecimalField): Hedef tutar
        current_amount (DecimalField): Mevcut tutar
        target_date (DateField): Hedef tarih
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="%(app_label)s_%(class)s")
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=15, decimal_places=2)
    current_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    target_date = models.DateField()
    
    def progress_percentage(self):
        """Hedefin yüzde olarak tamamlanma oranını hesaplar"""
        if self.target_amount == 0:
            return 0
        return (self.current_amount / self.target_amount) * 100
    
    class Meta:
        abstract = True 