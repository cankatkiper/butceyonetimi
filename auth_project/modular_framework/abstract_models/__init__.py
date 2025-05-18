"""
Abstract Models (Soyut Modeller) Modülü

Bu modül, farklı uygulamalarda kullanılabilecek soyut model sınıflarını içerir.
BaseModel, AbstractTransaction gibi temel model yapıları burada tanımlanır.
"""

from .base import BaseModel
from .financial import (
    FinancialCategory,
    AbstractTransaction,
    AbstractSpendingLimit,
    AbstractSavingGoal
) 