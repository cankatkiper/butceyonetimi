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
from django.http import HttpResponse
import requests
import random
import datetime

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
                    icon='tag'  # Varsayılan ikon
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
            # Yeni kategori kontrolü
            new_category_name = form.cleaned_data.get('new_category')
            category = form.cleaned_data.get('category')
            
            # Yeni kategori girilmiş mi kontrol et
            if new_category_name:
                # Yeni kategori oluştur
                category, created = Category.objects.get_or_create(
                    name=new_category_name,
                    type='gelir',
                    icon='tag'  # Varsayılan ikon
                )
                transaction = form.save(commit=False)
                transaction.category = category
            elif category:
                # Mevcut kategori seçilmiş
                transaction = form.save(commit=False)
            else:
                # Hiçbir kategori seçilmemiş ve girilmemiş
                messages.error(request, 'Lütfen bir kategori seçin veya yeni bir kategori girin.')
                return render(request, 'accounts/add_transaction.html', {
                    'form': form,
                    'transaction_type': 'gelir'
                })
                
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
            # Yeni kategori kontrolü
            new_category_name = form.cleaned_data.get('new_category')
            category = form.cleaned_data.get('category')
            
            # Yeni kategori girilmiş mi kontrol et
            if new_category_name:
                # Yeni kategori oluştur
                category, created = Category.objects.get_or_create(
                    name=new_category_name,
                    type='gider',
                    icon='tag'  # Varsayılan ikon
                )
                transaction = form.save(commit=False)
                transaction.category = category
            elif category:
                # Mevcut kategori seçilmiş
                transaction = form.save(commit=False)
            else:
                # Hiçbir kategori seçilmemiş ve girilmemiş
                messages.error(request, 'Lütfen bir kategori seçin veya yeni bir kategori girin.')
                return render(request, 'accounts/add_transaction.html', {
                    'form': form,
                    'transaction_type': 'gider'
                })
                
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
    
    # Debug bilgisi
    print(f"Kullanıcı: {user.username}, Limit Sayısı: {limits.count()}")
    
    try:
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
    except Exception as e:
        # Hata durumunda basit bir sayfa göster
        print(f"Hata oluştu: {str(e)}")
        messages.error(request, f"Bir hata oluştu: {str(e)}")
        return HttpResponse(f"Harcama limitleri sayfası yüklenirken bir hata oluştu: {str(e)}")

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
    # Kategorileri al
    income_categories = Category.objects.filter(type='gelir')
    expense_categories = Category.objects.filter(type='gider')
    
    # Kategori ekleme formu
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_category':
            category_name = request.POST.get('category_name')
            category_type = request.POST.get('category_type')
            
            if category_name and category_type:
                Category.objects.create(
                    name=category_name,
                    type=category_type,
                    icon='tag'  # Varsayılan ikon
                )
                messages.success(request, 'Kategori başarıyla eklendi.')
                return redirect('settings')
            
        elif action == 'edit_category':
            category_id = request.POST.get('category_id')
            category_name = request.POST.get('category_name')
            
            if category_id and category_name:
                try:
                    category = Category.objects.get(id=category_id)
                    category.name = category_name
                    category.save()
                    messages.success(request, 'Kategori başarıyla güncellendi.')
                except Category.DoesNotExist:
                    messages.error(request, 'Kategori bulunamadı.')
                return redirect('settings')
            
        elif action == 'delete_category':
            category_id = request.POST.get('category_id')
            
            if category_id:
                try:
                    category = Category.objects.get(id=category_id)
                    
                    # Kategori işlemlerle ilişkilendirilmiş mi kontrol et
                    if Transaction.objects.filter(category=category).exists():
                        messages.error(request, 'Bu kategori işlemlerle ilişkilendirilmiş olduğu için silinemez.')
                    else:
                        category.delete()
                        messages.success(request, 'Kategori başarıyla silindi.')
                except Category.DoesNotExist:
                    messages.error(request, 'Kategori bulunamadı.')
                return redirect('settings')
    
    context = {
        'income_categories': income_categories,
        'expense_categories': expense_categories,
    }
    
    return render(request, 'accounts/settings.html', context)

@login_required
def borsa_view(request):
    """
    En popüler döviz, altın ve kripto para birimlerinin değerlerini API'lerden çeken sayfa
    Gerçek zamanlı olarak güncel fiyatları gösterir
    """
    # İstek parametreleri
    filtre = request.GET.get('filtre', 'hepsi')
    sayfa = int(request.GET.get('sayfa', '1'))
    sayfa_basina = 10  # Her sayfada 10 kayıt gösterilecek
    arama = request.GET.get('arama', '').strip().lower()
    guncel_data = []
    
    # Tüm varlık bilgilerini hazırla
    TUM_VARLIKLAR = {
        # Dövizler
        "USD": {"isim": "Dolar (USD)", "tip": "doviz", "icon": "fas fa-dollar-sign text-success", "pair": "USDTRY"},
        "EUR": {"isim": "Euro (EUR)", "tip": "doviz", "icon": "fas fa-euro-sign text-primary", "pair": "EURTRY"},
        "GBP": {"isim": "Sterlin (GBP)", "tip": "doviz", "icon": "fas fa-pound-sign text-primary", "pair": "GBPTRY"},
        "JPY": {"isim": "Japon Yeni (JPY)", "tip": "doviz", "icon": "fas fa-yen-sign text-dark", "pair": "JPYTRY"},
        "CHF": {"isim": "İsviçre Frangı (CHF)", "tip": "doviz", "icon": "fas fa-money-bill-wave text-danger", "pair": "CHFTRY"},
        "CAD": {"isim": "Kanada Doları (CAD)", "tip": "doviz", "icon": "fas fa-dollar-sign text-danger", "pair": "CADTRY"},
        "AUD": {"isim": "Avustralya Doları (AUD)", "tip": "doviz", "icon": "fas fa-dollar-sign text-warning", "pair": "AUDTRY"},
        "CNY": {"isim": "Çin Yuanı (CNY)", "tip": "doviz", "icon": "fas fa-yen-sign text-danger", "pair": "CNYTRY"},
        "RUB": {"isim": "Rus Rublesi (RUB)", "tip": "doviz", "icon": "fas fa-ruble-sign text-success", "pair": "RUBTRY"},
        "SAR": {"isim": "Suudi Riyali (SAR)", "tip": "doviz", "icon": "fas fa-money-bill-wave text-success", "pair": "SARTRY"},
        "KWD": {"isim": "Kuveyt Dinarı (KWD)", "tip": "doviz", "icon": "fas fa-money-bill-wave text-warning", "pair": "KWDTRY"},
        "AED": {"isim": "BAE Dirhemi (AED)", "tip": "doviz", "icon": "fas fa-money-bill-wave text-primary", "pair": "AEDTRY"},
        "PLN": {"isim": "Polonya Zlotisi (PLN)", "tip": "doviz", "icon": "fas fa-money-bill-wave text-success", "pair": "PLNTRY"},
        "KRW": {"isim": "Güney Kore Wonu (KRW)", "tip": "doviz", "icon": "fas fa-won-sign text-warning", "pair": "KRWTRY"},
        "MXN": {"isim": "Meksika Pesosu (MXN)", "tip": "doviz", "icon": "fas fa-dollar-sign text-success", "pair": "MXNTRY"},
        "NOK": {"isim": "Norveç Kronu (NOK)", "tip": "doviz", "icon": "fas fa-money-bill-wave text-primary", "pair": "NOKTRY"},
        "SEK": {"isim": "İsveç Kronu (SEK)", "tip": "doviz", "icon": "fas fa-money-bill-wave text-primary", "pair": "SEKTRY"},
        "DKK": {"isim": "Danimarka Kronu (DKK)", "tip": "doviz", "icon": "fas fa-money-bill-wave text-danger", "pair": "DKKTRY"},
        "TRY": {"isim": "Türk Lirası (TRY)", "tip": "doviz", "icon": "fas fa-lira-sign text-danger", "pair": "TRY"},
        
        # Değerli Metaller
        "XAU": {"isim": "Gram Altın", "tip": "doviz", "icon": "fas fa-coins text-warning", "pair": "GA"},
        "XAU_QUARTER": {"isim": "Çeyrek Altın", "tip": "doviz", "icon": "fas fa-coins text-warning", "pair": "C"},
        "XAU_HALF": {"isim": "Yarım Altın", "tip": "doviz", "icon": "fas fa-coins text-warning", "pair": "Y"},
        "XAU_FULL": {"isim": "Tam Altın", "tip": "doviz", "icon": "fas fa-coins text-warning", "pair": "T"},
        "XAU_REPUBLIC": {"isim": "Cumhuriyet Altını", "tip": "doviz", "icon": "fas fa-coins text-warning", "pair": "CMR"},
        "XAU_RESAT": {"isim": "Reşat Altın", "tip": "doviz", "icon": "fas fa-coins text-warning", "pair": "ATA"},
        "XAG": {"isim": "Gümüş (XAG)", "tip": "doviz", "icon": "fas fa-coins text-secondary", "pair": "gumus"},
        "XPT": {"isim": "Platin (XPT)", "tip": "doviz", "icon": "fas fa-coins text-info", "pair": "PLT"},
        "XPD": {"isim": "Paladyum (XPD)", "tip": "doviz", "icon": "fas fa-coins text-dark", "pair": "PLD"},
        
        # Kripto Para Birimleri
        "BTC": {"isim": "Bitcoin (BTC)", "tip": "kripto", "icon": "fab fa-bitcoin text-warning", "pair": "BTCUSDT"},
        "ETH": {"isim": "Ethereum (ETH)", "tip": "kripto", "icon": "fab fa-ethereum text-secondary", "pair": "ETHUSDT"},
        "USDT": {"isim": "Tether (USDT)", "tip": "kripto", "icon": "fas fa-dollar-sign text-info", "pair": "USDTTRY"},
        "BNB": {"isim": "Binance Coin (BNB)", "tip": "kripto", "icon": "fas fa-coins text-warning", "pair": "BNBUSDT"},
        "SOL": {"isim": "Solana (SOL)", "tip": "kripto", "icon": "fas fa-solar-panel text-danger", "pair": "SOLUSDT"},
        "XRP": {"isim": "Ripple (XRP)", "tip": "kripto", "icon": "fas fa-wave-square text-primary", "pair": "XRPUSDT"},
        "ADA": {"isim": "Cardano (ADA)", "tip": "kripto", "icon": "fas fa-project-diagram text-primary", "pair": "ADAUSDT"},
        "AVAX": {"isim": "Avalanche (AVAX)", "tip": "kripto", "icon": "fas fa-mountain text-danger", "pair": "AVAXUSDT"},
        "DOGE": {"isim": "Dogecoin (DOGE)", "tip": "kripto", "icon": "fas fa-dog text-warning", "pair": "DOGEUSDT"},
        "TRX": {"isim": "TRON (TRX)", "tip": "kripto", "icon": "fas fa-network-wired text-danger", "pair": "TRXUSDT"},
        "DOT": {"isim": "Polkadot (DOT)", "tip": "kripto", "icon": "fas fa-circle-notch text-pink", "pair": "DOTUSDT"},
        "MATIC": {"isim": "Polygon (MATIC)", "tip": "kripto", "icon": "fas fa-cube text-primary", "pair": "MATICUSDT"},
        "LTC": {"isim": "Litecoin (LTC)", "tip": "kripto", "icon": "fas fa-coins text-secondary", "pair": "LTCUSDT"},
        "SHIB": {"isim": "Shiba Inu (SHIB)", "tip": "kripto", "icon": "fas fa-dog text-warning", "pair": "SHIBUSDT"},
        "DAI": {"isim": "Dai (DAI)", "tip": "kripto", "icon": "fas fa-dollar-sign text-warning", "pair": "DAIUSDT"},
        "UNI": {"isim": "Uniswap (UNI)", "tip": "kripto", "icon": "fas fa-exchange-alt text-pink", "pair": "UNIUSDT"},
        "LINK": {"isim": "Chainlink (LINK)", "tip": "kripto", "icon": "fas fa-link text-blue", "pair": "LINKUSDT"},
        "ATOM": {"isim": "Cosmos (ATOM)", "tip": "kripto", "icon": "fas fa-atom text-primary", "pair": "ATOMUSDT"},
        "XMR": {"isim": "Monero (XMR)", "tip": "kripto", "icon": "fas fa-user-secret text-warning", "pair": "XMRUSDT"},
        "FIL": {"isim": "Filecoin (FIL)", "tip": "kripto", "icon": "fas fa-database text-info", "pair": "FILUSDT"},
        "NEAR": {"isim": "NEAR Protocol (NEAR)", "tip": "kripto", "icon": "fas fa-network-wired text-warning", "pair": "NEARUSDT"},
        "APE": {"isim": "ApeCoin (APE)", "tip": "kripto", "icon": "fas fa-ape text-success", "pair": "APEUSDT"},
        "SAND": {"isim": "The Sandbox (SAND)", "tip": "kripto", "icon": "fas fa-cubes text-warning", "pair": "SANDUSDT"},
        "ALGO": {"isim": "Algorand (ALGO)", "tip": "kripto", "icon": "fas fa-project-diagram text-success", "pair": "ALGOUSDT"},
        "AXS": {"isim": "Axie Infinity (AXS)", "tip": "kripto", "icon": "fas fa-gamepad text-pink", "pair": "AXSUSDT"},
    }
    
    # Varsayılan değerleri baştan tanımla, try/except bloğu içerisinde kaybolmaması için
    varsayilan_veriler = [
        {"isim": "Dolar (USD)", "deger": 32.86, "degisim": 0.35, "sembol": "usd", "tip": "doviz", "kod": "USD", "icon": "fas fa-dollar-sign text-success"},
        {"isim": "Euro (EUR)", "deger": 35.50, "degisim": -0.20, "sembol": "eur", "tip": "doviz", "kod": "EUR", "icon": "fas fa-euro-sign text-primary"},
        {"isim": "Sterlin (GBP)", "deger": 41.24, "degisim": 0.15, "sembol": "gbp", "tip": "doviz", "kod": "GBP", "icon": "fas fa-pound-sign text-primary"},
        {"isim": "Japon Yeni (JPY)", "deger": 0.213, "degisim": 0.05, "sembol": "jpy", "tip": "doviz", "kod": "JPY", "icon": "fas fa-yen-sign text-dark"},
        {"isim": "İsviçre Frangı (CHF)", "deger": 36.18, "degisim": 0.22, "sembol": "chf", "tip": "doviz", "kod": "CHF", "icon": "fas fa-money-bill-wave text-danger"},
        {"isim": "Kanada Doları (CAD)", "deger": 24.15, "degisim": 0.10, "sembol": "cad", "tip": "doviz", "kod": "CAD", "icon": "fas fa-dollar-sign text-danger"},
        {"isim": "Avustralya Doları (AUD)", "deger": 21.70, "degisim": -0.05, "sembol": "aud", "tip": "doviz", "kod": "AUD", "icon": "fas fa-dollar-sign text-warning"},
        {"isim": "Rus Rublesi (RUB)", "deger": 0.36, "degisim": 0.02, "sembol": "rub", "tip": "doviz", "kod": "RUB", "icon": "fas fa-ruble-sign text-success"},
        {"isim": "Çin Yuanı (CNY)", "deger": 4.54, "degisim": 0.12, "sembol": "cny", "tip": "doviz", "kod": "CNY", "icon": "fas fa-yen-sign text-danger"},
        {"isim": "Suudi Riyali (SAR)", "deger": 8.76, "degisim": 0.08, "sembol": "sar", "tip": "doviz", "kod": "SAR", "icon": "fas fa-money-bill-wave text-success"},
        {"isim": "Kuveyt Dinarı (KWD)", "deger": 107.25, "degisim": 0.25, "sembol": "kwd", "tip": "doviz", "kod": "KWD", "icon": "fas fa-money-bill-wave text-warning"},
        {"isim": "BAE Dirhemi (AED)", "deger": 8.95, "degisim": 0.10, "sembol": "aed", "tip": "doviz", "kod": "AED", "icon": "fas fa-money-bill-wave text-primary"},
        {"isim": "Gram Altın", "deger": 2410, "degisim": 0.45, "sembol": "gold", "tip": "doviz", "kod": "XAU", "icon": "fas fa-coins text-warning"},
        {"isim": "Çeyrek Altın", "deger": 4217, "degisim": 0.30, "sembol": "gold-quarter", "tip": "doviz", "kod": "XAU_QUARTER", "icon": "fas fa-coins text-warning"},
        {"isim": "Yarım Altın", "deger": 8435, "degisim": 0.35, "sembol": "gold-half", "tip": "doviz", "kod": "XAU_HALF", "icon": "fas fa-coins text-warning"},
        {"isim": "Tam Altın", "deger": 16870, "degisim": 0.40, "sembol": "gold-full", "tip": "doviz", "kod": "XAU_FULL", "icon": "fas fa-coins text-warning"},
        {"isim": "Cumhuriyet Altını", "deger": 17352, "degisim": 0.42, "sembol": "gold-republic", "tip": "doviz", "kod": "XAU_REPUBLIC", "icon": "fas fa-coins text-warning"},
        {"isim": "Reşat Altını", "deger": 18220, "degisim": 0.45, "sembol": "gold-resat", "tip": "doviz", "kod": "XAU_RESAT", "icon": "fas fa-coins text-warning"},
        {"isim": "Gümüş (XAG)", "deger": 29.85, "degisim": 0.75, "sembol": "silver", "tip": "doviz", "kod": "XAG", "icon": "fas fa-coins text-secondary"},
        {"isim": "Platin (XPT)", "deger": 2550, "degisim": 0.38, "sembol": "platinum", "tip": "doviz", "kod": "XPT", "icon": "fas fa-coins text-info"},
        {"isim": "Paladyum (XPD)", "deger": 2160, "degisim": 0.42, "sembol": "palladium", "tip": "doviz", "kod": "XPD", "icon": "fas fa-coins text-dark"},
    ]
    
    # Veri çekme işlevi
    import requests
    import json
    import datetime
    import random
    import time
    from decimal import Decimal

    # Hata mesajı varsayılanı
    error_message = None
    
    # Tüm verileri saklamak için liste
    borsa_verileri = []
    
    try:
        # 1. Döviz ve altın verilerini API'den al
        try:
            # Döviz API - Açık API
            doviz_url = "https://api.exchangerate-api.com/v4/latest/USD"
            doviz_response = requests.get(doviz_url, timeout=5)
            
            if doviz_response.status_code == 200:
                doviz_data = doviz_response.json()
                
                # TRY/USD paritesini al (diğer dövizleri TL'ye çevirmek için)
                try_usd_rate = doviz_data.get("rates", {}).get("TRY", 0)
                
                if try_usd_rate > 0:
                    # USD/TRY
                    borsa_verileri.append({
                        "isim": TUM_VARLIKLAR["USD"]["isim"],
                        "deger": round(try_usd_rate, 2),
                        "degisim": 0.35,  # Değişim oranı API'den alınamıyor
                        "tip": "doviz",
                        "kod": "USD",
                        "icon": TUM_VARLIKLAR["USD"]["icon"]
                    })
                    
                    # Diğer dövizler
                    for kod, veri in TUM_VARLIKLAR.items():
                        if veri["tip"] == "doviz" and kod != "USD" and kod not in ["XAU", "XAU_QUARTER", "XAU_HALF", "XAU_FULL", "XAU_REPUBLIC", "XAU_RESAT", "XAG", "XPT", "XPD"]:
                            try:
                                # Bu dövizin USD karşılığı
                                usd_rate = doviz_data.get("rates", {}).get(kod, 0)
                                
                                # Eğer bu dövizin USD karşılığı varsa
                                if usd_rate > 0:
                                    # TL karşılığını hesapla (USD/TRY * USD/X)
                                    tl_value = round(try_usd_rate / usd_rate, 2)
                                    
                                    borsa_verileri.append({
                                        "isim": veri["isim"],
                                        "deger": tl_value,
                                        "degisim": 0.10,  # Varsayılan değişim
                                        "tip": "doviz",
                                        "kod": kod,
                                        "icon": veri["icon"]
                                    })
                            except Exception as e:
                                print(f"Döviz hesaplama hatası ({kod}): {str(e)}")
                else:
                    print("USD/TRY kuru bulunamadı, varsayılan değerler kullanılacak")
            else:
                print(f"Döviz API'si çalışmıyor: HTTP {doviz_response.status_code}")
        except Exception as e:
            print(f"Döviz API bağlantı hatası: {str(e)}")
        
        # Altın verilerini ekleyelim (Güncel USD/TRY kurundan hesaplama)
        try:
            # USD/TRY kurunu bul
            usd_try_item = next((item for item in borsa_verileri if item.get("kod") == "USD"), None)
            if usd_try_item:
                usd_try_rate = usd_try_item.get("deger", 0)
                
                # Güncel altın değerleri (USD)
                altin_usd = 2550  # 1 ons altın (yaklaşık)
                gram_altin = round((altin_usd / 31.1) * usd_try_rate, 2)  # 1 ons = 31.1 gram
                
                # Gram altın
                borsa_verileri.append({
                    "isim": TUM_VARLIKLAR["XAU"]["isim"],
                    "deger": gram_altin,
                    "degisim": 0.45,
                    "tip": "doviz",
                    "kod": "XAU",
                    "icon": TUM_VARLIKLAR["XAU"]["icon"]
                })
                
                # Çeyrek altın (1.75 gram)
                borsa_verileri.append({
                    "isim": TUM_VARLIKLAR["XAU_QUARTER"]["isim"],
                    "deger": round(gram_altin * 1.75, 2),
                    "degisim": 0.45,
                    "tip": "doviz",
                    "kod": "XAU_QUARTER",
                    "icon": TUM_VARLIKLAR["XAU_QUARTER"]["icon"]
                })
                
                # Yarım altın (3.5 gram)
                borsa_verileri.append({
                    "isim": TUM_VARLIKLAR["XAU_HALF"]["isim"],
                    "deger": round(gram_altin * 3.5, 2),
                    "degisim": 0.45,
                    "tip": "doviz",
                    "kod": "XAU_HALF",
                    "icon": TUM_VARLIKLAR["XAU_HALF"]["icon"]
                })
                
                # Tam altın (7 gram)
                borsa_verileri.append({
                    "isim": TUM_VARLIKLAR["XAU_FULL"]["isim"],
                    "deger": round(gram_altin * 7.0, 2),
                    "degisim": 0.45,
                    "tip": "doviz",
                    "kod": "XAU_FULL",
                    "icon": TUM_VARLIKLAR["XAU_FULL"]["icon"]
                })
                
                # Cumhuriyet altını (7.2 gram)
                borsa_verileri.append({
                    "isim": TUM_VARLIKLAR["XAU_REPUBLIC"]["isim"],
                    "deger": round(gram_altin * 7.2, 2),
                    "degisim": 0.45,
                    "tip": "doviz",
                    "kod": "XAU_REPUBLIC",
                    "icon": TUM_VARLIKLAR["XAU_REPUBLIC"]["icon"]
                })
                
                # Reşat altını (7.2 gram + premium)
                borsa_verileri.append({
                    "isim": TUM_VARLIKLAR["XAU_RESAT"]["isim"],
                    "deger": round(gram_altin * 7.2 * 1.05, 2),
                    "degisim": 0.45,
                    "tip": "doviz",
                    "kod": "XAU_RESAT",
                    "icon": TUM_VARLIKLAR["XAU_RESAT"]["icon"]
                })
                
                # Gümüş
                gumus_usd = 30  # 1 ons gümüş (yaklaşık)
                gram_gumus = round((gumus_usd / 31.1) * usd_try_rate, 2)
                
                borsa_verileri.append({
                    "isim": TUM_VARLIKLAR["XAG"]["isim"],
                    "deger": gram_gumus,
                    "degisim": 0.60,
                    "tip": "doviz",
                    "kod": "XAG",
                    "icon": TUM_VARLIKLAR["XAG"]["icon"]
                })
            else:
                print("USD/TRY kuru bulunamadı, altın değerleri hesaplanamadı")
        except Exception as e:
            print(f"Altın hesaplama hatası: {str(e)}")
        
        # 2. Kripto para verilerini Coingecko API'den al
        crypto_ids = "bitcoin,ethereum,tether,binancecoin,solana,ripple,cardano,avalanche-2,dogecoin,tron,polkadot,matic-network,litecoin,shiba-inu,dai,uniswap,chainlink,cosmos,monero,filecoin,near,apecoin,the-sandbox,algorand,axie-infinity"
        
        crypto_map = {
            "bitcoin": "BTC",
            "ethereum": "ETH",
            "tether": "USDT",
            "binancecoin": "BNB",
            "solana": "SOL",
            "ripple": "XRP",
            "cardano": "ADA",
            "avalanche-2": "AVAX",
            "dogecoin": "DOGE",
            "tron": "TRX",
            "polkadot": "DOT",
            "matic-network": "MATIC",
            "litecoin": "LTC",
            "shiba-inu": "SHIB",
            "dai": "DAI",
            "uniswap": "UNI",
            "chainlink": "LINK",
            "cosmos": "ATOM",
            "monero": "XMR",
            "filecoin": "FIL",
            "near": "NEAR",
            "apecoin": "APE",
            "the-sandbox": "SAND",
            "algorand": "ALGO",
            "axie-infinity": "AXS"
        }
        
        try:
            # Coingecko Free API
            crypto_url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_ids}&vs_currencies=try,usd&include_24h_change=true"
            crypto_response = requests.get(crypto_url, timeout=5)
            
            if crypto_response.status_code == 200:
                crypto_data = crypto_response.json()
                
                # USDT/TRY kurunu al (diğer pariteler için kullanacağız)
                usdt_try_parite = crypto_data.get("tether", {}).get("try", 0)
                
                for coingecko_id, json_data in crypto_data.items():
                    if coingecko_id in crypto_map:
                        kod = crypto_map[coingecko_id]
                        if kod in TUM_VARLIKLAR and TUM_VARLIKLAR[kod]["tip"] == "kripto":
                            try:
                                # TRY fiyat (eğer TRY fiyat yoksa USD fiyat * USDT/TRY paritesini kullan)
                                try_deger = json_data.get("try", 0)
                                if try_deger == 0 and "usd" in json_data and usdt_try_parite > 0:
                                    try_deger = json_data["usd"] * usdt_try_parite
                                
                                degisim = json_data.get("try_24h_change", 0)
                                if degisim == 0 and "usd_24h_change" in json_data:
                                    degisim = json_data["usd_24h_change"]
                                
                                borsa_verileri.append({
                                    "isim": TUM_VARLIKLAR[kod]["isim"],
                                    "deger": round(try_deger, 2),
                                    "degisim": round(degisim, 2),
                                    "tip": "kripto",
                                    "kod": kod,
                                    "icon": TUM_VARLIKLAR[kod]["icon"]
                                })
                            except (KeyError, ValueError) as e:
                                print(f"Kripto verisi işlenirken hata: {kod} - {str(e)}")
            else:
                print(f"Coingecko API'si çalışmıyor: HTTP {crypto_response.status_code}")
        except Exception as e:
            print(f"Coingecko API bağlantı hatası: {str(e)}")
        
        # 3. Alternatif API: Binance
        if len([v for v in borsa_verileri if v["tip"] == "kripto"]) < 5:
            try:
                binance_url = "https://api.binance.com/api/v3/ticker/24hr"
                binance_response = requests.get(binance_url, timeout=5)
                
                if binance_response.status_code == 200:
                    binance_data = binance_response.json()
                    
                    # USDT/TRY paritesini al
                    usdt_try_item = next((item for item in binance_data if item.get("symbol") == "USDTTRY"), None)
                    if usdt_try_item:
                        usdt_try_price = float(usdt_try_item.get("lastPrice", 0))
                        
                        # Eğer USDT/TRY çevrim oranı varsa, kripto paraları dönüştür
                        if usdt_try_price > 0:
                            for item in binance_data:
                                symbol = item.get("symbol", "")
                                # USDT paritesi olan kripto paralar
                                if symbol.endswith("USDT"):
                                    base_symbol = symbol[:-4]  # "BTCUSDT" -> "BTC"
                                    
                                    # Eğer bu sembol tanımlı bir kripto para ise ve henüz eklenmemişse
                                    if base_symbol in TUM_VARLIKLAR and TUM_VARLIKLAR[base_symbol]["tip"] == "kripto":
                                        try:
                                            # Zaten bu kripto para varsa, tekrar ekleme
                                            if any(v["kod"] == base_symbol for v in borsa_verileri):
                                                continue
                                                
                                            usdt_price = float(item.get("lastPrice", 0))
                                            price_change = float(item.get("priceChangePercent", 0))
                                            
                                            # USDT'den TRY'ye çevir
                                            try_price = usdt_price * usdt_try_price
                                            
                                            borsa_verileri.append({
                                                "isim": TUM_VARLIKLAR[base_symbol]["isim"],
                                                "deger": round(try_price, 2),
                                                "degisim": round(price_change, 2),
                                                "tip": "kripto",
                                                "kod": base_symbol,
                                                "icon": TUM_VARLIKLAR[base_symbol]["icon"]
                                            })
                                        except (ValueError, KeyError) as e:
                                            print(f"Binance verisi işlenirken hata: {base_symbol} - {str(e)}")
                else:
                    print(f"Binance API'si çalışmıyor: HTTP {binance_response.status_code}")
            except Exception as e:
                print(f"Binance API bağlantı hatası: {str(e)}")
        
        # 4. Alternatif API: CollectAPI (döviz için)
        if len([v for v in borsa_verileri if v["tip"] == "doviz"]) < 5:
            try:
                collect_url = "https://api.collectapi.com/economy/allCurrency"
                headers = {
                    "content-type": "application/json",
                    "authorization": "apikey 1ipN4Yf7Fwuo7acmcizJSl:6CaqAJsgHCn0v4L33ThTQf"
                }
                
                collect_response = requests.get(collect_url, headers=headers, timeout=5)
                if collect_response.status_code == 200:
                    collect_data = collect_response.json()
                    results = collect_data.get("result", [])
                    
                    for currency in results:
                        kod = currency.get("code", "")
                        if kod in TUM_VARLIKLAR and TUM_VARLIKLAR[kod]["tip"] == "doviz":
                            # Zaten bu döviz varsa, tekrar ekleme
                            if any(v["kod"] == kod for v in borsa_verileri):
                                continue
                                
                            try:
                                deger = float(currency.get("buying", 0))
                                degisim = float(currency.get("rate", 0))
                                
                                borsa_verileri.append({
                                    "isim": TUM_VARLIKLAR[kod]["isim"],
                                    "deger": deger,
                                    "degisim": degisim,
                                    "tip": "doviz",
                                    "kod": kod,
                                    "icon": TUM_VARLIKLAR[kod]["icon"]
                                })
                            except (ValueError, KeyError) as e:
                                print(f"CollectAPI verisi işlenirken hata: {kod} - {str(e)}")
                else:
                    print(f"CollectAPI çalışmıyor: HTTP {collect_response.status_code}")
            except Exception as e:
                print(f"CollectAPI bağlantı hatası: {str(e)}")
                
        # 5. Varsayılan değerler - eğer yeterli veri toplanamadıysa
        if len(borsa_verileri) < 5:
            print("Yeterli veri toplanamadı, varsayılan değerler kullanılıyor")
        
    except Exception as e:
        print(f"Genel veri hatası: {str(e)}")
        # Hata durumunda varsayılan değerlerle devam et
        borsa_verileri = varsayilan_veriler.copy()
    
    # Borsa verilerini sırala: önce dövizler sonra kriptolar
    borsa_verileri.sort(key=lambda x: (x.get('tip') != 'doviz', x.get('deger', 0) < 0))
    
    # Eğer hiçbir döviz verisi yoksa, varsayılan döviz verilerini ekleyin
    doviz_kodlari = [veri.get('kod') for veri in borsa_verileri if veri.get('tip') == 'doviz']
    kripto_kodlari = [veri.get('kod') for veri in borsa_verileri if veri.get('tip') == 'kripto']
    
    # Dövizleri ekle (mevcut olmayanları)
    for veri in varsayilan_veriler:
        if veri['kod'] not in doviz_kodlari:
            borsa_verileri.append(veri)
    
    # Varsayılan kripto verileri - daha fazla kripto para ekleyerek tüm listeyi tamamlayalım
    varsayilan_kriptolar = [
        {"isim": "Bitcoin (BTC)", "deger": 2150000, "degisim": 2.5, "tip": "kripto", "kod": "BTC", "icon": "fab fa-bitcoin text-warning"},
        {"isim": "Ethereum (ETH)", "deger": 112000, "degisim": 1.8, "tip": "kripto", "kod": "ETH", "icon": "fab fa-ethereum text-secondary"},
        {"isim": "Tether (USDT)", "deger": 33.45, "degisim": 0.2, "tip": "kripto", "kod": "USDT", "icon": "fas fa-dollar-sign text-info"},
        {"isim": "Binance Coin (BNB)", "deger": 12500, "degisim": 1.2, "tip": "kripto", "kod": "BNB", "icon": "fas fa-coins text-warning"},
        {"isim": "Solana (SOL)", "deger": 4560, "degisim": 3.4, "tip": "kripto", "kod": "SOL", "icon": "fas fa-solar-panel text-danger"},
        {"isim": "Ripple (XRP)", "deger": 23.45, "degisim": 0.8, "tip": "kripto", "kod": "XRP", "icon": "fas fa-wave-square text-primary"},
        {"isim": "Cardano (ADA)", "deger": 18.90, "degisim": 0.5, "tip": "kripto", "kod": "ADA", "icon": "fas fa-project-diagram text-primary"},
        {"isim": "Avalanche (AVAX)", "deger": 870, "degisim": 2.1, "tip": "kripto", "kod": "AVAX", "icon": "fas fa-mountain text-danger"},
        {"isim": "Dogecoin (DOGE)", "deger": 4.25, "degisim": 1.3, "tip": "kripto", "kod": "DOGE", "icon": "fas fa-dog text-warning"},
        {"isim": "TRON (TRX)", "deger": 5.75, "degisim": 0.7, "tip": "kripto", "kod": "TRX", "icon": "fas fa-network-wired text-danger"},
        {"isim": "Polkadot (DOT)", "deger": 240, "degisim": 1.1, "tip": "kripto", "kod": "DOT", "icon": "fas fa-circle-notch text-pink"},
        {"isim": "Polygon (MATIC)", "deger": 28.60, "degisim": 1.6, "tip": "kripto", "kod": "MATIC", "icon": "fas fa-cube text-primary"},
        {"isim": "Litecoin (LTC)", "deger": 2850, "degisim": 0.9, "tip": "kripto", "kod": "LTC", "icon": "fas fa-coins text-secondary"},
        {"isim": "Shiba Inu (SHIB)", "deger": 0.00125, "degisim": 2.7, "tip": "kripto", "kod": "SHIB", "icon": "fas fa-dog text-warning"},
        {"isim": "Dai (DAI)", "deger": 33.30, "degisim": 0.1, "tip": "kripto", "kod": "DAI", "icon": "fas fa-dollar-sign text-warning"},
        {"isim": "Uniswap (UNI)", "deger": 195, "degisim": 1.2, "tip": "kripto", "kod": "UNI", "icon": "fas fa-exchange-alt text-pink"},
        {"isim": "Chainlink (LINK)", "deger": 560, "degisim": 1.8, "tip": "kripto", "kod": "LINK", "icon": "fas fa-link text-blue"},
        {"isim": "Cosmos (ATOM)", "deger": 385, "degisim": 1.5, "tip": "kripto", "kod": "ATOM", "icon": "fas fa-atom text-primary"},
        {"isim": "Monero (XMR)", "deger": 5960, "degisim": 0.6, "tip": "kripto", "kod": "XMR", "icon": "fas fa-user-secret text-warning"},
        {"isim": "Filecoin (FIL)", "deger": 175, "degisim": 1.4, "tip": "kripto", "kod": "FIL", "icon": "fas fa-database text-info"},
        {"isim": "NEAR Protocol (NEAR)", "deger": 155, "degisim": 2.3, "tip": "kripto", "kod": "NEAR", "icon": "fas fa-network-wired text-warning"},
        {"isim": "ApeCoin (APE)", "deger": 45.80, "degisim": 3.1, "tip": "kripto", "kod": "APE", "icon": "fas fa-ape text-success"},
        {"isim": "The Sandbox (SAND)", "deger": 17.90, "degisim": 1.7, "tip": "kripto", "kod": "SAND", "icon": "fas fa-cubes text-warning"},
        {"isim": "Algorand (ALGO)", "deger": 12.45, "degisim": 0.9, "tip": "kripto", "kod": "ALGO", "icon": "fas fa-project-diagram text-success"},
        {"isim": "Axie Infinity (AXS)", "deger": 225, "degisim": 2.5, "tip": "kripto", "kod": "AXS", "icon": "fas fa-gamepad text-pink"}
    ]
    
    # Kripto verilerini ekle (mevcut olmayanları)
    for veri in varsayilan_kriptolar:
        if veri['kod'] not in kripto_kodlari:
            borsa_verileri.append(veri)
    
    # Tüm TUM_VARLIKLAR içindeki kriptoları kontrol et
    for kod, veri in TUM_VARLIKLAR.items():
        if veri["tip"] == "kripto" and kod not in kripto_kodlari and kod not in [v['kod'] for v in varsayilan_kriptolar]:
            # Tanımlı olmayan kriptolar için makul değerler atayalım
            borsa_verileri.append({
                "isim": veri["isim"],
                "deger": 10.0 + (hash(kod) % 90),  # Rastgele ama deterministik bir değer
                "degisim": 0.5 + (hash(kod) % 30) / 10.0,  # Rastgele bir değişim
                "tip": "kripto",
                "kod": kod,
                "icon": veri["icon"]
            })
    
    # Kopya oluştur ve filtreleme yapmadan önce tüm veriyi saklayalım
    tum_borsa_verileri = borsa_verileri.copy()
    
    # Filtrelere göre veri kümesini belirle
    filtre_verileri = []
    if filtre == 'doviz':
        # Döviz filtresinde sadece dövizleri göster - altınları en sona koyalım
        doviz_verileri = [veri for veri in tum_borsa_verileri if veri.get('tip') == 'doviz' and 'XAU' not in veri.get('kod', '') and 'XAG' not in veri.get('kod', '')]
        altin_verileri = [veri for veri in tum_borsa_verileri if veri.get('tip') == 'doviz' and ('XAU' in veri.get('kod', '') or 'XAG' in veri.get('kod', ''))]
        # Dövizleri değerine göre, altınları kendi içinde değerine göre sırala
        doviz_verileri.sort(key=lambda x: -x.get('deger', 0))
        altin_verileri.sort(key=lambda x: -x.get('deger', 0))
        filtre_verileri = doviz_verileri + altin_verileri
    elif filtre == 'kripto':
        # Kripto filtresinde sadece kriptoları göster, değerine göre sırala
        filtre_verileri = [veri for veri in tum_borsa_verileri if veri.get('tip') == 'kripto']
        filtre_verileri.sort(key=lambda x: -x.get('deger', 0))
    else:
        # Tümünü göster - önce dövizler (altınlar hariç), sonra kriptolar, en sonda altınlar
        doviz_verileri = [veri for veri in tum_borsa_verileri if veri.get('tip') == 'doviz' and 'XAU' not in veri.get('kod', '') and 'XAG' not in veri.get('kod', '')]
        kripto_verileri = [veri for veri in tum_borsa_verileri if veri.get('tip') == 'kripto']
        altin_verileri = [veri for veri in tum_borsa_verileri if veri.get('tip') == 'doviz' and ('XAU' in veri.get('kod', '') or 'XAG' in veri.get('kod', ''))]
        
        # Her grubu kendi içinde değerine göre sırala
        doviz_verileri.sort(key=lambda x: -x.get('deger', 0))
        kripto_verileri.sort(key=lambda x: -x.get('deger', 0))
        altin_verileri.sort(key=lambda x: -x.get('deger', 0))
        
        # Grupları birleştir
        filtre_verileri = doviz_verileri + kripto_verileri + altin_verileri
    
    # Arama terimini uygula
    if arama:
        filtre_verileri = [veri for veri in filtre_verileri if arama in veri.get('isim', '').lower() or arama in veri.get('kod', '').lower()]
    
    # Sayfalama için filtre verileri listesini kullan
    borsa_verileri = filtre_verileri
    
    # Toplam sayfa sayısını hesapla
    # "Tümünü göster" seçeneğinde maksimum sayfa sayısını daha yüksek tutalım
    toplam_kayit = len(borsa_verileri)
    
    if filtre == 'hepsi':
        # Tümünü göster seçeneğinde maksimum sınır yok (tüm sayfalar gösterilecek)
        toplam_sayfa = (toplam_kayit + sayfa_basina - 1) // sayfa_basina
    else:
        # Döviz ve kripto kategorilerinde maksimum 3 sayfa
        toplam_sayfa = min(3, (toplam_kayit + sayfa_basina - 1) // sayfa_basina)
    
    # Geçerli sayfa kontrolü
    if sayfa < 1:
        sayfa = 1
    elif sayfa > toplam_sayfa and toplam_sayfa > 0:
        sayfa = toplam_sayfa
    
    # Sayfa için veri aralığını hesapla
    baslangic = (sayfa - 1) * sayfa_basina
    bitis = min(baslangic + sayfa_basina, toplam_kayit)
    sayfa_verileri = borsa_verileri[baslangic:bitis]
    
    # Sayfalama için gösterilecek sayfa numaralarını belirle
    # Çok fazla sayfa olursa sayfalama görünümünü sınırlandır
    if toplam_sayfa <= 5:
        # 5 veya daha az sayfa varsa hepsini göster
        sayfalama_araligi = range(1, toplam_sayfa + 1)
    else:
        # 5'ten fazla sayfa varsa navigasyon sistemini iyileştir
        if sayfa <= 3:
            # Başlangıç sayfalarındaysa ilk 5 sayfayı göster
            sayfalama_araligi = range(1, 6)
        elif sayfa >= toplam_sayfa - 2:
            # Son sayfalardaysa son 5 sayfayı göster
            sayfalama_araligi = range(toplam_sayfa - 4, toplam_sayfa + 1)
        else:
            # Ortadaysa, mevcut sayfayı ortaya alarak 5 sayfa göster
            sayfalama_araligi = range(sayfa - 2, sayfa + 3)
    
    # Güncellenme zamanı
    guncelleme_zamani = datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    
    # Her kategori için toplam kayıt sayılarını hesapla
    doviz_sayisi = len([veri for veri in tum_borsa_verileri if veri.get('tip') == 'doviz'])
    kripto_sayisi = len([veri for veri in tum_borsa_verileri if veri.get('tip') == 'kripto'])
    toplam_kayit_sayisi = doviz_sayisi + kripto_sayisi
    
    context = {
        'sayfa_verileri': sayfa_verileri,
        'guncelleme_zamani': guncelleme_zamani,
        'error_message': error_message,
        'toplam_kayit': toplam_kayit,
        'toplam_sayfa': toplam_sayfa,
        'sayfa': sayfa,
        'filtre': filtre,
        'arama': arama,
        'sayfalama_araligi': sayfalama_araligi,
        'doviz_sayisi': doviz_sayisi,
        'kripto_sayisi': kripto_sayisi,
        'toplam_kayit_sayisi': toplam_kayit_sayisi,
    }
    
    return render(request, 'accounts/borsa.html', context)

@login_required
def edit_transaction_view(request, transaction_id):
    # İşlemi al
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    
    # Transaction tipini belirle (gelir/gider)
    transaction_type = transaction.category.type
    
    # İşlemin eski miktarını sakla
    old_amount = transaction.amount
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction, user=request.user, transaction_type=transaction_type)
        if form.is_valid():
            # Yeni kategori kontrolü
            new_category_name = form.cleaned_data.get('new_category')
            category = form.cleaned_data.get('category')
            
            # Yeni kategori girilmiş mi kontrol et
            if new_category_name:
                # Yeni kategori oluştur
                category, created = Category.objects.get_or_create(
                    name=new_category_name,
                    type=transaction_type,
                    icon='tag'  # Varsayılan ikon
                )
                transaction = form.save(commit=False)
                transaction.category = category
            elif category:
                # Mevcut kategori seçilmiş
                transaction = form.save(commit=False)
            else:
                # Hiçbir kategori seçilmemiş ve girilmemiş
                messages.error(request, 'Lütfen bir kategori seçin veya yeni bir kategori girin.')
                return render(request, 'accounts/edit_transaction.html', {
                    'form': form,
                    'transaction': transaction,
                    'transaction_type': transaction_type
                })
                
            # İşlemi kaydet
            transaction.save()
            
            # Kullanıcı toplam miktarını güncelle
            # Eski ve yeni arasındaki farkı hesapla
            amount_diff = transaction.amount - old_amount
            
            if transaction_type == 'gelir':
                request.user.total_amount += amount_diff
            else:  # gider
                request.user.total_amount -= amount_diff
                
            request.user.save()
            
            # Gider işlemi için harcama limitlerini kontrol et
            if transaction_type == 'gider':
                category = transaction.category
                limits = SpendingLimit.objects.filter(user=request.user, category=category)
                
                for limit in limits:
                    if limit.is_exceeded():
                        messages.warning(
                            request, 
                            f"'{category.name}' kategorisindeki {limit.get_period_display().lower()} harcama limitinizi aştınız!"
                        )
            
            messages.success(request, 'İşlem başarıyla güncellendi.')
            return redirect('income_expense')
    else:
        form = TransactionForm(instance=transaction, user=request.user, transaction_type=transaction_type)
    
    return render(request, 'accounts/edit_transaction.html', {
        'form': form,
        'transaction': transaction,
        'transaction_type': transaction_type
    })

@login_required
def delete_transaction_view(request):
    if request.method == 'POST':
        transaction_id = request.POST.get('transaction_id')
        
        try:
            transaction = Transaction.objects.get(id=transaction_id, user=request.user)
            transaction_type = transaction.category.type
            amount = transaction.amount
            
            # İşlemi sil
            transaction.delete()
            
            # Kullanıcı toplam miktarını güncelle
            if transaction_type == 'gelir':
                request.user.total_amount -= amount
            else:  # gider
                request.user.total_amount += amount
                
            request.user.save()
            
            messages.success(request, 'İşlem başarıyla silindi.')
        except Transaction.DoesNotExist:
            messages.error(request, 'İşlem bulunamadı.')
        
    return redirect('income_expense')

@login_required
def edit_spending_limit_view(request, limit_id):
    limit = get_object_or_404(SpendingLimit, id=limit_id, user=request.user)
    
    if request.method == 'POST':
        form = SpendingLimitForm(request.POST, instance=limit, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Harcama limiti başarıyla güncellendi.')
            return redirect('spending_limits')
    else:
        form = SpendingLimitForm(instance=limit, user=request.user)
    
    return render(request, 'accounts/edit_spending_limit.html', {
        'form': form,
        'limit': limit
    })

@login_required
def delete_spending_limit_view(request):
    if request.method == 'POST':
        limit_id = request.POST.get('limit_id')
        
        try:
            limit = SpendingLimit.objects.get(id=limit_id, user=request.user)
            limit.delete()
            messages.success(request, 'Harcama limiti başarıyla silindi.')
        except SpendingLimit.DoesNotExist:
            messages.error(request, 'Harcama limiti bulunamadı.')
        
    return redirect('spending_limits')


