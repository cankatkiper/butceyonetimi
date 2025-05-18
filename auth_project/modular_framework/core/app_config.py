"""
Uygulama Yapılandırması

Bu modül, uygulama yapılandırması için kullanılan sınıfları içerir.
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
        from ..core import signals 