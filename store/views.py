
from django.db.models import Avg, F
from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Customer, Product, WishList
from .serializers import (
    LuxurySpecialSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    WishlistItemSerializer,
)


class ProductListAPIView(APIView):
    def get(self, request):
        products = (
            Product.objects
            .select_related("brand", "category")
            .only(
                "id",
                "title",
                "slug",
                "price",
                "is_available",
                "stash",
                "brand__id",
                "brand__name",
                "category__id",
                "category__title",
            )
        )

        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductDetailAPIView(APIView):
    def get(self, request, slug):
        product = get_object_or_404(
            Product.objects
            .select_related("brand", "category")
            .prefetch_related(
                "images",
                "colors",
                "comments__customer__user",
            ),
            slug=slug,
        )

        Product.objects.filter(pk=product.pk).update(
            click_count=F("click_count") + 1
        )

        product.click_count += 1

        serializer = ProductDetailSerializer(product)
        return Response(serializer.data)


class LuxurySpecialAPIView(APIView):
    def get(self, request):
        average_price = (
            Product.objects
            .filter(is_luxury=True)
            .aggregate(average_price=Avg("price"))
            ["average_price"]
        )

        products = (
            Product.objects
            .filter(
                is_special=True,
                is_luxury=True,
                is_available=True,
            )
            .only(
                "id",
                "title",
                "price",
                "gender",
                "strap_material",
                "engine",
            )
        )

        serializer = LuxurySpecialSerializer(
            products,
            many=True,
            context={
                "average_luxury_price": average_price,
            },
        )

        return Response(serializer.data)


class MyWishlistAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        customer = get_object_or_404(
            Customer,
            user=request.user,
        )

        wishlist = (
            WishList.objects
            .filter(customer=customer)
            .select_related(
                "customer__user",
                "product",
            )
            .only(
                "id",
                "created_at",
                "customer__id",
                "customer__phone_number",
                "customer__user__username",
                "customer__user__email",
                "product__id",
                "product__title",
                "product__slug",
                "product__price",
                "product__stash",
                "product__main_image",
            )
        )

        serializer = WishlistItemSerializer(
            wishlist,
            many=True,
        )

        return Response(serializer.data)
