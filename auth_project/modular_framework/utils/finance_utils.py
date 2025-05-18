"""
Finansal İşlemler Yardımcı Fonksiyonları

Bu modül, finansal hesaplamalar ve para birimi işlemleri için
yardımcı fonksiyonlar içerir.
"""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

def format_currency(amount, decimal_places=2, currency_symbol='₺', position='suffix'):
    """
    Para miktarını biçimlendirir.
    
    Args:
        amount (Decimal or float or str): Para miktarı
        decimal_places (int, optional): Ondalık basamak sayısı. Varsayılan: 2
        currency_symbol (str, optional): Para birimi sembolü. Varsayılan: ₺
        position (str, optional): Sembol konumu ('prefix' veya 'suffix'). Varsayılan: 'suffix'
        
    Returns:
        str: Biçimlendirilmiş para miktarı
    """
    try:
        # Decimal'a çevir (eğer değilse)
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        
        # Belirtilen ondalık basamağa yuvarla
        amount = amount.quantize(Decimal('0.1') ** decimal_places, rounding=ROUND_HALF_UP)
        
        # Sayıyı formatlı metne çevir
        formatted = f"{amount:,.{decimal_places}f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        # Para birimi sembolünü ekle
        if position == 'prefix':
            return f"{currency_symbol}{formatted}"
        else:  # suffix
            return f"{formatted} {currency_symbol}"
    except (InvalidOperation, ValueError, TypeError):
        return f"0,00 {currency_symbol}" if position == 'suffix' else f"{currency_symbol}0,00"

def parse_currency(amount_str, decimal_separator=','):
    """
    Para miktarı metnini parse ederek Decimal nesnesine çevirir.
    
    Args:
        amount_str (str): Para miktarı metni (örn: "1.234,56")
        decimal_separator (str, optional): Ondalık ayırıcı. Varsayılan: ','
        
    Returns:
        Decimal: Para miktarı
    """
    try:
        # Rakam olmayan karakterleri temizle
        cleaned = ''.join(c for c in amount_str if c.isdigit() or c in ['.', ','])
        
        # Binlik ayırıcı ve ondalık ayırıcıyı standartlaştır
        if decimal_separator == ',':
            # Önce noktaları kaldır (binlik ayırıcı), sonra virgülü noktaya çevir (ondalık ayırıcı)
            cleaned = cleaned.replace('.', '').replace(',', '.')
        # Decimal nesnesi oluştur
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return Decimal('0')

def calculate_percentage(part, total):
    """
    İki sayı arasındaki yüzdelik oranı hesaplar.
    
    Args:
        part (Decimal or float): Parça değeri
        total (Decimal or float): Toplam değer
        
    Returns:
        float: Yüzdelik oran (0-100 arasında)
    """
    try:
        if not isinstance(part, Decimal):
            part = Decimal(str(part))
        if not isinstance(total, Decimal):
            total = Decimal(str(total))
        
        if total == 0:
            return 0
        
        return float((part / total) * 100)
    except (InvalidOperation, ValueError, TypeError, ZeroDivisionError):
        return 0

def calculate_vat(amount, rate=18):
    """
    KDV hesaplar.
    
    Args:
        amount (Decimal or float): KDV'siz miktar
        rate (int or float, optional): KDV oranı. Varsayılan: 18
        
    Returns:
        tuple: (kdv_tutarı, toplam_tutar)
    """
    try:
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        
        rate_decimal = Decimal(str(rate)) / 100
        vat_amount = amount * rate_decimal
        total_amount = amount + vat_amount
        
        return vat_amount, total_amount
    except (InvalidOperation, ValueError, TypeError):
        return Decimal('0'), Decimal('0')

def extract_vat(total_amount, rate=18):
    """
    Toplam tutardan KDV'yi ayırır.
    
    Args:
        total_amount (Decimal or float): KDV dahil toplam tutar
        rate (int or float, optional): KDV oranı. Varsayılan: 18
        
    Returns:
        tuple: (kdvsiz_tutar, kdv_tutarı)
    """
    try:
        if not isinstance(total_amount, Decimal):
            total_amount = Decimal(str(total_amount))
        
        rate_decimal = Decimal(str(rate)) / 100
        net_amount = total_amount / (1 + rate_decimal)
        vat_amount = total_amount - net_amount
        
        return net_amount, vat_amount
    except (InvalidOperation, ValueError, TypeError):
        return Decimal('0'), Decimal('0') 