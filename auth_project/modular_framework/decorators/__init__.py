"""
Decorators (Dekoratörler) Modülü

Bu modül, fonksiyonlara ve sınıflara ek davranışlar ekleyen
dekoratör fonksiyonlarını içerir. Önbelleğe alma, kimlik doğrulama,
izleme gibi işlemler için dekoratörler burada tanımlanır.
"""

# Kimlik doğrulama dekoratörleri
from .auth_decorators import (
    ajax_login_required,
    user_has_attribute,
    staff_required,
    permission_required
)

# Önbellek dekoratörleri
from .cache_decorators import (
    simple_cache,
    django_cache,
    method_cache
) 