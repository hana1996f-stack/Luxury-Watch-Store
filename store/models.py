from django.conf import settings
from django.db import models
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseModel(TimeStampedModel):
    class Meta:
        abstract = True


class SluggedMixinModel(models.Model):
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug and getattr(self, "title", None):
            base_slug = slugify(self.title) or "product"
            candidate = base_slug
            counter = 1
            model = self.__class__
            while model.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                counter += 1
                candidate = f"{base_slug}-{counter}"
            self.slug = candidate
        super().save(*args, **kwargs)


class Brand(BaseModel):
    name = models.CharField(max_length=150, unique=True)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Category(BaseModel):
    title = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=180, unique=True, blank=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["title"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "category"
            candidate, counter = base_slug, 1
            while Category.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                counter += 1
                candidate = f"{base_slug}-{counter}"
            self.slug = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Product(BaseModel, SluggedMixinModel):
    class Gender(models.TextChoices):
        MEN = "men", "Men"
        WOMEN = "women", "Women"
        UNISEX = "unisex", "Unisex"

    class Origin(models.TextChoices):
        SWISS = "swiss", "Swiss"
        JAPANESE = "japanese", "Japanese"
        GERMAN = "german", "German"
        OTHER = "other", "Other"

    class StrapMaterial(models.TextChoices):
        LEATHER = "leather", "Leather"
        STEEL = "steel", "Steel"
        RUBBER = "rubber", "Rubber"
        FABRIC = "fabric", "Fabric"
        GOLD = "gold", "Gold"

    class Usage(models.TextChoices):
        FORMAL = "formal", "Formal"
        SPORT = "sport", "Sport"
        DAILY = "daily", "Daily"
        DIVER = "diver", "Diver"

    class Design(models.TextChoices):
        CLASSIC = "classic", "Classic"
        MODERN = "modern", "Modern"
        MINIMAL = "minimal", "Minimal"
        CHRONOGRAPH = "chronograph", "Chronograph"

    class Engine(models.TextChoices):
        AUTOMATIC = "automatic", "Automatic"
        QUARTZ = "quartz", "Quartz"
        MANUAL = "manual", "Manual"
        SMART = "smart", "Smart"

    title = models.CharField(max_length=200)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    is_discount = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    is_special = models.BooleanField(default=False)
    gender = models.CharField(max_length=10, choices=Gender.choices)
    origin = models.CharField(max_length=12, choices=Origin.choices)
    strap_material = models.CharField(max_length=12, choices=StrapMaterial.choices)
    usage = models.CharField(max_length=12, choices=Usage.choices)
    design = models.CharField(max_length=20, choices=Design.choices)
    engine = models.CharField(max_length=12, choices=Engine.choices)
    main_image = models.ImageField(upload_to="products/main/", blank=True, null=True)
    features = models.JSONField(default=dict, blank=True)
    is_luxury = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    stash = models.PositiveIntegerField(default=0)
    click_count = models.PositiveBigIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_special", "is_luxury", "is_available"]),
            models.Index(fields=["slug"]),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(price__gte=0), name="product_price_nonnegative"),
        ]

    def __str__(self):
        return self.title


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/gallery/")

    def __str__(self):
        return f"Image for {self.product.title}"


class ProductColor(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="colors")
    color = models.CharField(max_length=80)
    hex_code = models.CharField(max_length=7)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product", "color"], name="unique_product_color"),
        ]

    def __str__(self):
        return f"{self.product.title} - {self.color}"


class Customer(BaseModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer")
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.user.get_username()


class Comment(TimeStampedModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="comments")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="comments")
    body = models.TextField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment by {self.customer}"


class WishList(TimeStampedModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="wishlist_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product", "customer"], name="unique_customer_product_wishlist"),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer} - {self.product}"
