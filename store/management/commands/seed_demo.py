from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from store.models import (
    Brand,
    Category,
    Customer,
    Product,
    ProductColor,
    ProductImage,
    Comment,
    WishList,
)


class Command(BaseCommand):
    help = "Create demo data for Luxury Watch Store"

    @transaction.atomic
    def handle(self, *args, **kwargs):

        # 1. Brands
        brands = {}
        for name in [
            "Rolex", "Omega", "Patek Philippe",
            "Seiko", "TAG Heuer"
        ]:
            brands[name], _ = Brand.objects.update_or_create(
                name=name,
                defaults={
                    "meta_title": f"{name} Watches",
                    "meta_description": f"Demo brand {name}"
                }
            )

        # 2. Categories
        categories = {}
        for title in [
            "Dress Watches",
            "Sports Watches",
            "Diver Watches",
            "Chronograph Watches",
            "Classic Watches",
            "Smart Watches",
        ]:
            categories[title], _ = Category.objects.get_or_create(
                title=title
            )

        # 3. Customers and Users
        User = get_user_model()
        customers = {}

        for username, email, phone in [
            ("alice_demo", "alice@example.com", "09120000001"),
            ("bob_demo", "bob@example.com", "09120000002"),
            ("charlie_demo", "charlie@example.com", "09120000003"),
        ]:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": email}
            )

            if created:
                user.set_password("DemoPass123!")
                user.save()

            customers[username], _ = Customer.objects.update_or_create(
                user=user,
                defaults={"phone_number": phone}
            )

        # 4. Products
        products_data = [
            ("Submariner Date", "Rolex", "Diver Watches", 12500, "men", "swiss", "steel", "diver", "classic", "automatic", True, True, 4),
            ("Datejust 41", "Rolex", "Classic Watches", 9800, "men", "swiss", "steel", "formal", "classic", "automatic", True, True, 2),
            ("Lady-Datejust", "Rolex", "Dress Watches", 8700, "women", "swiss", "gold", "formal", "classic", "automatic", True, False, 3),
            ("Speedmaster Moonwatch", "Omega", "Chronograph Watches", 7200, "unisex", "swiss", "steel", "sport", "chronograph", "manual", True, True, 5),
            ("Seamaster Aqua Terra", "Omega", "Sports Watches", 6100, "men", "swiss", "leather", "daily", "modern", "automatic", True, True, 6),
            ("Nautilus", "Patek Philippe", "Classic Watches", 45000, "men", "swiss", "steel", "formal", "modern", "automatic", True, True, 1),
            ("Calatrava", "Patek Philippe", "Dress Watches", 28000, "unisex", "swiss", "leather", "formal", "minimal", "manual", True, True, 1),
            ("Presage Cocktail Time", "Seiko", "Dress Watches", 520, "women", "japanese", "leather", "daily", "classic", "automatic", False, False, 12),
            ("Prospex Diver", "Seiko", "Diver Watches", 680, "men", "japanese", "rubber", "diver", "modern", "automatic", False, False, 8),
            ("Seiko 5 Sports", "Seiko", "Sports Watches", 310, "unisex", "japanese", "steel", "daily", "modern", "automatic", False, False, 15),
            ("Carrera Chronograph", "TAG Heuer", "Chronograph Watches", 4300, "men", "swiss", "steel", "sport", "chronograph", "automatic", True, True, 3),
            ("Aquaracer Professional", "TAG Heuer", "Diver Watches", 3500, "unisex", "swiss", "steel", "diver", "modern", "automatic", True, True, 4),
        ]

        products = {}

        for data in products_data:
            (
                title, brand, category, price, gender, origin,
                strap, usage, design, engine, luxury, special, stash
            ) = data

            product, _ = Product.objects.update_or_create(
                title=title,
                defaults={
                    "brand": brands[brand],
                    "category": categories[category],
                    "price": Decimal(str(price)),
                    "gender": gender,
                    "origin": origin,
                    "strap_material": strap,
                    "usage": usage,
                    "design": design,
                    "engine": engine,
                    "is_discount": False,
                    "is_available": stash > 0,
                    "is_special": special,
                    "is_luxury": luxury,
                    "stash": stash,
                    "features": {
                        "water_resistance": "100m",
                        "display": "analog",
                        "demo_data": True,
                    },
                    "description": f"Demo product: {title}",
                    "meta_title": title,
                    "meta_description": f"Luxury watch {title}",
                }
            )

            products[title] = product

            # Product colors
            for color, hex_code in [
                ("Silver", "#C0C0C0"),
                ("Black", "#000000"),
            ]:
                ProductColor.objects.update_or_create(
                    product=product,
                    color=color,
                    defaults={"hex_code": hex_code}
                )

            # Image placeholder record
            if not product.images.exists():
                ProductImage.objects.create(product=product)

        # 5. Comments
        comments = [
            ("alice_demo", "Submariner Date", "Excellent quality."),
            ("bob_demo", "Submariner Date", "Beautiful design."),
            ("charlie_demo", "Speedmaster Moonwatch", "Amazing watch."),
            ("alice_demo", "Nautilus", "Very elegant."),
            ("bob_demo", "Seiko 5 Sports", "Great value."),
            ("charlie_demo", "Aquaracer Professional", "Excellent sports watch."),
            ("alice_demo", "Datejust 41", "Classic design."),
            ("bob_demo", "Presage Cocktail Time", "Beautiful dial."),
        ]

        for username, title, body in comments:
            Comment.objects.get_or_create(
                customer=customers[username],
                product=products[title],
                body=body
            )

        # 6. Wishlist
        wishlist = [
            ("alice_demo", "Submariner Date"),
            ("alice_demo", "Nautilus"),
            ("alice_demo", "Presage Cocktail Time"),
            ("bob_demo", "Speedmaster Moonwatch"),
            ("bob_demo", "Seiko 5 Sports"),
            ("charlie_demo", "Calatrava"),
            ("charlie_demo", "Aquaracer Professional"),
        ]

        for username, title in wishlist:
            WishList.objects.get_or_create(
                customer=customers[username],
                product=products[title]
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Demo data created successfully!"
            )
        )