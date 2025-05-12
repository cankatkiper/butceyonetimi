from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Category, Transaction, SavingGoal, PurchaseGoal, SpendingLimit
from django.utils import timezone

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Bu e-posta adresi zaten kullanılıyor.')
        return email

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='E-posta veya Kullanıcı Adı', widget=forms.TextInput(attrs={'autocomplete': 'off'}))
    password = forms.CharField(label='Şifre', widget=forms.PasswordInput)

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label='E-posta')

class SetNewPasswordForm(forms.Form):
    password1 = forms.CharField(label='Yeni Şifre', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Yeni Şifre (Tekrar)', widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Şifreler eşleşmiyor.')

class FinancialInfoForm(forms.Form):
    total_amount = forms.DecimalField(
        label='Toplam Paranız',
        decimal_places=2,
        max_digits=15,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Toplam paranızı girin'})
    )

class TransactionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        transaction_type = kwargs.pop('transaction_type', None)
        super(TransactionForm, self).__init__(*args, **kwargs)
        
        if transaction_type:
            self.fields['category'].queryset = Category.objects.filter(type=transaction_type)
            
        # Kategori alanının zorunluluğunu kaldır
        self.fields['category'].required = False
            
        # Yeni Kategori alanı ekleniyor
        self.fields['new_category'] = forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Yeni kategori adı',
                'oninput': 'toggleCategoryField(this)'
            }),
            label='Yeni Kategori Ekle'
        )
        
        # Kategori alanı
        self.fields['category'].widget.attrs.update({
            'oninput': 'toggleNewCategoryField(this)',
            'class': 'form-select'
        })
    
    class Meta:
        model = Transaction
        fields = ['category', 'amount', 'description', 'date', 'is_regular']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_regular': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'category': 'Kategori',
            'amount': 'Miktar',
            'description': 'Açıklama',
            'date': 'Tarih',
            'is_regular': 'Düzenli mi?',
        }

class SavingGoalForm(forms.ModelForm):
    class Meta:
        model = SavingGoal
        fields = ['name', 'target_amount', 'target_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'target_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'target_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'name': 'Hedef Adı',
            'target_amount': 'Hedef Miktar',
            'target_date': 'Hedef Tarih',
        }
    
    def clean_target_date(self):
        target_date = self.cleaned_data.get('target_date')
        if target_date and target_date < timezone.now().date():
            raise forms.ValidationError('Geçmiş bir tarih seçemezsiniz.')
        return target_date

class PurchaseGoalForm(forms.ModelForm):
    class Meta:
        model = PurchaseGoal
        fields = ['name', 'price', 'trigger_percentage']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'trigger_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'name': 'Ürün Adı',
            'price': 'Ürün Fiyatı',
            'trigger_percentage': 'Tetikleme Yüzdesi (%)',
        }
    
    def clean_trigger_percentage(self):
        trigger_percentage = self.cleaned_data.get('trigger_percentage')
        if trigger_percentage and (trigger_percentage < 0 or trigger_percentage > 100):
            raise forms.ValidationError('Tetikleme yüzdesi 0 ile 100 arasında olmalıdır.')
        return trigger_percentage

class SpendingLimitForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(SpendingLimitForm, self).__init__(*args, **kwargs)
        
        if user:
            self.fields['category'].queryset = Category.objects.filter(type='gider')
    
    class Meta:
        model = SpendingLimit
        fields = ['category', 'amount', 'period']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'period': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'category': 'Kategori',
            'amount': 'Limit Miktarı',
            'period': 'Periyot',
        }
