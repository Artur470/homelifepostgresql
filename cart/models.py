from django.db import models
from django.conf import settings
from product.models import Product
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from decimal import Decimal
import uuid
class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    id = models.BigAutoField(primary_key=True)  # Обновлено на BigAutoField
    def __str__(self):
        return f"{self.user.first_name} - {self.total_price:.2f}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    promotion = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    isOrder = models.BooleanField(default=False)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.user.first_name} - {self.product.title}"

    def save(self, *args, **kwargs):
        product = self.product
        quantity = self.quantity

        # Вычисляем цену с учетом промо-акции
        if product.promotion:
            self.price = Decimal(product.promotion) * quantity
        else:
            self.price = Decimal(product.price) * quantity

        super().save(*args, **kwargs)

@receiver(post_save, sender=CartItem)
def update_cart_total(sender, instance, **kwargs):
    cart = instance.cart
    total_price = sum(item.price for item in cart.items.all())
    cart.total_price = total_price
    cart.save()
# Order Models
class PaymentMethod(models.Model):
    name = models.CharField(max_length=50)  # Например: "Card", "Cash", "Bank Transfer"
    description = models.TextField(blank=True, null=True)  # Дополнительное описание (по желанию)

    def __str__(self):
        return self.name

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    payment_method = models.ForeignKey(PaymentMethod, null=True, blank=True, on_delete=models.SET_NULL)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # Используем DecimalField для точности
    address = models.CharField(max_length=255)
    ordered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.email}"

    def clear_user_cart(self):
        # Очистите корзину пользователя
        cart_items = self.cart.items.all()
        cart_items.delete()
        self.cart.total_price = Decimal('0.00')
        self.cart.save()

    def send_order_email(self):
        subject = 'Новый заказ!'
        message = f'Номер заказа: {self.id}\n' \
                  f'Email Пользователя: {self.user.email}\n' \
                  f'Имя пользователя: {self.user.first_name} {self.user.last_name}\n' \
                  f'Адрес: {self.address}\n' \
                  f'Способ оплаты: {self.payment_method.name if self.payment_method else "Не указан"}\n' \
                  f'Цена: {self.total_price:.2f}\n' \
                  f'Время заказа: {self.ordered_at}\n\n'

        if hasattr(self.user, 'wholesaler') and self.user.wholesaler:
            message += "Покупатель является оптовиком.\n\n"

        # Добавляем информацию о товарах
        items = self.cart.items.all()
        if items.exists():
            message += "Товары в заказе:\n"
            for item in items:
                message += f'Продукт: {item.product.title}\n' \
                           f'Категория: {item.product.category.title}\n' \
                           f'Цвет: {item.product.color.title}\n' \
                           f'Бренд: {item.product.brand.title}\n' \
                           f'Количество: {item.quantity}\n' \
                           f'Цена товара: {item.price:.2f}\n\n'
        else:
            message += "Корзина пуста."

        admin_email = 'homelife.site.kg@gmail.com'  # Замените на реальный email администратора
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [admin_email])
