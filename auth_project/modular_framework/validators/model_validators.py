"""
Model Doğrulama İşlemleri için Doğrulayıcılar

Bu modül, model alanları için özelleştirilmiş doğrulayıcı
fonksiyonları ve sınıfları içerir.
"""

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from decimal import Decimal

@deconstructible
class UniqueFieldValidator:
    """
    Belirli bir alan için benzersizlik doğrulayıcısı.
    
    Alanın değerinin belirtilen modelde benzersiz olmasını sağlar.
    Bir örnekte kullanılabilir (özellikle güncelleme durumlarında).
    
    Args:
        model: Kontrol edilecek model sınıfı
        field (str): Kontrol edilecek alan adı
        exclude_id (bool, optional): Geçerli örneği hariç tut. Varsayılan: True
        message (str, optional): Hata mesajı
    """
    def __init__(self, model, field, exclude_id=True, message=None):
        self.model = model
        self.field = field
        self.exclude_id = exclude_id
        self.message = message or _('Bu değer zaten kullanılıyor.')
        
    def __call__(self, value, instance=None):
        # Sorgu oluştur
        query = {self.field: value}
        
        # Geçerli örneği hariç tut
        if self.exclude_id and instance and instance.pk:
            existing = self.model.objects.filter(**query).exclude(pk=instance.pk).exists()
        else:
            existing = self.model.objects.filter(**query).exists()
        
        if existing:
            raise ValidationError(self.message)
    
    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.model == other.model and
            self.field == other.field and
            self.exclude_id == other.exclude_id and
            self.message == other.message
        )

@deconstructible
class UniqueTogetherValidator:
    """
    Birden fazla alan için birlikte benzersizlik doğrulayıcısı.
    
    Alan kombinasyonunun belirtilen modelde benzersiz olmasını sağlar.
    
    Args:
        model: Kontrol edilecek model sınıfı
        fields (list): Kontrol edilecek alan adları listesi
        exclude_id (bool, optional): Geçerli örneği hariç tut. Varsayılan: True
        message (str, optional): Hata mesajı
    """
    def __init__(self, model, fields, exclude_id=True, message=None):
        self.model = model
        self.fields = fields
        self.exclude_id = exclude_id
        self.message = message or _('Bu alan kombinasyonu zaten kullanılıyor.')
    
    def __call__(self, values, instance=None):
        # Değerler bir sözlük değilse, değerleri alanlarla eşleştir
        if not isinstance(values, dict):
            values = dict(zip(self.fields, values))
        
        # Sorgu oluştur
        query = Q()
        for field, value in values.items():
            query &= Q(**{field: value})
        
        # Geçerli örneği hariç tut
        if self.exclude_id and instance and instance.pk:
            existing = self.model.objects.filter(query).exclude(pk=instance.pk).exists()
        else:
            existing = self.model.objects.filter(query).exists()
        
        if existing:
            raise ValidationError(self.message)
    
    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.model == other.model and
            self.fields == other.fields and
            self.exclude_id == other.exclude_id and
            self.message == other.message
        )

def validate_price_range(min_price=None, max_price=None):
    """
    Fiyat aralığı doğrulama fonksiyonu üreteci.
    
    Args:
        min_price (Decimal, optional): Minimum fiyat
        max_price (Decimal, optional): Maksimum fiyat
        
    Returns:
        function: Doğrulayıcı fonksiyon
    """
    def validator(value):
        """
        Fiyatın belirtilen aralıkta olup olmadığını doğrular.
        
        Args:
            value: Doğrulanacak fiyat değeri
            
        Raises:
            ValidationError: Geçersiz fiyat değeri
        """
        if min_price is not None and value < min_price:
            raise ValidationError(_('Fiyat en az {min_price} olmalıdır.').format(min_price=min_price))
        
        if max_price is not None and value > max_price:
            raise ValidationError(_('Fiyat en fazla {max_price} olmalıdır.').format(max_price=max_price))
    
    return validator

def validate_date_range(start_field, end_field, equal_allowed=True):
    """
    Tarih aralığı doğrulayıcısı üreteci.
    
    İki tarih alanının sırasını doğrular.
    
    Args:
        start_field (str): Başlangıç tarihi alan adı
        end_field (str): Bitiş tarihi alan adı
        equal_allowed (bool, optional): Başlangıç ve bitiş tarihlerinin eşit olmasına izin verilsin mi?
        
    Returns:
        function: Model doğrulayıcı fonksiyonu
    """
    def validator(instance):
        """
        Model örneğindeki tarih aralığını doğrular.
        
        Args:
            instance: Doğrulanacak model örneği
            
        Raises:
            ValidationError: Geçersiz tarih aralığı
        """
        start_date = getattr(instance, start_field)
        end_date = getattr(instance, end_field)
        
        if start_date and end_date:
            if equal_allowed and start_date > end_date:
                raise ValidationError({
                    end_field: _('Bitiş tarihi, başlangıç tarihinden önce olamaz.')
                })
            elif not equal_allowed and start_date >= end_date:
                raise ValidationError({
                    end_field: _('Bitiş tarihi, başlangıç tarihinden sonra olmalıdır.')
                })
    
    return validator

@deconstructible
class MaximumInstancesValidator:
    """
    Bir model için maksimum örnek sayısı doğrulayıcısı.
    
    Args:
        model: Kontrol edilecek model sınıfı
        max_count (int): İzin verilen maksimum örnek sayısı
        filter_kwargs (dict, optional): Filtreleme parametreleri
        message (str, optional): Hata mesajı
    """
    def __init__(self, model, max_count, filter_kwargs=None, message=None):
        self.model = model
        self.max_count = max_count
        self.filter_kwargs = filter_kwargs or {}
        self.message = message or _('En fazla {max_count} kayıt oluşturabilirsiniz.')
    
    def __call__(self, value=None, instance=None):
        # Mevcut kayıt sayısını kontrol et
        query = self.model.objects.filter(**self.filter_kwargs)
        
        # Geçerli örneği hariç tut
        if instance and instance.pk:
            query = query.exclude(pk=instance.pk)
        
        count = query.count()
        
        if count >= self.max_count:
            raise ValidationError(self.message.format(max_count=self.max_count))
    
    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.model == other.model and
            self.max_count == other.max_count and
            self.filter_kwargs == other.filter_kwargs and
            self.message == other.message
        ) 