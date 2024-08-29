from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.core.exceptions import ValidationError

from config import settings
from cloudinary.models import CloudinaryField
from decimal import Decimal, InvalidOperation


class Category(models.Model):
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title


class Brand(models.Model):
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title


class Color(models.Model):
    title = models.CharField(max_length=200)
    key = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.title

class Product(models.Model):
    title = models.CharField(max_length=255)
    image1 = models.ImageField(upload_to='images/', blank=True)
    image2 = models.ImageField(upload_to='images/', blank=True, null=True)
    image3 = models.ImageField(upload_to='images/', blank=True, null=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='products')
    color = models.ForeignKey('Color', on_delete=models.CASCADE, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Исправлено
    promotion = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Исправлено
    brand = models.ForeignKey('Brand', on_delete=models.CASCADE, related_name='products')
    quantity = models.IntegerField()
    description = models.TextField(max_length=255)
    is_product_of_the_day = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Review(models.Model):

    RATING_CHOICES = [
        (1, '1 star'),
        (1.5, '1.5 star'),
        (2, '2 star'),
        (2.5, '2.5 star'),
        (3, '3 star'),
        (3.5, '3.5 star'),
        (4, '4 star'),
        (4.5, '4.5 star'),
        (5, '5 star'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews", verbose_name="Product")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="User")
    comments = models.TextField(verbose_name="Comments", blank=True, null=True)
    rating = models.FloatField(
        choices=RATING_CHOICES,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ],
        verbose_name="Rating"
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date Created")
    updated = models.DateTimeField(auto_now=True, verbose_name="Date Updated")

    def clean(self):
        super().clean()  # Always call the parent class's `clean` method.
        # Дополнительная проверка на корректность рейтинга (можно убрать, если используется только choices)
        if self.rating not in dict(self.RATING_CHOICES).keys():
            raise ValidationError("Invalid rating value. It must be one of the predefined choices.")

    def __str__(self):
        return f'Review by {self.user} for {self.product} - Rating: {self.rating}'


class Banner(models.Model):
    image = models.ImageField(upload_to='images/')

    def __str__(self):
        return self.image
