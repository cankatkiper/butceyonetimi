"""
Kimlik Doğrulama İşlemleri için Dekoratörler

Bu modül, kimlik doğrulama ve yetkilendirme için
kullanılabilecek dekoratörler içerir.
"""

from functools import wraps
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse

def ajax_login_required(view_func):
    """
    AJAX istekleri için giriş gerekli dekoratörü.
    
    Normal istekler için oturum açma sayfasına yönlendirirken,
    AJAX istekleri için 403 JSON yanıtı döndürür.
    
    Args:
        view_func: Dekore edilecek view fonksiyonu
        
    Returns:
        function: Dekore edilmiş view fonksiyonu
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        
        # AJAX isteği ise 403 hata kodu ile yanıt ver
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': 'Yetkilendirme hatası. Lütfen giriş yapın.',
                'login_required': True
            }, status=403)
        
        # Normal istek ise login sayfasına yönlendir
        login_url = reverse('login')
        return redirect(f"{login_url}?next={request.path}")
    
    return wrapper

def user_has_attribute(attribute_name, attribute_value=None, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Kullanıcının belirli bir özniteliğe sahip olmasını kontrol eden dekoratör oluşturur.
    
    Args:
        attribute_name (str): Kontrol edilecek öznitelik adı
        attribute_value: Beklenen öznitelik değeri (None ise, sadece özniteliğin varlığı kontrol edilir)
        login_url (str, optional): Giriş yapılmamışsa yönlendirilecek URL
        redirect_field_name (str, optional): Yönlendirme alanı adı
        
    Returns:
        function: Dekoratör fonksiyonu
    """
    def check_attribute(user):
        # Kullanıcı oturum açmış mı?
        if not user.is_authenticated:
            return False
        
        # Kullanıcı özniteliğe sahip mi?
        if not hasattr(user, attribute_name):
            return False
        
        # Belirli bir değer bekleniyor mu?
        if attribute_value is not None:
            return getattr(user, attribute_name) == attribute_value
        
        return True
    
    return user_passes_test(check_attribute, login_url=login_url, redirect_field_name=redirect_field_name)

def staff_required(view_func=None, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Staff yetkisi gerektiren dekoratör.
    
    Args:
        view_func: Dekore edilecek view fonksiyonu
        login_url (str, optional): Giriş yapılmamışsa yönlendirilecek URL
        redirect_field_name (str, optional): Yönlendirme alanı adı
        
    Returns:
        function: Dekore edilmiş view fonksiyonu
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_staff,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator

def permission_required(perm, raise_exception=False):
    """
    Belirli bir izin gerektiren dekoratör.
    
    Args:
        perm (str): Gerekli izin adı
        raise_exception (bool, optional): İzin yoksa hata fırlatılsın mı?
        
    Returns:
        function: Dekoratör fonksiyonu
    """
    def check_perms(user):
        if isinstance(perm, str):
            perms = (perm,)
        else:
            perms = perm
            
        if user.has_perms(perms):
            return True
        
        if raise_exception:
            raise HttpResponseForbidden("Bu işlemi yapmak için yetkiniz bulunmuyor.")
        
        return False
    
    return user_passes_test(check_perms) 