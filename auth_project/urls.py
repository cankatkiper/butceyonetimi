from django.contrib import admin
from django.urls import path, include
from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', accounts_views.dashboard_view, name='dashboard'),
    path('register/', accounts_views.register_view, name='register'),
    path('login/', accounts_views.login_view, name='login'),
    path('logout/', accounts_views.logout_view, name='logout'),
    path('financial-info/', accounts_views.financial_info_view, name='financial_info'),
    path('password-reset/', accounts_views.password_reset_request, name='password_reset_request'),
    path('reset-password/<uuid:token>/', accounts_views.password_reset_confirm, name='password_reset_confirm'),
    
    # Para Sekreterim uygulama URL'leri
    path('gelir-gider/', accounts_views.income_expense_view, name='income_expense'),
    path('gelir-ekle/', accounts_views.add_income_view, name='add_income'),
    path('gider-ekle/', accounts_views.add_expense_view, name='add_expense'),
    path('hedefler/', accounts_views.goals_view, name='goals'),
    path('tasarruf-hedefi-ekle/', accounts_views.add_saving_goal_view, name='add_saving_goal'),
    path('satin-alma-hedefi-ekle/', accounts_views.add_purchase_goal_view, name='add_purchase_goal'),
    path('harcama-limitleri/', accounts_views.spending_limits_view, name='spending_limits'),
    path('limit-ekle/', accounts_views.add_spending_limit_view, name='add_spending_limit'),
    path('raporlar/', accounts_views.reports_view, name='reports'),
    path('ayarlar/', accounts_views.settings_view, name='settings'),
]
