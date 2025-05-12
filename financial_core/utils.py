from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

def get_date_range(period, start_date=None):
    """Belirtilen periyoda göre tarih aralığı hesaplar"""
    today = start_date or timezone.now().date()
    
    if period == 'daily':
        return today, today
    elif period == 'weekly':
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return start_of_week, end_of_week
    elif period == 'monthly':
        start_of_month = today.replace(day=1)
        if today.month == 12:
            end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        return start_of_month, end_of_month
    else:
        return None, None
    
def calculate_period_transactions(transaction_queryset, period, date=None, category=None):
    """Belirli bir dönem içindeki işlemleri hesaplar"""
    start_date, end_date = get_date_range(period, date)
    if not start_date or not end_date:
        return Decimal(0)
    
    queryset = transaction_queryset.filter(date__range=[start_date, end_date])
    
    if category:
        queryset = queryset.filter(category=category)
    
    return queryset.aggregate(Sum('amount'))['amount__sum'] or Decimal(0)

def get_monthly_data(transaction_queryset, months=6, category_field_name='category'):
    """Son n ay için gelir ve gider toplamlarını hesaplar"""
    today = timezone.now().date()
    
    months_data = []
    income_data = []
    expense_data = []
    
    for i in range(months-1, -1, -1):
        month = today.month - i
        year = today.year
        
        while month < 1:
            month += 12
            year -= 1
        
        start_date = timezone.datetime(year, month, 1).date()
        if month == 12:
            end_date = timezone.datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = timezone.datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        month_name = start_date.strftime('%b')
        months_data.append(month_name)
        
        filter_kwargs = {
            'date__range': [start_date, end_date],
            f'{category_field_name}__type': 'gelir'
        }
        month_income = transaction_queryset.filter(**filter_kwargs).aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
        
        filter_kwargs = {
            'date__range': [start_date, end_date],
            f'{category_field_name}__type': 'gider'
        }
        month_expense = transaction_queryset.filter(**filter_kwargs).aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
        
        income_data.append(float(month_income))
        expense_data.append(float(month_expense))
    
    return {
        'months': months_data,
        'income': income_data,
        'expense': expense_data
    }

def get_category_summary(transaction_queryset, start_date=None, end_date=None, category_type='gider', category_field_name='category'):
    """Belirli bir dönemdeki işlemleri kategoriye göre gruplar"""
    if not start_date:
        today = timezone.now().date()
        start_date = today.replace(day=1)
        
    if not end_date:
        today = timezone.now().date()
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    
    filter_kwargs = {
        'date__range': [start_date, end_date],
        f'{category_field_name}__type': category_type
    }
    
    transactions = transaction_queryset.filter(**filter_kwargs)
    
    # Kategorilere göre gruplandırma
    result = {}
    for transaction in transactions:
        category = getattr(transaction, category_field_name)
        if category.id not in result:
            result[category.id] = {
                'category': category.name,
                'amount': Decimal(0),
                'icon': category.icon
            }
        result[category.id]['amount'] += transaction.amount
    
    # Sadece pozitif tutarlı kategorileri döndür
    summary = []
    for category_data in result.values():
        if category_data['amount'] > 0:
            category_data['amount'] = float(category_data['amount'])
            summary.append(category_data)
    
    return summary 