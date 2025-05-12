# Financial Core

Bu Django uygulaması, finansal yönetim sistemleri için yeniden kullanılabilir bileşenler sağlar.

## Özellikler

- Soyut model sınıfları (BaseModel, AbstractTransaction, AbstractSpendingLimit, AbstractSavingGoal)
- Kategori modeli için temel sınıf (FinancialCategory)
- Yeniden kullanılabilir form mixinleri
- View mixinleri (CRUD işlemleri için)
- Finansal hesaplamalar için utility fonksiyonları

## Kurulum

1. Uygulamayı Django projenize ekleyin:

```bash
pip install django-financial-core  # henüz yayınlanmadı
```

veya doğrudan projenize kopyalayın ve INSTALLED_APPS'e ekleyin:

```python
INSTALLED_APPS = [
    ...
    'financial_core',
    ...
]
```

## Kullanım Örnekleri

### Modeller

```python
from financial_core.models import BaseModel, AbstractTransaction, FinancialCategory

# Kategori modeli
class Category(FinancialCategory):
    # Ek alanlar ekleyebilirsiniz
    color = models.CharField(max_length=7, blank=True, null=True)

# İşlem modeli
class Transaction(AbstractTransaction):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='transactions')
```

### Formlar

```python
from django import forms
from financial_core.forms import TransactionFormMixin
from .models import Transaction

class TransactionForm(TransactionFormMixin, forms.ModelForm):
    class Meta(TransactionFormMixin.Meta):
        model = Transaction
```

### Utility Fonksiyonları

```python
from financial_core.utils import get_monthly_data, get_category_summary

# Son 6 ayın gelir/gider toplamları
chart_data = get_monthly_data(Transaction.objects.filter(user=request.user))

# Kategorilere göre harcamalar
category_summary = get_category_summary(Transaction.objects.filter(user=request.user))
```

### View Mixinler

```python
from django.views.generic import CreateView
from financial_core.mixins import TransactionCreateMixin
from .models import Transaction
from .forms import TransactionForm

class IncomeCreateView(TransactionCreateMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'income_form.html'
    success_url = '/transactions/'
    transaction_type = 'gelir'
    
    def update_user_total(self, transaction):
        # Gelir eklendiğinde kullanıcı bakiyesini güncelle
        transaction.user.balance += transaction.amount
        transaction.user.save()
```

## Entegrasyon

Mevcut finansal sistemlere entegre etmek için şunları yapmalısınız:

1. Kendi modellerinizi financial_core'daki soyut modellerden türetin
2. Form ve View sınıflarınızı ilgili mixinlerden türetin
3. İhtiyaç duyduğunuz utility fonksiyonlarını projenizde kullanın

## Katkıda Bulunma

Sorunları ve özellik isteklerini GitHub üzerinden bildirebilirsiniz. Pull Request'ler her zaman açıktır. 