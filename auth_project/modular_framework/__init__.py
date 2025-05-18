"""
Modular Framework - Yeniden kullanılabilir modüler bileşenler çerçevesi

Bu çerçeve, farklı Django projelerinde yeniden kullanılabilecek
modüler ve bağımsız bileşenler sunar. Her modül, kendi amacına
uygun şekilde organize edilmiştir.

Modüller:
- core: Temel sınıflar ve yapılar
- utils: Yardımcı işlevler ve araçlar
- mixins: Yeniden kullanılabilir mixin sınıfları
- abstract_models: Soyut model sınıfları
- helpers: Yardımcı fonksiyonlar ve sınıflar
- services: Servis sınıfları
- decorators: Yeniden kullanılabilir decorator fonksiyonları
- validators: Doğrulama işlevleri ve sınıfları
"""

# Django AppConfig tanımlaması
default_app_config = 'modular_framework.apps.ModularFrameworkConfig'

# Core modülünü içe aktar
from . import core

# Utils modülünü içe aktar
from . import utils

# Mixins modülünü içe aktar
from . import mixins

# Abstract Models modülünü içe aktar
from . import abstract_models

# Helpers modülünü içe aktar
from . import helpers

# Services modülünü içe aktar
from . import services

# Decorators modülünü içe aktar
from . import decorators

# Validators modülünü içe aktar
from . import validators

__version__ = '0.1.0' 