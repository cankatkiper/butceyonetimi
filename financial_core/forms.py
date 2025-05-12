from django import forms
from django.utils import timezone

class CategoryFormMixin:
    """Kategori formları için mixin"""
    class Meta:
        fields = ['name', 'type', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control'}),
        }

class TransactionFormMixin:
    """İşlem formları için mixin"""
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        transaction_type = kwargs.pop('transaction_type', None)
        category_model = self._meta.model.category.field.related_model
        
        super(TransactionFormMixin, self).__init__(*args, **kwargs)
        
        if transaction_type and hasattr(self.fields, 'category'):
            self.fields['category'].queryset = category_model.objects.filter(type=transaction_type)
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
        if hasattr(self.fields, 'category'):
            self.fields['category'].widget.attrs.update({
                'oninput': 'toggleNewCategoryField(this)',
                'class': 'form-select'
            })
    
    class Meta:
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

class SpendingLimitFormMixin:
    """Harcama limiti formları için mixin"""
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        category_model = self._meta.model.category.field.related_model
        
        super(SpendingLimitFormMixin, self).__init__(*args, **kwargs)
        
        if user and hasattr(self.fields, 'category'):
            self.fields['category'].queryset = category_model.objects.filter(type='gider')
    
    class Meta:
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

class SavingGoalFormMixin:
    """Tasarruf hedefi formları için mixin"""
    def clean_target_date(self):
        target_date = self.cleaned_data.get('target_date')
        if target_date and target_date < timezone.now().date():
            raise forms.ValidationError('Geçmiş bir tarih seçemezsiniz.')
        return target_date
    
    class Meta:
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