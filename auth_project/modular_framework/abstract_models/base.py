"""
Temel Model Sınıfları

Bu modül, diğer tüm modeller için temel sınıfları içerir.
"""
from django.db import models

class BaseModel(models.Model):
    """
    Tüm modeller için temel model
    
    Oluşturulma ve güncellenme tarihlerini otomatik olarak takip eder.
    
    Attributes:
        created_at (DateTimeField): Kaydın oluşturulma tarihi ve saati
        updated_at (DateTimeField): Kaydın son güncellenme tarihi ve saati
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True 