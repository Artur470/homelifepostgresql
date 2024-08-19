from rest_framework import serializers
from .models import *


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ["title"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["title"]


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["title"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    color = ColorSerializer(read_only=True)
    brand = BrandSerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'title',
            'category',
            'color',
            'image',
            'price',
            'promotion',
            'brand',
            'quantity',
            'description',
            'is_product_of_the_day'
        ]

    def create(self, validated_data):
        category_data = validated_data.pop('category')
        color_data = validated_data.pop('color')
        brand_data = validated_data.pop('brand')

        category_instance, _ = Category.objects.get_or_create(**category_data)
        color_instance, _ = Color.objects.get_or_create(**color_data)
        brand_instance, _ = Brand.objects.get_or_create(**brand_data)

        product = Product.objects.create(
            category=category_instance,
            color=color_instance,
            brand=brand_instance,
            **validated_data

        )

        return product


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id',
            'title',
            'category',
            'color',
            'image',
            'price',
            'promotion',
            'brand',
            'quantity',
            'description',
            'is_product_of_the_day'
        ]
