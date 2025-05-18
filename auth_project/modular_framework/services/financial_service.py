"""
Finansal Servis

Bu modül, finansal hesaplamalar ve işlemler için
servis sınıfları içerir.
"""

from decimal import Decimal, ROUND_HALF_UP
import datetime
from django.db.models import Sum, Avg, Count, Max, Min
from django.utils import timezone
from ..utils.date_utils import get_date_range

class FinancialCalculator:
    """
    Finansal hesaplamalar için yardımcı sınıf.
    """
    
    @staticmethod
    def calculate_compound_interest(principal, rate, time, compounds_per_year=1):
        """
        Bileşik faiz hesaplar.
        
        Args:
            principal (Decimal): Ana para
            rate (Decimal): Yıllık faiz oranı (örn. 0.05 = %5)
            time (int): Yıl sayısı
            compounds_per_year (int, optional): Yıllık birleştirme sayısı. Varsayılan: 1
            
        Returns:
            Decimal: Toplam miktar
        """
        # Decimal'a çevir
        principal = Decimal(str(principal))
        rate = Decimal(str(rate))
        time = Decimal(str(time))
        compounds_per_year = Decimal(str(compounds_per_year))
        
        # Bileşik faiz formülü: A = P(1 + r/n)^(nt)
        exponent = time * compounds_per_year
        base = Decimal('1') + (rate / compounds_per_year)
        
        # Üs hesaplama
        amount = principal * (base ** exponent)
        
        # 2 ondalık basamağa yuvarla
        return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_loan_payment(principal, rate, time):
        """
        Aylık kredi ödemesi hesaplar.
        
        Args:
            principal (Decimal): Kredi tutarı
            rate (Decimal): Yıllık faiz oranı (örn. 0.05 = %5)
            time (int): Ay sayısı
            
        Returns:
            Decimal: Aylık ödeme tutarı
        """
        # Decimal'a çevir
        principal = Decimal(str(principal))
        rate = Decimal(str(rate)) / 12  # Aylık faiz oranı
        time = Decimal(str(time))
        
        # Aylık ödeme formülü: P * r * (1 + r)^n / ((1 + r)^n - 1)
        if rate == 0:
            # Faizsiz kredi
            return principal / time
        
        numerator = rate * ((1 + rate) ** time)
        denominator = ((1 + rate) ** time) - 1
        
        payment = principal * (numerator / denominator)
        
        # 2 ondalık basamağa yuvarla
        return payment.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_mortgage_payment(principal, rate, time, payment_frequency='monthly'):
        """
        İpotek ödemesi hesaplar.
        
        Args:
            principal (Decimal): İpotek tutarı
            rate (Decimal): Yıllık faiz oranı (örn. 0.05 = %5)
            time (int): Yıl sayısı
            payment_frequency (str, optional): Ödeme sıklığı (örn. 'monthly', 'biweekly'). Varsayılan: 'monthly'
            
        Returns:
            Decimal: Periyodik ödeme tutarı
        """
        # Decimal'a çevir
        principal = Decimal(str(principal))
        rate = Decimal(str(rate))
        time = Decimal(str(time))
        
        # Ödeme sıklığına göre ayarlamalar yap
        if payment_frequency == 'monthly':
            payments_per_year = Decimal('12')
        elif payment_frequency == 'biweekly':
            payments_per_year = Decimal('26')
        elif payment_frequency == 'weekly':
            payments_per_year = Decimal('52')
        else:
            payments_per_year = Decimal('12')  # Varsayılan olarak aylık
        
        # Toplam ödeme sayısı
        total_payments = time * payments_per_year
        
        # Periyodik faiz oranı
        periodic_rate = rate / payments_per_year
        
        # Ödeme formülü: P * r * (1 + r)^n / ((1 + r)^n - 1)
        if periodic_rate == 0:
            # Faizsiz kredi
            return principal / total_payments
        
        numerator = periodic_rate * ((1 + periodic_rate) ** total_payments)
        denominator = ((1 + periodic_rate) ** total_payments) - 1
        
        payment = principal * (numerator / denominator)
        
        # 2 ondalık basamağa yuvarla
        return payment.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_investment_growth(initial_investment, monthly_contribution, rate, time):
        """
        Yatırım büyümesini hesaplar.
        
        Args:
            initial_investment (Decimal): Başlangıç yatırımı
            monthly_contribution (Decimal): Aylık katkı
            rate (Decimal): Yıllık getiri oranı (örn. 0.08 = %8)
            time (int): Yıl sayısı
            
        Returns:
            dict: Yatırım sonuçları
        """
        # Decimal'a çevir
        initial_investment = Decimal(str(initial_investment))
        monthly_contribution = Decimal(str(monthly_contribution))
        rate = Decimal(str(rate))
        time = int(time)
        
        # Aylık getiri oranı
        monthly_rate = rate / 12
        
        # Sonuç listesi
        results = []
        
        # Toplam yatırım ve toplam getiri
        total_investment = initial_investment
        total_growth = Decimal('0')
        
        # Mevcut değer
        current_value = initial_investment
        
        # Her ay için hesapla
        for month in range(1, time * 12 + 1):
            # Aylık getiri
            monthly_growth = current_value * monthly_rate
            
            # Değeri güncelle
            current_value += monthly_growth + monthly_contribution
            
            # Toplam yatırımı güncelle
            total_investment += monthly_contribution
            
            # Toplam getiriyi güncelle
            total_growth += monthly_growth
            
            # Her yıl için sonuçları kaydet
            if month % 12 == 0:
                year = month // 12
                results.append({
                    'year': year,
                    'value': current_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                    'investment': total_investment.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                    'growth': total_growth.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                })
        
        return {
            'initial_investment': initial_investment,
            'monthly_contribution': monthly_contribution,
            'annual_rate': rate,
            'time_years': time,
            'final_value': current_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'total_investment': total_investment.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'total_growth': total_growth.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'results': results
        }

class TransactionAnalyzer:
    """
    İşlem analizleri için servis sınıfı.
    
    Args:
        transaction_model: İşlem modeli
        category_model: Kategori modeli
    """
    def __init__(self, transaction_model, category_model):
        self.transaction_model = transaction_model
        self.category_model = category_model
    
    def get_summary_by_period(self, user, period='monthly', reference_date=None):
        """
        Belirtilen dönem için gelir-gider özetini getirir.
        
        Args:
            user: Kullanıcı
            period (str, optional): Dönem ('daily', 'weekly', 'monthly'). Varsayılan: 'monthly'
            reference_date (date, optional): Referans tarih. Varsayılan: None (bugün)
            
        Returns:
            dict: Dönem özeti
        """
        # Tarih aralığını al
        start_date, end_date = get_date_range(period, reference_date)
        
        # Gelirler
        income = self.transaction_model.objects.filter(
            user=user,
            category__type='gelir',
            date__range=[start_date, end_date]
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Giderler
        expense = self.transaction_model.objects.filter(
            user=user,
            category__type='gider',
            date__range=[start_date, end_date]
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Net tasarruf
        net_savings = income - expense
        
        return {
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'income': income,
            'expense': expense,
            'net_savings': net_savings,
            'savings_rate': (net_savings / income * 100) if income > 0 else 0
        }
    
    def get_category_breakdown(self, user, category_type, period='monthly', reference_date=None):
        """
        Kategori bazında harcama veya gelir dağılımını getirir.
        
        Args:
            user: Kullanıcı
            category_type (str): Kategori türü ('gelir' veya 'gider')
            period (str, optional): Dönem ('daily', 'weekly', 'monthly'). Varsayılan: 'monthly'
            reference_date (date, optional): Referans tarih. Varsayılan: None (bugün)
            
        Returns:
            list: Kategori bazında harcama veya gelir dağılımı
        """
        # Tarih aralığını al
        start_date, end_date = get_date_range(period, reference_date)
        
        # Toplam miktar
        total = self.transaction_model.objects.filter(
            user=user,
            category__type=category_type,
            date__range=[start_date, end_date]
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Kategori bazında dağılım
        categories = self.category_model.objects.filter(type=category_type)
        breakdown = []
        
        for category in categories:
            amount = self.transaction_model.objects.filter(
                user=user,
                category=category,
                date__range=[start_date, end_date]
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            if amount > 0:
                percentage = (amount / total * 100) if total > 0 else 0
                
                breakdown.append({
                    'category': category.name,
                    'amount': amount,
                    'percentage': percentage,
                    'icon': category.icon
                })
        
        # Miktara göre azalan sıralama
        breakdown.sort(key=lambda x: x['amount'], reverse=True)
        
        return {
            'total': total,
            'breakdown': breakdown,
            'period': period,
            'start_date': start_date,
            'end_date': end_date
        }
    
    def get_trends_by_month(self, user, months=6):
        """
        Aylık gelir-gider trendlerini getirir.
        
        Args:
            user: Kullanıcı
            months (int, optional): Ay sayısı. Varsayılan: 6
            
        Returns:
            dict: Aylık gelir-gider trendleri
        """
        # Bugünün tarihi
        today = timezone.now().date()
        
        # Sonuç listesi
        trends = []
        
        # Belirtilen ay sayısı kadar geriye git
        for i in range(months - 1, -1, -1):
            # Ay ve yıl hesapla
            month = today.month - i
            year = today.year
            
            while month < 1:
                month += 12
                year -= 1
            
            # Ayın başlangıç ve bitiş tarihleri
            if month == 12:
                start_date = datetime.date(year, month, 1)
                end_date = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
            else:
                start_date = datetime.date(year, month, 1)
                end_date = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
            
            # Gelirler
            income = self.transaction_model.objects.filter(
                user=user,
                category__type='gelir',
                date__range=[start_date, end_date]
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # Giderler
            expense = self.transaction_model.objects.filter(
                user=user,
                category__type='gider',
                date__range=[start_date, end_date]
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # Net tasarruf
            net_savings = income - expense
            
            trends.append({
                'month': start_date.strftime('%b'),
                'year': year,
                'income': float(income),
                'expense': float(expense),
                'net_savings': float(net_savings)
            })
        
        return {
            'trends': trends,
            'months': [trend['month'] for trend in trends],
            'income_data': [trend['income'] for trend in trends],
            'expense_data': [trend['expense'] for trend in trends],
            'savings_data': [trend['net_savings'] for trend in trends]
        } 