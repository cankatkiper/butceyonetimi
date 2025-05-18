"""
Tarih İşlemleri Yardımcı Fonksiyonları

Bu modül, tarih ve zaman işlemleri için yardımcı fonksiyonlar içerir.
"""

from datetime import datetime, date, timedelta
from django.utils import timezone

def get_month_start_end(year=None, month=None):
    """
    Belirtilen yıl ve ay için ayın başlangıç ve bitiş tarihlerini döndürür.
    
    Args:
        year (int, optional): Yıl. None ise, şu anki yıl kullanılır.
        month (int, optional): Ay. None ise, şu anki ay kullanılır.
        
    Returns:
        tuple: (başlangıç_tarihi, bitiş_tarihi) - Ayın ilk ve son günü
    """
    today = timezone.now().date()
    
    if year is None:
        year = today.year
    
    if month is None:
        month = today.month
    
    start_of_month = date(year, month, 1)
    
    # Bir sonraki ayın ilk günü
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    
    # Bitiş tarihi, bir sonraki ayın ilk gününden bir gün öncesi
    end_of_month = next_month - timedelta(days=1)
    
    return start_of_month, end_of_month

def get_week_start_end(year=None, week=None):
    """
    Belirtilen yıl ve hafta için haftanın başlangıç ve bitiş tarihlerini döndürür.
    
    Args:
        year (int, optional): Yıl. None ise, şu anki yıl kullanılır.
        week (int, optional): Hafta numarası. None ise, şu anki hafta kullanılır.
        
    Returns:
        tuple: (başlangıç_tarihi, bitiş_tarihi) - Haftanın ilk ve son günü
    """
    today = timezone.now().date()
    
    if year is None:
        year = today.year
    
    if week is None:
        # Yılın gününe göre hafta numarası hesapla
        week = today.isocalendar()[1]
    
    # Yılın ve haftanın ilk günü (Pazartesi)
    first_day_of_week = datetime.strptime(f'{year}-{week}-1', '%Y-%W-%w').date()
    
    # Haftanın son günü (Pazar)
    last_day_of_week = first_day_of_week + timedelta(days=6)
    
    return first_day_of_week, last_day_of_week

def get_date_range(period='monthly', reference_date=None):
    """
    Belirtilen dönem için tarih aralığını döndürür.
    
    Args:
        period (str, optional): Dönem ('daily', 'weekly', 'monthly', 'yearly'). Varsayılan: 'monthly'
        reference_date (date, optional): Referans tarih. None ise, bugün kullanılır.
        
    Returns:
        tuple: (başlangıç_tarihi, bitiş_tarihi) - Dönemin ilk ve son günü
    """
    if reference_date is None:
        reference_date = timezone.now().date()
    
    if period == 'daily':
        # Günlük: Referans tarihin kendisi
        return reference_date, reference_date
    
    elif period == 'weekly':
        # Haftalık: Haftanın başlangıç günü (Pazartesi) ve bitiş günü (Pazar)
        weekday = reference_date.weekday()  # 0: Pazartesi, 6: Pazar
        start_date = reference_date - timedelta(days=weekday)
        end_date = start_date + timedelta(days=6)
        return start_date, end_date
    
    elif period == 'monthly':
        # Aylık: Ayın ilk ve son günü
        year, month = reference_date.year, reference_date.month
        return get_month_start_end(year, month)
    
    elif period == 'yearly':
        # Yıllık: Yılın ilk ve son günü
        year = reference_date.year
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        return start_date, end_date
    
    else:
        # Varsayılan olarak aylık
        year, month = reference_date.year, reference_date.month
        return get_month_start_end(year, month)

def format_date(date_obj, format_str='%d-%m-%Y'):
    """
    Tarih nesnesini belirtilen formatta biçimlendirir.
    
    Args:
        date_obj (date): Biçimlendirilecek tarih nesnesi
        format_str (str, optional): Biçim dizgisi. Varsayılan: '%d-%m-%Y'
        
    Returns:
        str: Biçimlendirilmiş tarih dizgisi
    """
    if date_obj is None:
        return ''
    
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()
    
    return date_obj.strftime(format_str)

def parse_date(date_str, format_str='%d-%m-%Y'):
    """
    Tarih dizgisini tarih nesnesine dönüştürür.
    
    Args:
        date_str (str): Dönüştürülecek tarih dizgisi
        format_str (str, optional): Biçim dizgisi. Varsayılan: '%d-%m-%Y'
        
    Returns:
        date: Dönüştürülmüş tarih nesnesi
    """
    if not date_str:
        return None
    
    try:
        dt = datetime.strptime(date_str, format_str)
        return dt.date()
    except ValueError:
        # Geçersiz tarih formatı
        return None 