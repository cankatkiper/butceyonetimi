"""
Önbelleğe Alma İşlemleri için Dekoratörler

Bu modül, fonksiyonların ve metodların sonuçlarını önbelleğe almak için
kullanılabilecek dekoratörler içerir.
"""

import time
import hashlib
import pickle
import functools
from datetime import datetime, timedelta

# Basit önbellek yöneticisi
_memory_cache = {}

def simple_cache(timeout=300):
    """
    Basit bir bellek içi önbellek dekoratörü.
    
    Args:
        timeout (int, optional): Önbellek süresi (saniye). Varsayılan: 300
        
    Returns:
        function: Dekoratör fonksiyonu
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Anahtar oluştur
            key_parts = [func.__name__]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            cache_key = "".join(key_parts)
            
            # MD5 hash oluştur (uzun anahtarlar için)
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()
            
            # Önbellekte var mı kontrol et
            current_time = time.time()
            if cache_key in _memory_cache:
                result, expiry_time = _memory_cache[cache_key]
                if expiry_time > current_time:
                    return result
            
            # Fonksiyonu çağır ve sonucu önbelleğe al
            result = func(*args, **kwargs)
            expiry_time = current_time + timeout
            _memory_cache[cache_key] = (result, expiry_time)
            
            # Eski önbellek girdilerini temizle
            for key in list(_memory_cache.keys()):
                if _memory_cache[key][1] < current_time:
                    del _memory_cache[key]
            
            return result
        
        # Önbelleği temizleme metodu ekle
        def clear_cache():
            nonlocal _memory_cache
            for key in list(_memory_cache.keys()):
                if key.startswith(hashlib.md5(func.__name__.encode()).hexdigest()[:8]):
                    del _memory_cache[key]
        
        wrapper.clear_cache = clear_cache
        return wrapper
    
    return decorator

def django_cache(timeout=300, key_prefix=''):
    """
    Django'nun önbellek çerçevesini kullanan bir önbellek dekoratörü.
    
    Args:
        timeout (int, optional): Önbellek süresi (saniye). Varsayılan: 300
        key_prefix (str, optional): Önbellek anahtarı öneki
        
    Returns:
        function: Dekoratör fonksiyonu
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from django.core.cache import cache
            
            # Anahtar oluştur
            key_parts = [key_prefix or func.__name__]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            cache_key = ":".join(key_parts)
            
            # MD5 hash oluştur (uzun anahtarlar için)
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()
            
            # Önbellekte var mı kontrol et
            result = cache.get(cache_key)
            if result is not None:
                return pickle.loads(result)
            
            # Fonksiyonu çağır ve sonucu önbelleğe al
            result = func(*args, **kwargs)
            cache.set(cache_key, pickle.dumps(result), timeout)
            
            return result
        
        # Önbelleği temizleme metodu ekle
        def clear_cache():
            from django.core.cache import cache
            cache_key_prefix = hashlib.md5((key_prefix or func.__name__).encode()).hexdigest()[:8]
            
            # Not: Django'nun önbellek API'si tüm anahtarları aramayı desteklemez
            # Bu yüzden sadece önbelleği tamamen temizleyebiliriz
            cache.clear()
        
        wrapper.clear_cache = clear_cache
        return wrapper
    
    return decorator

def method_cache(timeout=300):
    """
    Sınıf metodları için önbellek dekoratörü.
    self parametresini dikkate alır.
    
    Args:
        timeout (int, optional): Önbellek süresi (saniye). Varsayılan: 300
        
    Returns:
        function: Dekoratör fonksiyonu
    """
    def decorator(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            # Anahtar oluştur (self'i dahil etme)
            key_parts = [method.__name__, str(id(self))]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            cache_key = "".join(key_parts)
            
            # MD5 hash oluştur
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()
            
            # Önbellekte var mı kontrol et
            current_time = time.time()
            if cache_key in _memory_cache:
                result, expiry_time = _memory_cache[cache_key]
                if expiry_time > current_time:
                    return result
            
            # Metodu çağır ve sonucu önbelleğe al
            result = method(self, *args, **kwargs)
            expiry_time = current_time + timeout
            _memory_cache[cache_key] = (result, expiry_time)
            
            # Eski önbellek girdilerini temizle
            for key in list(_memory_cache.keys()):
                if _memory_cache[key][1] < current_time:
                    del _memory_cache[key]
            
            return result
        
        return wrapper
    
    return decorator 