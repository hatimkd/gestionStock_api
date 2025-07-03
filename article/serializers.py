
# serializers.py
from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Category, Article, Order, OrderItem, ArticleSupplier ,StockMovement,RestockRequest

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description"]


class ArticleSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only=True,
        required=False,
        allow_null=True,
    )
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Article
        fields = [
            "id",
            "name",
            "reference",
            "category",
            "category_id",
            "unit_price",
            "quantity",
            "critical_threshold",
            "created_at",
            "is_critical",
            "image",
        ]
        read_only_fields = ["reference", "created_at", "is_critical"]


class OrderItemSerializer(serializers.ModelSerializer):
    article_name = serializers.ReadOnlyField(source="article.name")
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "article",
            "article_name",
            "quantity_ordered",
            "quantity_received",
            "unit_price",
            "total_price",
        ]
        extra_kwargs = {
            "quantity_received": {"read_only": True},  # souvent géré à part
        }

    def validate_quantity_ordered(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "La quantité commandée doit être au moins 1."
            )
        return value


class OrderSerializer(serializers.ModelSerializer):
    supplier_name = serializers.ReadOnlyField(source="supplier.username")
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )  # Auto fill user
    order_items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "supplier",
            "supplier_name",
            "status",
            "order_date",
            "expected_delivery_date",
            "actual_delivery_date",
            "total_amount",
            "user",
            "created_at",
            "updated_at",
            "order_items",
        ]
        read_only_fields = ["total_amount", "created_at", "updated_at"]

    def validate(self, data):
        order_date = data.get("order_date", timezone.now())
        expected_delivery_date = data.get("expected_delivery_date")
        actual_delivery_date = data.get("actual_delivery_date")

        if expected_delivery_date and expected_delivery_date < order_date.date():
            raise serializers.ValidationError(
                "La date de livraison prévue ne peut être antérieure à la date de commande."
            )

        if (
            actual_delivery_date
            and expected_delivery_date
            and actual_delivery_date < expected_delivery_date
        ):
            raise serializers.ValidationError(
                "La date de livraison réelle ne peut être antérieure à la date de livraison prévue."
            )

        return data

    def create(self, validated_data):
        order_items_data = validated_data.pop("order_items")
        user = self.context["request"].user
        validated_data["user"] = user

        validated_data["order_number"] = (
            f"ORD-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        )

        order = Order.objects.create(**validated_data)

        for item_data in order_items_data:
            OrderItem.objects.create(order=order, **item_data)

        order.calculate_total()

        return order

    def update(self, instance, validated_data):
        order_items_data = validated_data.pop("order_items", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if order_items_data is not None:
            instance.order_items.all().delete()
            for item_data in order_items_data:
                OrderItem.objects.create(order=instance, **item_data)

        instance.calculate_total()
        return instance


class ArticleSupplierSerializer(serializers.ModelSerializer):
    article_id = serializers.PrimaryKeyRelatedField(
        queryset=Article.objects.all(), source="article"
    )
    supplier_id = serializers.PrimaryKeyRelatedField(
        # queryset=User.objects.filter(role='fournisseur'),
        queryset=User.objects.filter(groups__name="fournisseur"),
        source="supplier",
    )

    class Meta:
        model = ArticleSupplier
        fields = [
            "id",
            "article_id",
            "supplier_id",
            "supplier_reference",
            "supplier_price",
            "is_preferred",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_supplier_price(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Le prix fournisseur doit être positif ou nul."
            )
        return value

    def validate(self, attrs):
        article = attrs.get("article")
        supplier = attrs.get("supplier")
        if (
            self.instance is None
            and ArticleSupplier.objects.filter(
                article=article, supplier=supplier
            ).exists()
        ):
            raise serializers.ValidationError(
                "Cette association article-fournisseur existe déjà."
            )
        return attrs




class StockMovementSerializer(serializers.ModelSerializer):
    article_name = serializers.ReadOnlyField(source="article.name")
    user_name = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "article",
            "article_name",
            "movement_type",
            "quantity",
            "reference_document",
            "user",
            "user_name",
            "created_at"
        ]
        read_only_fields = ["id", "created_at", "user", "user_name"]
    
    def create(self, validated_data):
        # Injecter l'utilisateur courant comme responsable du mouvement
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
    

class RestockRequestSerializer(serializers.ModelSerializer):
    requester = serializers.StringRelatedField(read_only=True)  # pour afficher le nom

    class Meta:
        model = RestockRequest
        fields = '__all__'
        read_only_fields = ['requester', 'created_at', 'status']