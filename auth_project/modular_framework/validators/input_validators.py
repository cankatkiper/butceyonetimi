"""
Girdi Doğrulama İşlemleri için Doğrulayıcılar

Bu modül, form ve model alanları için kullanılabilecek
doğrulayıcı fonksiyonları içerir.
"""

import re
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from decimal import Decimal, InvalidOperation

def validate_turkish_identity_number(value):
    """
    Türkiye Cumhuriyeti Kimlik Numarası doğrulama.
    
    Args:
        value (str): Doğrulanacak TC kimlik numarası
        
    Raises:
        ValidationError: Geçersiz TC kimlik numarası
    """
    value = str(value).strip()
    
    # 11 haneli olmalı ve rakamlardan oluşmalı
    if not value.isdigit() or len(value) != 11:
        raise ValidationError(_('TC kimlik numarası 11 haneli olmalı ve sadece rakamlardan oluşmalıdır.'))
    
    # İlk hane 0 olamaz
    if value[0] == '0':
        raise ValidationError(_('TC kimlik numarasının ilk hanesi 0 olamaz.'))
    
    # Algoritma doğrulaması
    digits = [int(d) for d in value]
    
    # 10. hane kontrolü
    odd_sum = sum(digits[0:9:2])
    even_sum = sum(digits[1:8:2])
    
    tenth_digit = (odd_sum * 7 - even_sum) % 10
    if tenth_digit != digits[9]:
        raise ValidationError(_('Geçersiz TC kimlik numarası.'))
    
    # 11. hane kontrolü
    if sum(digits[0:10]) % 10 != digits[10]:
        raise ValidationError(_('Geçersiz TC kimlik numarası.'))

def validate_turkish_tax_number(value):
    """
    Türkiye Vergi Kimlik Numarası doğrulama.
    
    Args:
        value (str): Doğrulanacak vergi kimlik numarası
        
    Raises:
        ValidationError: Geçersiz vergi kimlik numarası
    """
    value = str(value).strip()
    
    # 10 haneli olmalı ve rakamlardan oluşmalı
    if not value.isdigit() or len(value) != 10:
        raise ValidationError(_('Vergi kimlik numarası 10 haneli olmalı ve sadece rakamlardan oluşmalıdır.'))
    
    # Algoritma doğrulaması
    digits = [int(d) for d in value]
    
    # Son hane kontrolü için
    sum_val = 0
    for i in range(9):
        tmp = (digits[i] + 9 - i) % 10
        sum_val += (tmp * (2 ** (9 - i))) % 9
    
    last_digit = (10 - (sum_val % 10)) % 10
    
    if last_digit != digits[9]:
        raise ValidationError(_('Geçersiz vergi kimlik numarası.'))

def validate_turkish_phone(value):
    """
    Türkiye telefon numarası doğrulama.
    
    Args:
        value (str): Doğrulanacak telefon numarası
        
    Raises:
        ValidationError: Geçersiz telefon numarası
    """
    value = str(value).strip()
    
    # Boşlukları ve tire gibi karakterleri temizle
    value = re.sub(r'[\s\-\(\)]', '', value)
    
    # +90 veya 0 ile başlayan öneki kaldır
    if value.startswith('+90'):
        value = value[3:]
    elif value.startswith('0'):
        value = value[1:]
    
    # 10 haneli olmalı ve rakamlardan oluşmalı
    if not value.isdigit() or len(value) != 10:
        raise ValidationError(_('Telefon numarası 10 haneli olmalı ve sadece rakamlardan oluşmalıdır.'))
    
    # Operatör kodları kontrolü
    operator_codes = ['501', '505', '506', '507', '551', '552', '553', '554', '555', '559',
                     '530', '531', '532', '533', '534', '535', '536', '537', '538', '539',
                     '540', '541', '542', '543', '544', '545', '546', '547', '548', '549',
                     '561', '562', '563', '564', '565', '566', '567', '568', '569',
                     '312', '216', '212', '232', '242', '224', '258', '352', '412']
    
    if value[:3] not in operator_codes:
        raise ValidationError(_('Geçersiz operatör kodu.'))

@deconstructible
class FileExtensionValidator:
    """
    Dosya uzantısı doğrulayıcısı.
    
    Args:
        allowed_extensions (list): İzin verilen uzantılar listesi
        message (str, optional): Hata mesajı
    """
    def __init__(self, allowed_extensions, message=None):
        self.allowed_extensions = allowed_extensions
        self.message = message or _('Dosya uzantısı uygun değil. İzin verilen uzantılar: {extensions}')
    
    def __call__(self, value):
        extension = value.name.split('.')[-1].lower()
        if extension not in self.allowed_extensions:
            raise ValidationError(
                self.message.format(
                    extensions=', '.join(self.allowed_extensions)
                )
            )
    
    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.allowed_extensions == other.allowed_extensions and
            self.message == other.message
        )

def validate_currency_format(value):
    """
    Para birimi formatı doğrulama.
    
    Args:
        value (str): Doğrulanacak para birimi değeri
        
    Raises:
        ValidationError: Geçersiz para birimi formatı
    """
    value = str(value).strip()
    
    # Para birimi sembolünü kaldır
    value = re.sub(r'[₺$€£¥]', '', value)
    # Binlik ayırıcıları kaldır
    value = value.replace('.', '')
    # Virgülü noktaya çevir
    value = value.replace(',', '.')
    
    try:
        # Decimal'a çevrilebilmeli
        decimal_value = Decimal(value)
        
        # Negatif değer kontrolü
        if decimal_value < 0:
            raise ValidationError(_('Para birimi değeri negatif olamaz.'))
    except InvalidOperation:
        raise ValidationError(_('Geçerli bir para birimi formatı giriniz.'))

def validate_no_special_chars(value):
    """
    Özel karakterlerin olmadığını doğrulama.
    
    Args:
        value (str): Doğrulanacak metin
        
    Raises:
        ValidationError: Özel karakter içeren metin
    """
    if not re.match(r'^[a-zA-Z0-9ğüşöçıİĞÜŞÖÇ\s]+$', value):
        raise ValidationError(_('Sadece harf, rakam ve boşluk karakterleri kullanılabilir.'))

def validate_secure_password(value):
    """
    Güçlü şifre doğrulama.
    
    Args:
        value (str): Doğrulanacak şifre
        
    Raises:
        ValidationError: Güçlü olmayan şifre
    """
    if len(value) < 8:
        raise ValidationError(_('Şifre en az 8 karakter olmalıdır.'))
    
    if not re.search(r'[A-Z]', value):
        raise ValidationError(_('Şifre en az bir büyük harf içermelidir.'))
    
    if not re.search(r'[a-z]', value):
        raise ValidationError(_('Şifre en az bir küçük harf içermelidir.'))
    
    if not re.search(r'[0-9]', value):
        raise ValidationError(_('Şifre en az bir rakam içermelidir.'))
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise ValidationError(_('Şifre en az bir özel karakter içermelidir.'))
    
    # Sık kullanılan şifreler
    common_passwords = ['12345678', 'qwerty123', 'password123', '123456789', 'admin123']
    
    if value.lower() in common_passwords:
        raise ValidationError(_('Bu şifre çok yaygın olarak kullanılıyor. Daha güvenli bir şifre seçiniz.')) 