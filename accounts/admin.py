from django.contrib import admin
from .models import CustomUser, PasswordResetToken, Category, Transaction, SavingGoal, PurchaseGoal, SpendingLimit

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_email_verified', 'financial_info_completed', 'total_amount')
    search_fields = ('username', 'email')
    list_filter = ('is_email_verified', 'financial_info_completed')

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'icon')
    list_filter = ('type',)
    search_fields = ('name',)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'amount', 'description', 'date', 'is_regular')
    list_filter = ('category', 'date', 'is_regular')
    search_fields = ('description', 'user__username')
    date_hierarchy = 'date'

class SavingGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'target_amount', 'current_amount', 'target_date')
    search_fields = ('name', 'user__username')
    list_filter = ('target_date', 'created_at')

class PurchaseGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'price', 'trigger_percentage', 'is_notified')
    search_fields = ('name', 'user__username')
    list_filter = ('is_notified', 'created_at')

class SpendingLimitAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'amount', 'period', 'start_date')
    search_fields = ('user__username', 'category__name')
    list_filter = ('period', 'start_date')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(PasswordResetToken)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(SavingGoal, SavingGoalAdmin)
admin.site.register(PurchaseGoal, PurchaseGoalAdmin)
admin.site.register(SpendingLimit, SpendingLimitAdmin)
