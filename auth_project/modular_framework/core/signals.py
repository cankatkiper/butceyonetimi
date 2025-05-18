"""
Django Sinyalleri

Bu modül, Django sinyal bağlantılarını tanımlar.
Model kaydetme, silme gibi olaylar gerçekleştiğinde
tetiklenecek sinyal işleyiciler burada bulunur.
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
import logging

# Logger yapılandırması
logger = logging.getLogger(__name__)

# Sinyal işleyici fonksiyonları

@receiver(post_save, sender=get_user_model())
def user_created_handler(sender, instance, created, **kwargs):
    """
    Kullanıcı oluşturulduğunda çalıştırılacak sinyal işleyici.
    
    Args:
        sender: Sinyali gönderen model sınıfı
        instance: Kaydedilen model örneği
        created (bool): Yeni bir kayıt mı oluşturuldu?
        **kwargs: Ek parametreler
    """
    if created:
        logger.info(f"Yeni kullanıcı oluşturuldu: {instance.username}")
        
        # Burada yeni kullanıcı için tanımlama işlemleri yapılabilir
        # Örneğin: Varsayılan kategoriler oluşturulabilir, profil ayarları tanımlanabilir, vb.

# Diğer faydalı sinyal işleyici örnekleri

# Model değişikliklerini izleme örneği
def model_change_tracking(sender, instance, **kwargs):
    """
    Model değişikliklerini izleyen genel bir sinyal.
    
    Bu fonksiyonu receiver dekoratörü olmadan tanımlayıp,
    farklı modeller için ayrı ayrı kaydetmek üzere kullanabilirsiniz.
    
    Args:
        sender: Sinyali gönderen model sınıfı
        instance: Kaydedilen model örneği
        **kwargs: Ek parametreler
    """
    logger.debug(f"{sender.__name__} modeli güncellendi: {instance.pk}")

# İşlem sayısı değiştiğinde kullanıcı toplam miktarını güncelleme örneği
def update_user_total_amount(sender, instance, **kwargs):
    """
    İşlem kaydedildiğinde kullanıcı toplam miktarını günceller.
    
    Args:
        sender: Sinyali gönderen model sınıfı (Transaction modeli)
        instance: Kaydedilen model örneği (Transaction örneği)
        **kwargs: Ek parametreler
    """
    # Transaction modeli import edilmiş olmalı
    # Burada ilgili kodu kendi Transaction modeline uyarlamanız gerekir
    
    # Kullanıcının toplam miktarını güncelle
    # user = instance.user
    # if instance.category.type == 'gelir':
    #     user.total_amount += instance.amount
    # else:  # gider
    #     user.total_amount -= instance.amount
    # user.save()
    pass

# Harcama limitlerini kontrol etme örneği
def check_spending_limits(sender, instance, **kwargs):
    """
    Harcama işlemi kaydedildiğinde limitleri kontrol eder.
    
    Args:
        sender: Sinyali gönderen model sınıfı (Transaction modeli)
        instance: Kaydedilen model örneği (Transaction örneği)
        **kwargs: Ek parametreler
    """
    # SpendingLimit modeli import edilmiş olmalı
    # Burada ilgili kodu kendi Transaction ve SpendingLimit modellerine uyarlamanız gerekir
    
    # Harcama limitlerini kontrol et
    # if instance.category.type == 'gider':
    #     category = instance.category
    #     user = instance.user
    #     limits = SpendingLimit.objects.filter(user=user, category=category)
    #     
    #     for limit in limits:
    #         if limit.is_exceeded():
    #             logger.warning(f"Harcama limiti aşıldı: {user.username}, {category.name}")
    #             
    #             # Bildirim gönder
    #             Notification.objects.create(
    #                 user=user,
    #                 message=f"'{category.name}' kategorisindeki harcama limitinizi aştınız!",
    #                 level='warning'
    #             )
    pass

# Sinyalleri manuel olarak kaydetme örneği:
# pre_save.connect(check_spending_limits, sender=Transaction)
# post_save.connect(update_user_total_amount, sender=Transaction) 