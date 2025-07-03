from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator


from django.utils import timezone


class Category(models.Model):
    """
    Modèle représentant une catégorie d'articles.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom de la catégorie",
        help_text="Nom unique de la catégorie",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Description optionnelle de la catégorie",
    )

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("category-detail", kwargs={"pk": self.pk})


import uuid


class Article(models.Model):
    """
    Modèle représentant un article stocké.
    """

    name = models.CharField(max_length=100, verbose_name="Nom de l'article")
    reference = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Référence UUID unique de l'article",
    )
    image = models.ImageField(
        upload_to="uploads/articles/",
        null=True,
        blank=True,
        verbose_name="Image de l'article",
        help_text="Image représentant l'article (optionnel)",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
        verbose_name="Catégorie",
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Prix unitaire",
    )
    quantity = models.PositiveIntegerField(
        default=0, verbose_name="Quantité en stock", validators=[MinValueValidator(0)]
    )
    critical_threshold = models.PositiveIntegerField(
        default=5,
        verbose_name="Seuil critique",
        help_text="Quantité minimale avant alerte",
        validators=[MinValueValidator(0)],
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )

    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.reference})"

    @property
    def is_critical(self):
        """
        Indique si la quantité est inférieure ou égale au seuil critique.
        """
        return self.quantity <= self.critical_threshold

    def get_absolute_url(self):
        return reverse("article-detail", kwargs={"pk": self.pk})


from django.contrib.auth.models import User


class ArticleSupplier(models.Model):
    """
    Relation entre un article et un fournisseur.
    """

    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    supplier = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        # limit_choices_to={'role': 'fournisseur'},
        verbose_name="Fournisseur",
    )
    supplier_reference = models.CharField(
        max_length=100, blank=True, verbose_name="Référence fournisseur"
    )
    supplier_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Prix fournisseur",
    )
    is_preferred = models.BooleanField(
        default=False, verbose_name="Fournisseur préféré"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["article", "supplier"]
        verbose_name = "Article-Fournisseur"
        verbose_name_plural = "Articles-Fournisseurs"

    def __str__(self):
        return f"{self.article.name} - {self.supplier.username}"


class StockMovement(models.Model):
    """
    Mouvements de stock : entrées, sorties, ajustements, transferts.
    """

    MOVEMENT_TYPES = [
        ("in", "Entrée"),
        ("out", "Sortie"),
        ("adjustment", "Ajustement"),
        ("transfer", "Transfert"),
    ]

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="stock_movements",
        verbose_name="Article",
    )
    movement_type = models.CharField(
        max_length=20, choices=MOVEMENT_TYPES, verbose_name="Type de mouvement"
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)], verbose_name="Quantité"
    )
    reference_document = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Document de référence",
        help_text="Numéro de bon, facture, etc.",
    )
    # notes = models.TextField(blank=True, verbose_name="Notes")
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="stock_movements",
        verbose_name="Utilisateur",
    )
    created_at = models.DateTimeField(
        default=timezone.now, verbose_name="Date du mouvement"
    )

    class Meta:
        verbose_name = "Mouvement de stock"
        verbose_name_plural = "Mouvements de stock"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.article.name} ({self.quantity})"

    def save(self, *args, **kwargs):
        """
        Mise à jour automatique du stock à la création du mouvement.
        """
        if self.pk is None:  # Nouveau mouvement
            if self.movement_type in ["in", "adjustment"]:
                self.article.quantity += self.quantity
            elif self.movement_type == "out":
                if self.article.quantity >= self.quantity:
                    self.article.quantity -= self.quantity
                else:
                    raise ValueError("Quantité insuffisante en stock")
            self.article.save()
        super().save(*args, **kwargs)


class Order(models.Model):
    """
    Commande fournisseur.
    """

    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("confirmed", "Confirmée"),
        ("shipped", "Expédiée"),
        ("delivered", "Livrée"),
        ("cancelled", "Annulée"),
    ]

    order_number = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro de commande"
    )
    supplier = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="supplier_orders",  # Changed here        # limit_choices_to={'role': 'fournisseur'},
        verbose_name="Fournisseur",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Statut"
    )
    order_date = models.DateTimeField(
        default=timezone.now, verbose_name="Date de commande"
    )
    expected_delivery_date = models.DateField(
        null=True, blank=True, verbose_name="Livraison prévue"
    )
    actual_delivery_date = models.DateField(
        null=True, blank=True, verbose_name="Livraison réelle"
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Montant total",
    )
    # notes = models.TextField(blank=True, verbose_name="Notes")
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="user_orders",  # Changed here
        verbose_name="Utilisateur créateur",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Commande {self.order_number} - {self.supplier.username}"

    def get_absolute_url(self):
        return reverse("order-detail", kwargs={"pk": self.pk})

    def calculate_total(self):
        """
        Calcule le total de la commande.
        """
        self.total_amount = sum(item.total_price for item in self.order_items.all())
        self.save()
        return self.total_amount


class OrderItem(models.Model):
    """
    Article contenu dans une commande fournisseur.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="order_items",
        verbose_name="Commande",
    )
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="order_items",
        verbose_name="Article",
    )
    quantity_ordered = models.PositiveIntegerField(
        validators=[MinValueValidator(1)], verbose_name="Quantité commandée"
    )
    quantity_received = models.PositiveIntegerField(
        default=0, verbose_name="Quantité reçue"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Prix unitaire",
    )

    class Meta:
        verbose_name = "Article de commande"
        verbose_name_plural = "Articles de commande"
        unique_together = ["order", "article"]

    def __str__(self):
        return f"{self.article.name} - {self.quantity_ordered} unités"

    @property
    def total_price(self):
        return self.quantity_ordered * self.unit_price

    @property
    def is_fully_received(self):
        return self.quantity_received >= self.quantity_ordered

    @property
    def remaining_quantity(self):
        return max(0, self.quantity_ordered - self.quantity_received)







class RestockRequest(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="restock_requests")
    quantity_requested = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    comment = models.TextField(blank=True)
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name="restock_requests")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'En attente'),
            ('approved', 'Approuvée'),
            ('rejected', 'Rejetée')
        ],
        default='pending'
    )

    def __str__(self):
        return f"{self.article.name} - {self.quantity_requested} demandée par {self.requester.username}"
