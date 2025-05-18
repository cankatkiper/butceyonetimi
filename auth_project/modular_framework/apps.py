"""
Django AppConfig for Modular Framework
"""

from django.apps import AppConfig

class ModularFrameworkConfig(AppConfig):
    """
    Modular Framework için Django AppConfig sınıfı.
    """
    name = 'modular_framework'
    verbose_name = 'Modüler Çerçeve'
    
    def ready(self):
        """
        Uygulama hazır olduğunda çalıştırılacak kod.
        Sinyal yöneticilerini kaydetmek ve başlangıç işlemlerini yapmak için kullanılır.
        """
        # Sinyalleri içe aktar
        # İleride gerekirse sinyal kayıtlarını burada yapabiliriz
        pass 