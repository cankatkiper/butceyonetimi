from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    PasswordResetRequestForm,
    SetNewPasswordForm,
    FinancialInfoForm,
    TransactionForm,
    SavingGoalForm,
    PurchaseGoalForm,
    SpendingLimitForm
)
from .models import (
    PasswordResetToken,
    Category,
    Transaction,
    SavingGoal,
    PurchaseGoal,
    SpendingLimit
)
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
import uuid
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
import json
from decimal import Decimal

User = get_user_model()

def landing_page(request):
    """Tanıtım sayfasını görüntüler"""
    return render(request, 'accounts/landing_page.html')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Kayıt başarılı! Hoş geldiniz.')
            return redirect('financial_info')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Başarıyla giriş yaptınız!')
                # Check if the user has filled out their financial information
                if not user.financial_info_completed:
                    return redirect('financial_info')
                return redirect('dashboard')
            else:
                messages.error(request, 'Geçersiz kullanıcı adı veya şifre!')
        else:
            messages.error(request, 'Lütfen geçerli bilgiler girin!')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Başarıyla çıkış yaptınız.')
    return redirect('login')

@login_required
def home_view(request):
    return render(request, 'accounts/home.html')

def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                token = PasswordResetToken.objects.create(user=user)
                
                reset_url = f"{request.scheme}://{request.get_host()}/reset-password/{token.token}"
                send_mail(
                    'Şifre Sıfırlama',
                    f'Şifrenizi sıfırlamak için aşağıdaki linke tıklayın:\n\n{reset_url}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                messages.success(request, 'Şifre sıfırlama bağlantısı e-posta adresinize gönderildi.')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'Bu e-posta adresiyle kayıtlı bir kullanıcı bulunamadı.')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'accounts/password_reset_request.html', {'form': form})

def password_reset_confirm(request, token):
    try:
        reset_token = PasswordResetToken.objects.get(token=token, is_used=False)
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Geçersiz veya kullanılmış token.')
        return redirect('login')

    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            user = reset_token.user
            user.set_password(form.cleaned_data['password1'])
            user.save()
            reset_token.is_used = True
            reset_token.save()
            messages.success(request, 'Şifreniz başarıyla değiştirildi. Şimdi giriş yapabilirsiniz.')
            return redirect('login')
    else:
        form = SetNewPasswordForm()
    
    return render(request, 'accounts/password_reset_confirm.html', {'form': form})

@login_required
def financial_info_view(request):
    if request.method == 'POST':
        form = FinancialInfoForm(request.POST)
        if form.is_valid():
            user = request.user
            user.total_amount = form.cleaned_data['total_amount']
            user.financial_info_completed = True
            user.save()
            messages.success(request, 'Finansal bilgileriniz başarıyla kaydedildi.')
            
            # Temel kategorileri oluştur
            kategoriler = [
                {'name': 'Maaş', 'type': 'gelir', 'icon': 'money-bill'},
                {'name': 'Ek Gelir', 'type': 'gelir', 'icon': 'plus-circle'},
                {'name': 'Yatırım Getirisi', 'type': 'gelir', 'icon': 'chart-line'},
                {'name': 'Kira', 'type': 'gider', 'icon': 'home'},
                {'name': 'Market', 'type': 'gider', 'icon': 'shopping-cart'},
                {'name': 'Faturalar', 'type': 'gider', 'icon': 'file-invoice'},
                {'name': 'Ulaşım', 'type': 'gider', 'icon': 'car'},
                {'name': 'Eğlence', 'type': 'gider', 'icon': 'film'},
                {'name': 'Sağlık', 'type': 'gider', 'icon': 'medkit'},
                {'name': 'Giyim', 'type': 'gider', 'icon': 'tshirt'},
                {'name': 'Eğitim', 'type': 'gider', 'icon': 'graduation-cap'},
                {'name': 'Diğer', 'type': 'gider', 'icon': 'ellipsis-h'},
            ]
            
            for kategori in kategoriler:
                Category.objects.get_or_create(
                    name=kategori['name'],
                    type=kategori['type'],
                    icon=kategori['icon']
                )
            
            return redirect('dashboard')
    else:
        form = FinancialInfoForm()
    return render(request, 'accounts/financial_info.html', {'form': form})

@login_required
def dashboard_view(request):
    user = request.user
    
    # Son 5 işlem
    recent_transactions = Transaction.objects.filter(user=user).order_by('-date')[:5]
    
    # Gelir ve giderleri hesapla
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    income_this_month = Transaction.objects.filter(
        user=user,
        category__type='gelir',
        date__range=[start_of_month, end_of_month]
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    expense_this_month = Transaction.objects.filter(
        user=user,
        category__type='gider',
        date__range=[start_of_month, end_of_month]
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Tasarruf hedefleri
    saving_goals = SavingGoal.objects.filter(user=user)
    
    # Satın alma hedefleri
    purchase_goals = PurchaseGoal.objects.filter(user=user)
    
    # Bildirimler
    notifications = []
    
    # Harcama limitlerini kontrol et
    spending_limits = SpendingLimit.objects.filter(user=user)
    for limit in spending_limits:
        if limit.is_exceeded():
            notifications.append(f"'{limit.category.name}' kategorisindeki harcama limitinizi aştınız!")
    
    # Satın alma hedeflerini kontrol et
    for goal in purchase_goals:
        if goal.can_purchase(user.total_amount) and not goal.is_notified:
            notifications.append(f"'{goal.name}' ürününü satın almak için uygun zamanda olabilirsiniz!")
            goal.is_notified = True
            goal.save()
    
    # Son 6 ayın gelir/gider grafiği için veri
    months = []
    income_data = []
    expense_data = []
    
    for i in range(5, -1, -1):
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
        months.append(month_name)
        
        month_income = Transaction.objects.filter(
            user=user,
            category__type='gelir',
            date__range=[start_date, end_date]
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        month_expense = Transaction.objects.filter(
            user=user,
            category__type='gider',
            date__range=[start_date, end_date]
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        income_data.append(float(month_income))
        expense_data.append(float(month_expense))
    
    chart_data = {
        'months': months,
        'income': income_data,
        'expense': expense_data
    }
    
    # Harcama kategorilerine göre dağılım
    expense_by_category = []
    expense_categories = Category.objects.filter(type='gider')
    
    for category in expense_categories:
        category_expense = Transaction.objects.filter(
            user=user,
            category=category,
            date__range=[start_of_month, end_of_month]
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        if category_expense > 0:
            expense_by_category.append({
                'category': category.name,
                'amount': float(category_expense),
                'icon': category.icon
            })
    
    context = {
        'user': user,
        'recent_transactions': recent_transactions,
        'income_this_month': income_this_month,
        'expense_this_month': expense_this_month,
        'saving_goals': saving_goals,
        'purchase_goals': purchase_goals,
        'notifications': notifications,
        'chart_data': json.dumps(chart_data),
        'expense_by_category': expense_by_category,
    }
    
    return render(request, 'accounts/dashboard.html', context)

@login_required
def income_expense_view(request):
    user = request.user
    
    # Gelir ve giderleri hesapla
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    transactions = Transaction.objects.filter(user=user).order_by('-date')
    income_this_month = transactions.filter(
        category__type='gelir',
        date__gte=start_of_month
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    expense_this_month = transactions.filter(
        category__type='gider',
        date__gte=start_of_month
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'transactions': transactions,
        'income_this_month': income_this_month,
        'expense_this_month': expense_this_month,
    }
    
    return render(request, 'accounts/income_expense.html', context)

@login_required
def add_income_view(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user, transaction_type='gelir')
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            
            # Kullanıcı toplam miktarını güncelle
            request.user.total_amount += transaction.amount
            request.user.save()
            
            messages.success(request, 'Gelir başarıyla kaydedildi.')
            return redirect('income_expense')
    else:
        form = TransactionForm(user=request.user, transaction_type='gelir')
    
    return render(request, 'accounts/add_transaction.html', {
        'form': form,
        'transaction_type': 'gelir'
    })

@login_required
def add_expense_view(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user, transaction_type='gider')
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            
            # Kullanıcı toplam miktarını güncelle
            request.user.total_amount -= transaction.amount
            request.user.save()
            
            # Harcama limitlerini kontrol et
            category = transaction.category
            limits = SpendingLimit.objects.filter(user=request.user, category=category)
            
            for limit in limits:
                if limit.is_exceeded():
                    messages.warning(
                        request, 
                        f"'{category.name}' kategorisindeki {limit.get_period_display().lower()} harcama limitinizi aştınız!"
                    )
            
            messages.success(request, 'Gider başarıyla kaydedildi.')
            return redirect('income_expense')
    else:
        form = TransactionForm(user=request.user, transaction_type='gider')
    
    return render(request, 'accounts/add_transaction.html', {
        'form': form,
        'transaction_type': 'gider'
    })

@login_required
def goals_view(request):
    user = request.user
    saving_goals = SavingGoal.objects.filter(user=user)
    purchase_goals = PurchaseGoal.objects.filter(user=user)
    
    # Satın alma hedeflerini kontrol et
    for goal in purchase_goals:
        if goal.can_purchase(user.total_amount) and not goal.is_notified:
            messages.info(
                request, 
                f"'{goal.name}' ürününü satın almak için uygun zamanda olabilirsiniz!"
            )
            goal.is_notified = True
            goal.save()
    
    context = {
        'saving_goals': saving_goals,
        'purchase_goals': purchase_goals,
    }
    
    return render(request, 'accounts/goals.html', context)

@login_required
def add_saving_goal_view(request):
    if request.method == 'POST':
        form = SavingGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, 'Tasarruf hedefi başarıyla oluşturuldu.')
            return redirect('goals')
    else:
        form = SavingGoalForm()
    
    return render(request, 'accounts/add_saving_goal.html', {'form': form})

@login_required
def add_purchase_goal_view(request):
    if request.method == 'POST':
        form = PurchaseGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, 'Satın alma hedefi başarıyla oluşturuldu.')
            return redirect('goals')
    else:
        form = PurchaseGoalForm()
    
    return render(request, 'accounts/add_purchase_goal.html', {'form': form})

@login_required
def spending_limits_view(request):
    user = request.user
    limits = SpendingLimit.objects.filter(user=user)
    
    for limit in limits:
        if limit.is_exceeded():
            messages.warning(
                request, 
                f"'{limit.category.name}' kategorisindeki {limit.get_period_display().lower()} harcama limitinizi aştınız!"
            )
    
    context = {
        'limits': limits,
    }
    
    return render(request, 'accounts/spending_limits.html', context)

@login_required
def add_spending_limit_view(request):
    if request.method == 'POST':
        form = SpendingLimitForm(request.POST, user=request.user)
        if form.is_valid():
            limit = form.save(commit=False)
            limit.user = request.user
            limit.save()
            messages.success(request, 'Harcama limiti başarıyla oluşturuldu.')
            return redirect('spending_limits')
    else:
        form = SpendingLimitForm(user=request.user)
    
    return render(request, 'accounts/add_spending_limit.html', {'form': form})

@login_required
def reports_view(request):
    user = request.user
    
    # Varsayılan olarak bu ayın verilerini göster
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Tarih aralığı seçimi
    start_date = request.GET.get('start_date', start_of_month)
    end_date = request.GET.get('end_date', end_of_month)
    
    if isinstance(start_date, str):
        start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if isinstance(end_date, str):
        end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Gelir ve gider verileri
    income_data = Transaction.objects.filter(
        user=user,
        category__type='gelir',
        date__range=[start_date, end_date]
    )
    
    expense_data = Transaction.objects.filter(
        user=user,
        category__type='gider',
        date__range=[start_date, end_date]
    )
    
    total_income = income_data.aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = expense_data.aggregate(Sum('amount'))['amount__sum'] or 0
    net_savings = total_income - total_expense
    
    # Kategori bazında gelir-gider dağılımı
    income_by_category = {}
    income_percentages = {}
    for transaction in income_data:
        category_name = transaction.category.name
        if category_name in income_by_category:
            income_by_category[category_name] += transaction.amount
        else:
            income_by_category[category_name] = transaction.amount
    
    # Gelir yüzdelerini hesapla
    for category, amount in income_by_category.items():
        if total_income > 0:
            income_percentages[category] = round((float(amount) / float(total_income)) * 100, 1)
        else:
            income_percentages[category] = 0.0
    
    expense_by_category = {}
    expense_percentages = {}
    for transaction in expense_data:
        category_name = transaction.category.name
        if category_name in expense_by_category:
            expense_by_category[category_name] += transaction.amount
        else:
            expense_by_category[category_name] = transaction.amount
    
    # Gider yüzdelerini hesapla
    for category, amount in expense_by_category.items():
        if total_expense > 0:
            expense_percentages[category] = round((float(amount) / float(total_expense)) * 100, 1)
        else:
            expense_percentages[category] = 0.0
    
    # Veriyi grafik için hazırla
    income_chart_data = [{'category': k, 'amount': float(v)} for k, v in income_by_category.items()]
    expense_chart_data = [{'category': k, 'amount': float(v)} for k, v in expense_by_category.items()]
    
    # Günlük gelir-gider grafiği
    daily_data = {}
    date_range = (end_date - start_date).days + 1
    
    for i in range(date_range):
        current_date = start_date + timedelta(days=i)
        daily_data[current_date.strftime('%Y-%m-%d')] = {'income': 0, 'expense': 0}
    
    for transaction in income_data:
        date_str = transaction.date.strftime('%Y-%m-%d')
        if date_str in daily_data:
            daily_data[date_str]['income'] += float(transaction.amount)
    
    for transaction in expense_data:
        date_str = transaction.date.strftime('%Y-%m-%d')
        if date_str in daily_data:
            daily_data[date_str]['expense'] += float(transaction.amount)
    
    daily_chart_data = [
        {'date': k, 'income': v['income'], 'expense': v['expense']} 
        for k, v in daily_data.items()
    ]
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_savings': net_savings,
        'income_by_category': income_by_category,
        'expense_by_category': expense_by_category,
        'income_percentages': income_percentages,
        'expense_percentages': expense_percentages,
        'income_chart_data': json.dumps(income_chart_data),
        'expense_chart_data': json.dumps(expense_chart_data),
        'daily_chart_data': json.dumps(daily_chart_data),
    }
    
    return render(request, 'accounts/reports.html', context)

@login_required
def settings_view(request):
    return render(request, 'accounts/settings.html')


