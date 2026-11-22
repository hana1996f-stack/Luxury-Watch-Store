from django.contrib import admin
from .models import (
    Brand, Category, Comment, Customer, Product, ProductColor,
    ProductImage, WishList,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "brand", "category", "price", "is_available", "is_special", "is_luxury")
    list_filter = ("brand", "category", "is_available", "is_special", "is_luxury")
    search_fields = ("title", "slug", "brand__name")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ProductImageInline, ProductColorInline]


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number")
    search_fields = ("user__username", "user__email", "phone_number")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("product", "customer", "created_at")
    list_filter = ("created_at",)


@admin.register(WishList)
class WishListAdmin(admin.ModelAdmin):
    list_display = ("customer", "product", "created_at")


@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ("product", "color", "hex_code")
