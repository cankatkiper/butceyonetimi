"""
API Servisi

Bu modül, harici API'lerle iletişim kurmak için kullanılabilecek
servis sınıflarını içerir.
"""

import requests
import json
import logging
from functools import wraps
from urllib.parse import urlencode
from django.conf import settings
from ..decorators.cache_decorators import simple_cache

logger = logging.getLogger(__name__)

def handle_api_errors(func):
    """
    API hatalarını yakalayan dekoratör.
    
    Args:
        func: Dekore edilecek fonksiyon
        
    Returns:
        function: Dekore edilmiş fonksiyon
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.ConnectionError:
            logger.error(f"API bağlantı hatası: {func.__name__}")
            return {'error': 'API sunucusuna bağlanılamıyor.'}
        except requests.exceptions.Timeout:
            logger.error(f"API zaman aşımı: {func.__name__}")
            return {'error': 'API isteği zaman aşımına uğradı.'}
        except requests.exceptions.RequestException as e:
            logger.error(f"API istek hatası: {func.__name__} - {str(e)}")
            return {'error': f'API istek hatası: {str(e)}'}
        except json.JSONDecodeError:
            logger.error(f"API JSON ayrıştırma hatası: {func.__name__}")
            return {'error': 'API yanıtı geçerli bir JSON formatında değil.'}
        except Exception as e:
            logger.error(f"API bilinmeyen hata: {func.__name__} - {str(e)}")
            return {'error': f'API hatası: {str(e)}'}
    
    return wrapper

class BaseAPIService:
    """
    Temel API Servisi sınıfı.
    
    Bu sınıf, harici API'lerle iletişim kurmak için temel işlevleri sağlar.
    
    Args:
        base_url (str): API'nin temel URL'si
        api_key (str, optional): API anahtarı
        timeout (int, optional): İstek zaman aşımı (saniye)
    """
    def __init__(self, base_url, api_key=None, timeout=30):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        
        # API anahtarı varsa, oturum için varsayılan header'ları ayarla
        if self.api_key:
            self.session.headers.update({'Authorization': f'Bearer {self.api_key}'})
    
    @handle_api_errors
    def get(self, endpoint, params=None, headers=None):
        """
        GET isteği gönderir.
        
        Args:
            endpoint (str): API uç noktası
            params (dict, optional): Sorgu parametreleri
            headers (dict, optional): İstek başlıkları
            
        Returns:
            dict: API yanıtı
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    @handle_api_errors
    def post(self, endpoint, data=None, json_data=None, headers=None):
        """
        POST isteği gönderir.
        
        Args:
            endpoint (str): API uç noktası
            data (dict, optional): Form verileri
            json_data (dict, optional): JSON verileri
            headers (dict, optional): İstek başlıkları
            
        Returns:
            dict: API yanıtı
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.post(url, data=data, json=json_data, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    @handle_api_errors
    def put(self, endpoint, data=None, json_data=None, headers=None):
        """
        PUT isteği gönderir.
        
        Args:
            endpoint (str): API uç noktası
            data (dict, optional): Form verileri
            json_data (dict, optional): JSON verileri
            headers (dict, optional): İstek başlıkları
            
        Returns:
            dict: API yanıtı
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.put(url, data=data, json=json_data, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    @handle_api_errors
    def delete(self, endpoint, headers=None):
        """
        DELETE isteği gönderir.
        
        Args:
            endpoint (str): API uç noktası
            headers (dict, optional): İstek başlıkları
            
        Returns:
            dict: API yanıtı
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.delete(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def build_url(self, endpoint, params=None):
        """
        API URL'si oluşturur.
        
        Args:
            endpoint (str): API uç noktası
            params (dict, optional): Sorgu parametreleri
            
        Returns:
            str: Oluşturulan URL
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        if params:
            url = f"{url}?{urlencode(params)}"
        
        return url
    
    def close(self):
        """Oturumu kapatır."""
        self.session.close()

class ExchangeRateService(BaseAPIService):
    """
    Döviz kurları için API servisi.
    
    Args:
        api_key (str, optional): API anahtarı
    """
    def __init__(self, api_key=None):
        # Ayarlardan API anahtarını al
        if not api_key and hasattr(settings, 'EXCHANGE_RATE_API_KEY'):
            api_key = settings.EXCHANGE_RATE_API_KEY
        
        super().__init__('https://api.exchangerate-api.com/v4', api_key)
    
    @simple_cache(timeout=3600)  # 1 saat önbelleğe al
    def get_latest_rates(self, base_currency='USD'):
        """
        En son döviz kurlarını alır.
        
        Args:
            base_currency (str, optional): Temel para birimi. Varsayılan: 'USD'
            
        Returns:
            dict: Döviz kurları
        """
        endpoint = f'latest/{base_currency}'
        return self.get(endpoint)
    
    @simple_cache(timeout=86400)  # 24 saat önbelleğe al
    def convert_currency(self, from_currency, to_currency, amount):
        """
        Para birimi dönüşümü yapar.
        
        Args:
            from_currency (str): Kaynak para birimi
            to_currency (str): Hedef para birimi
            amount (float): Miktar
            
        Returns:
            float: Dönüştürülmüş miktar
        """
        rates = self.get_latest_rates(from_currency)
        
        if 'error' in rates:
            return rates
        
        if to_currency not in rates.get('rates', {}):
            return {'error': f"Para birimi bulunamadı: {to_currency}"}
        
        rate = rates['rates'][to_currency]
        converted_amount = float(amount) * rate
        
        return {
            'from': from_currency,
            'to': to_currency,
            'amount': float(amount),
            'rate': rate,
            'converted_amount': round(converted_amount, 2),
            'date': rates.get('date')
        }

class WeatherService(BaseAPIService):
    """
    Hava durumu için API servisi.
    
    Args:
        api_key (str, optional): API anahtarı
    """
    def __init__(self, api_key=None):
        # Ayarlardan API anahtarını al
        if not api_key and hasattr(settings, 'WEATHER_API_KEY'):
            api_key = settings.WEATHER_API_KEY
        
        super().__init__('https://api.openweathermap.org/data/2.5', api_key)
    
    @simple_cache(timeout=1800)  # 30 dakika önbelleğe al
    def get_current_weather(self, city, units='metric', lang='tr'):
        """
        Mevcut hava durumunu alır.
        
        Args:
            city (str): Şehir adı
            units (str, optional): Birim sistemi ('metric', 'imperial'). Varsayılan: 'metric'
            lang (str, optional): Dil kodu. Varsayılan: 'tr'
            
        Returns:
            dict: Hava durumu bilgileri
        """
        params = {
            'q': city,
            'units': units,
            'lang': lang,
            'appid': self.api_key
        }
        
        return self.get('weather', params=params)
    
    @simple_cache(timeout=3600)  # 1 saat önbelleğe al
    def get_forecast(self, city, days=5, units='metric', lang='tr'):
        """
        Hava durumu tahminini alır.
        
        Args:
            city (str): Şehir adı
            days (int, optional): Gün sayısı (max 7). Varsayılan: 5
            units (str, optional): Birim sistemi ('metric', 'imperial'). Varsayılan: 'metric'
            lang (str, optional): Dil kodu. Varsayılan: 'tr'
            
        Returns:
            dict: Hava durumu tahmini
        """
        params = {
            'q': city,
            'cnt': min(days, 7) * 8,  # 3 saatlik periyotlar (günde 8 periyot)
            'units': units,
            'lang': lang,
            'appid': self.api_key
        }
        
        return self.get('forecast', params=params) 