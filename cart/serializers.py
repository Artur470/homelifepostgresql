from rest_framework import serializers
from .models import Cart, CartItem, Order, PaymentMethod
from product.serializers import ProductSerializer

class CartSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'total_price', 'ordered', 'user', 'items']

    def get_total_price(self, obj):
        return obj.total_price

    def get_items(self, obj):
        items = CartItem.objects.filter(cart=obj)
        return CartItemsSerializer(items, many=True).data

class CartItemsSerializer(serializers.ModelSerializer):
    cart_id = serializers.IntegerField(source='cart.id', read_only=True)
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    product = ProductSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = '__all__'

    def create(self, validated_data):
        cart = validated_data.get('cart')
        product = validated_data.get('product')
        quantity = validated_data.get('quantity')
        user = self.context['request'].user

        if product.quantity < quantity:
            raise serializers.ValidationError('Not enough stock available.')

            # Рассчитываем цену с учетом промо-акции
        price = Decimal(product.promotion) if product.promotion else Decimal(product.price)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity, 'price': price * quantity, 'user': user}
        )

        if not created:
            if product.quantity + cart_item.quantity < quantity:
                raise serializers.ValidationError('Not enough stock available.')

            product.quantity += cart_item.quantity - quantity
            product.save()

            cart_item.quantity = quantity
            cart_item.price = price * quantity
            cart_item.save()
        else:
            product.quantity -= quantity
            product.save()

        cart.total_price = sum(item.price for item in cart.items.all())
        cart.save()

        return cart_item

    def update(self, instance, validated_data):
        new_quantity = validated_data.get('quantity', instance.quantity)
        product = instance.product

        if new_quantity != instance.quantity:
            if product.quantity + instance.quantity < new_quantity:
                raise serializers.ValidationError('Not enough stock available.')

            product.quantity += instance.quantity - new_quantity
            product.save()

             # Рассчитываем цену с учетом промо-акции
            price = Decimal(product.promotion) if product.promotion else Decimal(product.price)

            instance.quantity = new_quantity
            instance.price = price * new_quantity
            instance.save()

            # Пересчитываем общую стоимость корзины
            cart = instance.cart
            cart.total_price = sum(item.price for item in cart.items.all())
            cart.save()

        return instance
class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name']


class OrderSerializer(serializers.ModelSerializer):
    payment_method = serializers.PrimaryKeyRelatedField(queryset=PaymentMethod.objects.all())

    class Meta:
        model = Order
        fields = ['user', 'cart', 'total_price', 'address', 'payment_method']
