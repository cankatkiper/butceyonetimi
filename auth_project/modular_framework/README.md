# Modular Framework

Yeniden kullanılabilir, modüler ve bağımsız Django bileşenleri çerçevesi.

## Genel Bakış

Modular Framework, Django projelerinde yeniden kullanılabilecek modüler ve bağımsız bileşenler sunar. Her modül, kendi amacına uygun şekilde organize edilmiştir ve diğer projeler tarafından kolayca kullanılabilir.

## Modüller

### Core
Temel sınıflar ve yapılar içerir. Diğer modüller tarafından kullanılan çekirdek fonksiyonellik burada bulunur.

### Utils
Yardımcı işlevler ve araçlar içerir. Tarih/saat işlemleri, döviz çevirici, sayı biçimlendirme vb. yardımcı fonksiyonlar bulunur.

### Mixins
Yeniden kullanılabilir mixin sınıfları içerir. View, model ve form sınıfları için genişletilebilir mixin'ler burada tanımlanır.

### Abstract Models
Soyut model sınıfları içerir. BaseModel, AbstractTransaction gibi temel model yapıları burada tanımlanır.

### Helpers
Yardımcı fonksiyonlar ve sınıflar içerir. Formlar, görünümler veya modeller için yardımcı işlevler burada bulunur.

### Services
Servis sınıflarını barındırır. Finansal hesaplamalar, API istekleri, veri işleme hizmetleri gibi karmaşık işlemler için servis sınıfları burada tanımlanır.

### Decorators
Dekoratör fonksiyonları içerir. Önbelleğe alma, kimlik doğrulama, izleme gibi işlemler için dekoratörler burada tanımlanır.

### Validators
Doğrulayıcı fonksiyonları ve sınıfları içerir. E-posta doğrulama, sayı aralığı kontrolü gibi işlemler için doğrulayıcılar burada tanımlanır.

## Kurulum

```bash
# modular_framework paketini projenize kopyalayın
cp -r modular_framework /path/to/your/django/project/

# settings.py dosyasına ekleyin
INSTALLED_APPS = [
    ...
    'modular_framework.core',
]
```

## Kullanım Örnekleri

### Soyut Modeller

```python
from modular_framework.abstract_models import BaseModel

class MyModel(BaseModel):
    name = models.CharField(max_length=100)
    # BaseModel zaten created_at ve updated_at alanlarına sahip
```

### Mixinler

```python
from modular_framework.mixins import TransactionCreateMixin
from django.views.generic import CreateView

class TransactionCreateView(TransactionCreateMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    success_url = reverse_lazy('transactions')
```

### Yardımcı Fonksiyonlar

```python
from modular_framework.utils.date_utils import get_month_start_end
from modular_framework.utils.finance_utils import format_currency

# Ayın başlangıç ve bitiş tarihlerini al
start_date, end_date = get_month_start_end(2023, 5)

# Para birimini biçimlendir
formatted_amount = format_currency(1234.56)  # "1.234,56 ₺"
```

### Dekoratörler

```python
from modular_framework.decorators import ajax_login_required, simple_cache

@ajax_login_required
def my_ajax_view(request):
    # Bu view AJAX istekleri için özel kimlik doğrulama yapar
    return JsonResponse({'status': 'success'})

@simple_cache(timeout=3600)  # 1 saat önbelleğe al
def expensive_operation():
    # Bu fonksiyon sonuçları önbelleğe alınacak
    return complex_calculation()
```

### Servisler

```python
from modular_framework.services import ExchangeRateService, FinancialCalculator

# Döviz kurları servisi
exchange_service = ExchangeRateService()
rates = exchange_service.get_latest_rates('USD')

# Finansal hesaplamalar
calculator = FinancialCalculator()
future_value = calculator.calculate_compound_interest(1000, 0.05, 10)
```

### Doğrulayıcılar

```python
from modular_framework.validators import validate_turkish_identity_number, validate_secure_password

class MyForm(forms.Form):
    identity_number = forms.CharField(validators=[validate_turkish_identity_number])
    password = forms.CharField(widget=forms.PasswordInput, validators=[validate_secure_password])
```

## Katkıda Bulunma

1. Bu repo'yu fork edin
2. Yeni bir branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some amazing feature'`)
4. Branch'inize push edin (`git push origin feature/amazing-feature`)
5. Pull request açın

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır - Detaylar için [LICENSE](LICENSE) dosyasına bakın. 