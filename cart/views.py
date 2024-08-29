from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Cart, CartItem, Order
from product.models import Product
from .serializers import CartItemsSerializer, OrderSerializer
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        cart = Cart.objects.filter(user=user, ordered=False).first()
        if not cart:
            return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        user = request.user
        cart, _ = Cart.objects.get_or_create(user=user, ordered=False)

        product = get_object_or_404(Product, id=data.get('product'))
        quantity = int(data.get('quantity', 1))

        if quantity <= 0:
            return Response({'error': 'Quantity must be greater than 0'}, status=status.HTTP_400_BAD_REQUEST)

        if quantity > product.quantity:
            return Response({'error': 'Not enough stock available'}, status=status.HTTP_400_BAD_REQUEST)

        price = Decimal(product.promotion) if product.promotion else Decimal(product.price)
        logger.debug(f"Product ID: {product.id}, Price: {price}, Quantity: {quantity}")

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'price': price * quantity, 'quantity': quantity, 'user': user}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.price = price * cart_item.quantity
            cart_item.save()
        else:
            product.quantity -= quantity
            product.save()

        cart.total_price = sum(item.price for item in CartItem.objects.filter(cart=cart))
        cart.save()

        logger.debug(f"Cart ID: {cart.id}, Total Price: {cart.total_price}")

        return Response({'success': 'Item added to your cart'}, status=status.HTTP_201_CREATED)

    def put(self, request):
        data = request.data
        product_id = data.get('id')
        new_quantity = int(data.get('quantity'))

        if new_quantity <= 0:
            return Response({'error': 'Quantity must be greater than 0'}, status=status.HTTP_400_BAD_REQUEST)

        cart = Cart.objects.filter(user=request.user, ordered=False).first()
        if not cart:
            return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)

        cart_item = CartItem.objects.filter(cart=cart, product_id=product_id).first()
        if not cart_item:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

        product = cart_item.product

        if new_quantity > cart_item.quantity:
            additional_quantity = new_quantity - cart_item.quantity
            if product.quantity < additional_quantity:
                return Response({'error': 'Not enough stock available'}, status=status.HTTP_400_BAD_REQUEST)
            product.quantity -= additional_quantity
        else:
            product.quantity += cart_item.quantity - new_quantity

        price = Decimal(product.promotion) if product.promotion else Decimal(product.price)
        cart_item.quantity = new_quantity
        cart_item.price = price * new_quantity
        cart_item.save()

        product.save()

        cart.total_price = sum(item.price for item in CartItem.objects.filter(cart=cart))
        cart.save()

        return Response({'success': 'Product quantity updated successfully'}, status=status.HTTP_200_OK)

    def delete(self, request):
        data = request.data
        cart_item = CartItem.objects.filter(id=data.get('id')).first()
        if not cart_item:
            return Response({'error': 'CartItem not found'}, status=status.HTTP_404_NOT_FOUND)

        cart = cart_item.cart
        product = cart_item.product
        product.quantity += cart_item.quantity
        product.save()

        cart_item.delete()

        if CartItem.objects.filter(cart=cart).exists():
            cart.total_price = sum(item.price for item in CartItem.objects.filter(cart=cart))
        else:
            cart.total_price = 0
        cart.save()

        return Response({'success': 'Item removed from your cart'}, status=status.HTTP_200_OK)

class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['order'],
        operation_description="Этот эндпоинт позволяет пользователю оформить заказ, "
                              "который придет на email администратора, "
                              "после этого администратор свяжется с пользователем"
    )
    def post(self, request):
        user = request.user
        data = request.data

        cart = Cart.objects.filter(user=user, ordered=False).first()

        if not cart:
            return Response({'error': 'Cart not found'}, status=400)

        order_data = {
            'user': user.id,
            'cart': cart.id,
            'total_price': cart.total_price,
            'address': data.get('address'),
            'payment_method': data.get('payment_method')  # ID способа оплаты
        }
        serializer = OrderSerializer(data=order_data)
        if serializer.is_valid():
            order = serializer.save()
            order.send_order_email()
            order.clear_user_cart()
            return Response({'success': 'Order created and email sent'}, status=201)
        return Response(serializer.errors, status=400)
