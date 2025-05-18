"""
Form İşlemleri Yardımcı Fonksiyonları

Bu modül, form işlemleri için yardımcı fonksiyonlar içerir.
"""

from django import forms
from django.utils.text import slugify
from django.utils.html import format_html

def add_css_classes(form, css_classes=None):
    """
    Form alanlarına CSS sınıfları ekler.
    
    Args:
        form: Django Form nesnesi
        css_classes (dict, optional): Alan adı => CSS sınıfı eşleşmesi
            Örn: {'username': 'form-control', 'email': 'form-control email-field'}
            Eğer bir alan adı belirtilmezse, tüm alanlara varsayılan 'form-control' sınıfı eklenir.
    
    Returns:
        form: CSS sınıfları eklenmiş form nesnesi
    """
    if css_classes is None:
        css_classes = {}
    
    for field_name, field in form.fields.items():
        if 'class' not in field.widget.attrs:
            field.widget.attrs['class'] = ''
        
        # Eğer bu alan için özel bir sınıf belirtilmişse, onu kullan
        if field_name in css_classes:
            field.widget.attrs['class'] += ' ' + css_classes[field_name]
        # Aksi halde varsayılan 'form-control' sınıfını ekle
        else:
            field.widget.attrs['class'] += ' form-control'
        
        # Başındaki ve sonundaki boşlukları temizle
        field.widget.attrs['class'] = field.widget.attrs['class'].strip()
    
    return form

def add_placeholders(form, placeholders=None):
    """
    Form alanlarına placeholder metinleri ekler.
    
    Args:
        form: Django Form nesnesi
        placeholders (dict, optional): Alan adı => Placeholder metni eşleşmesi
            Eğer bir alan adı belirtilmezse, alanın etiketi placeholder olarak kullanılır.
    
    Returns:
        form: Placeholder'lar eklenmiş form nesnesi
    """
    if placeholders is None:
        placeholders = {}
    
    for field_name, field in form.fields.items():
        if field_name in placeholders:
            field.widget.attrs['placeholder'] = placeholders[field_name]
        else:
            field.widget.attrs['placeholder'] = field.label or field_name.replace('_', ' ').title()
    
    return form

def add_form_field_icons(form, icons=None):
    """
    Form alanlarına ikon ekler (Bootstrap-style).
    
    Args:
        form: Django Form nesnesi
        icons (dict): Alan adı => İkon sınıfı eşleşmesi
            Örn: {'username': 'fas fa-user', 'email': 'fas fa-envelope'}
    
    Returns:
        form: İkonlar eklenmiş form nesnesi
    """
    if icons is None:
        return form
    
    for field_name, icon_class in icons.items():
        if field_name in form.fields:
            field = form.fields[field_name]
            
            # Orijinal widget'ı sakla
            original_widget = field.widget
            
            # Widget'ı özelleştir
            field.widget = forms.TextInput(attrs=original_widget.attrs)
            field.widget.input_type = getattr(original_widget, 'input_type', 'text')
            
            # Render metodunu özelleştir
            original_render = field.widget.render
            
            def render_with_icon(name, value, attrs=None, renderer=None):
                html = original_render(name, value, attrs, renderer)
                icon_html = format_html('<div class="input-group-prepend"><span class="input-group-text"><i class="{}"></i></span></div>', icon_class)
                return format_html('<div class="input-group">{}{}</div>', icon_html, html)
            
            field.widget.render = render_with_icon
    
    return form

def create_dynamic_form(field_definitions):
    """
    Alan tanımlarına göre dinamik bir form oluşturur.
    
    Args:
        field_definitions (list): Alan tanımları listesi
            Her alan tanımı bir dict olmalı ve şu anahtarları içerebilir:
            - name: Alan adı (zorunlu)
            - field_type: Alan türü (zorunlu, 'CharField', 'IntegerField', vs.)
            - required: Zorunlu mu (isteğe bağlı, varsayılan: True)
            - label: Alan etiketi (isteğe bağlı)
            - initial: Başlangıç değeri (isteğe bağlı)
            - help_text: Yardım metni (isteğe bağlı)
            - widget: Widget sınıfı (isteğe bağlı)
            - validators: Doğrulayıcı listesi (isteğe bağlı)
            - attrs: Widget öznitelikleri (isteğe bağlı)
    
    Returns:
        Form: Oluşturulan dinamik form sınıfı
    """
    form_fields = {}
    
    for field_def in field_definitions:
        field_name = field_def.get('name')
        field_type = field_def.get('field_type')
        
        if not field_name or not field_type:
            continue
        
        # Alan türünü belirle
        field_class = getattr(forms, field_type, forms.CharField)
        
        # Alan parametrelerini hazırla
        field_kwargs = {
            'required': field_def.get('required', True),
        }
        
        if 'label' in field_def:
            field_kwargs['label'] = field_def['label']
        
        if 'initial' in field_def:
            field_kwargs['initial'] = field_def['initial']
        
        if 'help_text' in field_def:
            field_kwargs['help_text'] = field_def['help_text']
        
        if 'validators' in field_def:
            field_kwargs['validators'] = field_def['validators']
        
        # Widget parametrelerini hazırla
        if 'widget' in field_def:
            widget_class = getattr(forms, field_def['widget'], forms.TextInput)
            widget_attrs = field_def.get('attrs', {})
            field_kwargs['widget'] = widget_class(attrs=widget_attrs)
        
        # Alanı oluştur ve ekle
        form_fields[field_name] = field_class(**field_kwargs)
    
    # Dinamik form sınıfını oluştur
    return type('DynamicForm', (forms.Form,), form_fields) 