"""
Limitler (Limits) için Mixin Sınıfları

Bu modül, harcama limiti oluşturma, güncelleme ve silme gibi
işlemler için yeniden kullanılabilir mixin sınıflarını içerir.
"""

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect

class LimitCreateUpdateMixin:
    """
    Limit oluşturma/güncelleme için mixin
    
    View sınıflarına harcama limiti oluşturma ve güncelleme
    işlevselliği ekler.
    """
    def form_valid(self, form):
        limit = form.save(commit=False)
        limit.user = self.request.user
        limit.save()
        
        messages.success(self.request, 'Harcama limiti başarıyla kaydedildi.')
        return redirect(self.success_url)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class LimitDeleteMixin:
    """
    Limit silme için mixin
    
    View sınıflarına harcama limiti silme işlevselliği ekler.
    """
    def post(self, request, *args, **kwargs):
        limit_id = request.POST.get('limit_id')
        limit = get_object_or_404(self.model, id=limit_id, user=request.user)
        limit.delete()
        
        messages.success(request, 'Harcama limiti başarıyla silindi.')
        
        # AJAX isteği ise JSON yanıtı döndür
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        
        return redirect(self.success_url) 