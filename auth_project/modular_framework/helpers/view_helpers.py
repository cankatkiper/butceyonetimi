"""
View İşlemleri Yardımcı Fonksiyonları

Bu modül, view işlemleri için yardımcı fonksiyonlar içerir.
"""

from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.utils.text import slugify
import json

def render_with_messages(request, template_name, context=None, message=None, level=None):
    """
    Mesaj ekleyerek şablon render eder.
    
    Args:
        request: HTTP isteği
        template_name (str): Şablon adı
        context (dict, optional): Şablon bağlamı
        message (str, optional): Eklenecek mesaj
        level (str, optional): Mesaj seviyesi ('success', 'info', 'warning', 'error')
    
    Returns:
        HttpResponse: Render edilmiş şablon yanıtı
    """
    if context is None:
        context = {}
    
    if message:
        if level == 'success':
            messages.success(request, message)
        elif level == 'info':
            messages.info(request, message)
        elif level == 'warning':
            messages.warning(request, message)
        elif level == 'error':
            messages.error(request, message)
        else:
            messages.info(request, message)
    
    return render(request, template_name, context)

def handle_form_submission(request, form_class, template_name, 
                          success_url=None, success_message=None, 
                          context=None, form_kwargs=None, 
                          initial=None, redirect_params=None):
    """
    Form gönderimi işleme yardımcısı.
    
    Args:
        request: HTTP isteği
        form_class: Form sınıfı
        template_name (str): Şablon adı
        success_url (str, optional): Başarılı yönlendirme URL'si
        success_message (str, optional): Başarı mesajı
        context (dict, optional): Ek şablon bağlamı
        form_kwargs (dict, optional): Form için ek keyword argümanları
        initial (dict, optional): Form için başlangıç değerleri
        redirect_params (dict, optional): Başarılı yönlendirme için URL parametreleri
    
    Returns:
        HttpResponse: Render edilmiş şablon veya yönlendirme yanıtı
    """
    if context is None:
        context = {}
    
    if form_kwargs is None:
        form_kwargs = {}
    
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, **form_kwargs)
        if form.is_valid():
            form_instance = form.save() if hasattr(form, 'save') else None
            
            if success_message:
                messages.success(request, success_message)
            
            if success_url:
                if redirect_params and isinstance(redirect_params, dict):
                    return redirect(reverse(success_url, kwargs=redirect_params))
                return redirect(success_url)
            
            return form_instance
    else:
        if initial:
            form = form_class(initial=initial, **form_kwargs)
        else:
            form = form_class(**form_kwargs)
    
    context['form'] = form
    return render(request, template_name, context)

def ajax_response(data=None, status='success', message=None, status_code=200):
    """
    AJAX yanıtı oluşturur.
    
    Args:
        data: Yanıt verisi
        status (str, optional): Durum ('success', 'error', 'warning', 'info')
        message (str, optional): Mesaj
        status_code (int, optional): HTTP durum kodu
    
    Returns:
        JsonResponse: JSON yanıtı
    """
    response_data = {
        'status': status
    }
    
    if data is not None:
        response_data['data'] = data
    
    if message:
        response_data['message'] = message
    
    return JsonResponse(response_data, status=status_code)

def paginate_items(items, page_number, items_per_page=10, max_pages=5):
    """
    Öğeleri sayfalandırır.
    
    Args:
        items: Sayfalandırılacak öğeler
        page_number (int): Sayfa numarası
        items_per_page (int, optional): Sayfa başına öğe sayısı
        max_pages (int, optional): Sayfalandırma üzerinde görünecek maksimum sayfa sayısı
    
    Returns:
        dict: Sayfalandırma bilgisi
    """
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    paginator = Paginator(items, items_per_page)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
        page_number = 1
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
        page_number = paginator.num_pages
    
    page_number = int(page_number)
    
    # Sayfalandırma aralığını hesapla
    if paginator.num_pages <= max_pages:
        # 5 veya daha az sayfa varsa hepsini göster
        page_range = range(1, paginator.num_pages + 1)
    else:
        # 5'ten fazla sayfa varsa navigasyon sistemini iyileştir
        if page_number <= 3:
            # Başlangıç sayfalarındaysa ilk 5 sayfayı göster
            page_range = range(1, max_pages + 1)
        elif page_number >= paginator.num_pages - 2:
            # Son sayfalardaysa son 5 sayfayı göster
            page_range = range(paginator.num_pages - max_pages + 1, paginator.num_pages + 1)
        else:
            # Ortadaysa, mevcut sayfayı ortaya alarak 5 sayfa göster
            page_range = range(page_number - 2, page_number + 3)
    
    return {
        'page_obj': page_obj,
        'page_range': page_range,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'current_page': page_number,
        'paginator': paginator,
        'is_paginated': paginator.num_pages > 1
    } 