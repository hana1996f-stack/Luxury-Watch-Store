
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from rest_framework.test import APIClient

from .models import (
    Brand,
    Category,
    Comment,
    Customer,
    Product,
    ProductColor,
    ProductImage,
    WishList,
)


User = get_user_model()


class StoreAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.brand = Brand.objects.create(
            name="Omega",
        )

        self.category = Category.objects.create(
            title="Luxury",
        )

        self.product = self.create_product(
            title="Seamaster",
            price=Decimal("2500.00"),
            is_special=True,
            is_luxury=True,
            is_available=True,
        )

        self.user = User.objects.create_user(
            username="tester",
            password="StrongPass123",
            email="test@example.com",
        )

        self.customer = Customer.objects.create(
            user=self.user,
        )

    def create_product(self, **overrides):
        data = {
            "title": "Test Watch",
            "brand": self.brand,
            "category": self.category,
            "price": Decimal("2000.00"),
            "gender": Product.Gender.MEN,
            "origin": Product.Origin.SWISS,
            "strap_material": Product.StrapMaterial.STEEL,
            "usage": Product.Usage.DAILY,
            "design": Product.Design.CLASSIC,
            "engine": Product.Engine.AUTOMATIC,
            "stash": 3,
            "is_special": False,
            "is_luxury": True,
            "is_available": True,
        }

        data.update(overrides)

        return Product.objects.create(**data)


    def test_product_list(self):
        with self.assertNumQueries(1):
            response = self.client.get("/api/products/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        product_data = response.data[0]

        self.assertEqual(product_data["title"], "Seamaster")
        self.assertEqual(product_data["brand"], "Omega")
        self.assertEqual(product_data["category"], "Luxury")
        self.assertEqual(product_data["slug"], self.product.slug)

    def test_product_list_has_no_n_plus_one_queries(self):
        for index in range(5):
            self.create_product(
                title=f"Watch {index}",
                price=Decimal("2000.00") + index,
            )

        with self.assertNumQueries(1):
            response = self.client.get("/api/products/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 6)

    def test_product_detail_increments_click_count(self):
        response = self.client.get(
            f"/api/products/{self.product.slug}/"
        )

        self.assertEqual(response.status_code, 200)

        self.product.refresh_from_db()
        self.assertEqual(self.product.click_count, 1)

        response = self.client.get(
            f"/api/products/{self.product.slug}/"
        )

        self.assertEqual(response.status_code, 200)

        self.product.refresh_from_db()
        self.assertEqual(self.product.click_count, 2)

    def test_product_detail_returns_related_data(self):
        ProductImage.objects.create(
            product=self.product,
            image="products/test.jpg",
        )

        ProductColor.objects.create(
            product=self.product,
            color="Silver",
            hex_code="#C0C0C0",
        )

        Comment.objects.create(
            product=self.product,
            customer=self.customer,
            body="Excellent watch",
        )

        response = self.client.get(
            f"/api/products/{self.product.slug}/"
        )

        self.assertEqual(response.status_code, 200)

        self.assertIn("images", response.data)
        self.assertIn("colors", response.data)
        self.assertIn("comments", response.data)

        self.assertEqual(len(response.data["images"]), 1)
        self.assertEqual(len(response.data["colors"]), 1)
        self.assertEqual(len(response.data["comments"]), 1)

        self.assertEqual(
            response.data["comments"][0]["customer"],
            "tester",
        )

    def test_product_detail_not_found(self):
        response = self.client.get(
            "/api/products/non-existing-product/"
        )

        self.assertEqual(response.status_code, 404)

    def test_product_detail_has_no_n_plus_one_queries(self):
        for index in range(3):
            product = self.create_product(
                title=f"Related Watch {index}",
            )

            ProductImage.objects.create(
                product=product,
                image="products/test.jpg",
            )

            ProductColor.objects.create(
                product=product,
                color=f"Color {index}",
                hex_code="#C0C0C0",
            )

            Comment.objects.create(
                product=product,
                customer=self.customer,
                body=f"Comment {index}",
            )

        with self.assertNumQueries(5):
            response = self.client.get(
                f"/api/products/{self.product.slug}/"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["images"]), 0)
        self.assertEqual(len(response.data["colors"]), 0)
        self.assertEqual(len(response.data["comments"]), 0)



    def test_luxury_special_average_price(self):
        self.create_product(
            title="Luxury Hidden Watch",
            price=Decimal("3500.00"),
            is_special=False,
            is_luxury=True,
            is_available=False,
        )

        self.create_product(
            title="Regular Watch",
            price=Decimal("10000.00"),
            is_special=True,
            is_luxury=False,
            is_available=True,
        )

        response = self.client.get("/api/luxury-special/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        product_data = response.data[0]

        self.assertEqual(product_data["title"], "Seamaster")

        self.assertEqual(
            product_data["average_luxury_price"],
            "3000.00",
        )

    def test_luxury_special_filters_products(self):
        self.create_product(
            title="Not Special",
            is_special=False,
            is_luxury=True,
            is_available=True,
        )

        self.create_product(
            title="Not Luxury",
            is_special=True,
            is_luxury=False,
            is_available=True,
        )

        self.create_product(
            title="Not Available",
            is_special=True,
            is_luxury=True,
            is_available=False,
        )

        response = self.client.get("/api/luxury-special/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Seamaster")

    def test_luxury_special_has_no_n_plus_one_queries(self):
        for index in range(5):
            self.create_product(
                title=f"Special Luxury Watch {index}",
                price=Decimal("4000.00") + index,
                is_special=True,
                is_luxury=True,
                is_available=True,
            )

        with self.assertNumQueries(2):
            response = self.client.get("/api/luxury-special/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 6)


    def test_wishlist_requires_authentication(self):
        response = self.client.get("/api/me/wishlist/")

        self.assertEqual(response.status_code, 401)

    def test_wishlist_returns_user_items(self):
        WishList.objects.create(
            customer=self.customer,
            product=self.product,
        )

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get("/api/me/wishlist/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        item = response.data[0]

        self.assertEqual(item["product"]["title"], "Seamaster")
        self.assertEqual(item["product"]["slug"], self.product.slug)
        self.assertEqual(item["customer"]["username"], "tester")
        self.assertEqual(item["customer"]["email"], "test@example.com")

    def test_wishlist_only_returns_current_user_items(self):
        another_user = User.objects.create_user(
            username="another",
            password="StrongPass123",
            email="another@example.com",
        )

        another_customer = Customer.objects.create(
            user=another_user,
        )

        WishList.objects.create(
            customer=self.customer,
            product=self.product,
        )

        another_product = self.create_product(
            title="Another Watch",
            price=Decimal("4000.00"),
        )

        WishList.objects.create(
            customer=another_customer,
            product=another_product,
        )

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get("/api/me/wishlist/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        self.assertEqual(
            response.data[0]["product"]["slug"],
            self.product.slug,
        )

    def test_wishlist_has_no_n_plus_one_queries(self):
        for index in range(5):
            product = self.create_product(
                title=f"Wishlist Watch {index}",
                price=Decimal("3000.00") + index,
            )

            WishList.objects.create(
                customer=self.customer,
                product=product,
            )

        self.client.force_authenticate(
            user=self.user,
        )

        with self.assertNumQueries(2):
            response = self.client.get("/api/me/wishlist/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)

    def test_wishlist_unique_constraint(self):
        WishList.objects.create(
            customer=self.customer,
            product=self.product,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WishList.objects.create(
                    customer=self.customer,
                    product=self.product,
                )
