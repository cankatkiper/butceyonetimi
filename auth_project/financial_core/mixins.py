from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.db.models import ForeignKey

class TransactionCreateMixin:
    """İşlem oluşturma için yeniden kullanılabilir mixin"""
    def form_valid(self, form):
        # Yeni kategori kontrolü
        new_category_name = form.cleaned_data.get('new_category')
        category = form.cleaned_data.get('category')
        
        # İlgili kategori modelini bul
        for field in self.model._meta.fields:
            if isinstance(field, ForeignKey) and field.name == 'category':
                category_model = field.related_model
                break
        else:
            raise ValueError("Bu model bir 'category' foreign key alanına sahip değil.")
        
        # Yeni kategori girilmiş mi kontrol et
        if new_category_name:
            # Yeni kategori oluştur
            category, created = category_model.objects.get_or_create(
                name=new_category_name,
                type=self.transaction_type,
                icon='tag'  # Varsayılan ikon
            )
            transaction = form.save(commit=False)
            transaction.category = category
        elif category:
            # Mevcut kategori seçilmiş
            transaction = form.save(commit=False)
        else:
            # Hiçbir kategori seçilmemiş ve girilmemiş
            messages.error(self.request, 'Lütfen bir kategori seçin veya yeni bir kategori girin.')
            return self.form_invalid(form)
        
        transaction.user = self.request.user
        transaction.save()
        
        # Kullanıcı toplam miktarını güncelle
        self.update_user_total(transaction)
        
        # İşlem türüne göre başarı mesajı
        if self.transaction_type == 'gelir':
            messages.success(self.request, 'Gelir başarıyla kaydedildi.')
        else:
            messages.success(self.request, 'Gider başarıyla kaydedildi.')
            
            # Harcama limitlerini kontrol et (sadece gider işlemlerinde)
            self.check_spending_limits(transaction)
            
        return redirect(self.success_url)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['transaction_type'] = self.transaction_type
        return kwargs
    
    def update_user_total(self, transaction):
        """Kullanıcının toplam tutarını güncelle (somut sınıflarda uygulanmalı)"""
        raise NotImplementedError("Bu metod somut alt sınıfta uygulanmalıdır")
    
    def check_spending_limits(self, transaction):
        """Harcama limitlerini kontrol et (sadece gider işlemlerinde)"""
        pass  # Alt sınıflar uygulamalı

class TransactionUpdateMixin:
    """İşlem güncelleme için yeniden kullanılabilir mixin"""
    def form_valid(self, form):
        # Önceki işlem bilgilerini al
        old_transaction = self.get_object()
        old_amount = old_transaction.amount
        
        # Yeni kategori kontrolü
        new_category_name = form.cleaned_data.get('new_category')
        category = form.cleaned_data.get('category')
        
        # İlgili kategori modelini bul
        for field in self.model._meta.fields:
            if isinstance(field, ForeignKey) and field.name == 'category':
                category_model = field.related_model
                break
        else:
            raise ValueError("Bu model bir 'category' foreign key alanına sahip değil.")
        
        # Yeni kategori girilmiş mi kontrol et
        if new_category_name:
            # Yeni kategori oluştur
            category, created = category_model.objects.get_or_create(
                name=new_category_name,
                type=self.transaction_type,
                icon='tag'  # Varsayılan ikon
            )
            transaction = form.save(commit=False)
            transaction.category = category
        elif category:
            # Mevcut kategori seçilmiş
            transaction = form.save(commit=False)
        else:
            # Hiçbir kategori seçilmemiş ve girilmemiş
            messages.error(self.request, 'Lütfen bir kategori seçin veya yeni bir kategori girin.')
            return self.form_invalid(form)
        
        # Kullanıcı toplam miktarını güncelle
        self.update_user_total(transaction, old_amount)
        
        transaction.save()
        
        messages.success(self.request, 'İşlem başarıyla güncellendi.')
        return redirect(self.success_url)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['transaction_type'] = self.transaction_type
        return kwargs
    
    def update_user_total(self, transaction, old_amount):
        """Kullanıcının toplam tutarını güncelle (somut sınıflarda uygulanmalı)"""
        raise NotImplementedError("Bu metod somut alt sınıfta uygulanmalıdır")

class TransactionDeleteMixin:
    """İşlem silme için yeniden kullanılabilir mixin"""
    def post(self, request, *args, **kwargs):
        transaction_id = request.POST.get('transaction_id')
        transaction = get_object_or_404(self.model, id=transaction_id, user=request.user)
        
        # Kullanıcı toplam miktarını güncelle
        self.update_user_total(transaction)
        
        transaction.delete()
        messages.success(request, 'İşlem başarıyla silindi.')
        
        # AJAX isteği ise JSON yanıtı döndür
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        
        return redirect(self.success_url)
    
    def update_user_total(self, transaction):
        """Kullanıcının toplam tutarını güncelle (somut sınıflarda uygulanmalı)"""
        raise NotImplementedError("Bu metod somut alt sınıfta uygulanmalıdır")

class LimitCreateUpdateMixin:
    """Limit oluşturma/güncelleme için mixin"""
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
    """Limit silme için mixin"""
    def post(self, request, *args, **kwargs):
        limit_id = request.POST.get('limit_id')
        limit = get_object_or_404(self.model, id=limit_id, user=request.user)
        limit.delete()
        
        messages.success(request, 'Harcama limiti başarıyla silindi.')
        
        # AJAX isteği ise JSON yanıtı döndür
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        
        return redirect(self.success_url) 