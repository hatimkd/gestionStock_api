# views.py
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from .models import Category, Article,RestockRequest
from .serializers import CategorySerializer, ArticleSerializer
from .permissions import IsGestionnaire
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Category, Article, Order, OrderItem, ArticleSupplier,StockMovement
from .serializers import (
    CategorySerializer,
    ArticleSerializer,
    OrderSerializer,
    OrderItemSerializer,
    ArticleSupplierSerializer,
    StockMovementSerializer,
    RestockRequestSerializer
)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:  # GET, HEAD, OPTIONS sont ouverts à tous authentifiés
            permission_classes = [IsAuthenticated]
        else:  # POST, PUT, PATCH, DELETE réservés aux gestionnaires
            permission_classes = [IsAuthenticated, IsGestionnaire]
        return [permission() for permission in permission_classes]

from rest_framework.parsers import MultiPartParser, FormParser

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all().select_related('category')
    serializer_class = ArticleSerializer
    
    
    


    # parser_classes = [MultiPartParser, FormParser]  # <-- Ajoute ça ici



    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsGestionnaire]
        return [permission() for permission in permission_classes]

# class Article(viewsets.ModelViewSet):

    



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_articles(request):
    articles = Article.objects.all().select_related('category')
    serializer = ArticleSerializer(articles, many=True)
    return Response(serializer.data)
# views.py




# from rest_framework.decorators import api_view, permission_classes


User = get_user_model()


# =============================================================================
# ORDER VIEWS
# =============================================================================

class OrderListCreateView(generics.ListCreateAPIView):
    """
    Liste toutes les commandes ou crée une nouvelle commande
    GET /api/orders/ - Liste des commandes
    POST /api/orders/ - Créer une commande
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'supplier']
    search_fields = ['order_number', 'supplier__username']
    ordering_fields = ['order_date', 'expected_delivery_date', 'total_amount', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filtre les commandes selon le rôle de l'utilisateur"""
        user = self.request.user
        if user.groups.filter(name='fournisseur').exists():
            # Si l'utilisateur est fournisseur, il ne voit que ses commandes
            return Order.objects.filter(supplier=user).select_related('supplier', 'user').prefetch_related('order_items__article')
        else:
            # Sinon, il voit toutes les commandes
            return Order.objects.all().select_related('supplier', 'user').prefetch_related('order_items__article')


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Récupère, met à jour ou supprime une commande spécifique
    GET /api/orders/{id}/ - Détails d'une commande
    PUT /api/orders/{id}/ - Mise à jour complète
    PATCH /api/orders/{id}/ - Mise à jour partielle
    DELETE /api/orders/{id}/ - Suppression
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filtre les commandes selon le rôle de l'utilisateur"""
        user = self.request.user
        if user.groups.filter(name='fournisseur').exists():
            return Order.objects.filter(supplier=user).select_related('supplier', 'user').prefetch_related('order_items__article')
        else:
            return Order.objects.all().select_related('supplier', 'user').prefetch_related('order_items__article')


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_order_status(request, pk):
    """
    Met à jour le statut d'une commande
    PATCH /api/orders/{id}/status/
    Body: {"status": "nouveau_statut"}
    """
    order = get_object_or_404(Order, pk=pk)
    
    # Vérifier les permissions
    user = request.user
    if user.groups.filter(name='fournisseur').exists() and order.supplier != user:
        return Response(
            {'error': 'Vous ne pouvez modifier que vos propres commandes'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    new_status = request.data.get('status')
    if not new_status:
        return Response(
            {'error': 'Le statut est requis'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Valider les statuts autorisés
    valid_statuses = ['en_attente', 'confirmee', 'en_cours', 'livree', 'annulee']
    if new_status not in valid_statuses:
        return Response(
            {'error': f'Statut non valide. Statuts autorisés: {valid_statuses}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    order.status = new_status
    order.save()
    
    serializer = OrderSerializer(order)
    return Response(serializer.data)


# =============================================================================
# ORDER ITEM VIEWS
# =============================================================================

class OrderItemListView(generics.ListAPIView):
    """
    Liste tous les éléments de commande
    GET /api/order-items/ - Liste des éléments de commande
    """
    queryset = OrderItem.objects.select_related('order', 'article').all()
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'article']
    ordering_fields = ['quantity_ordered', 'unit_price', 'total_price']
    ordering = ['-order__created_at']


class OrderItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Récupère, met à jour ou supprime un élément de commande spécifique
    GET /api/order-items/{id}/ - Détails d'un élément
    PUT /api/order-items/{id}/ - Mise à jour complète
    PATCH /api/order-items/{id}/ - Mise à jour partielle
    DELETE /api/order-items/{id}/ - Suppression
    """
    queryset = OrderItem.objects.select_related('order', 'article').all()
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_received_quantity(request, pk):
    """
    Met à jour la quantité reçue d'un élément de commande
    PATCH /api/order-items/{id}/received-quantity/
    Body: {"quantity_received": 10}
    """
    order_item = get_object_or_404(OrderItem, pk=pk)
    
    quantity_received = request.data.get('quantity_received')
    if quantity_received is None:
        return Response(
            {'error': 'La quantité reçue est requise'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if quantity_received < 0:
        return Response(
            {'error': 'La quantité reçue ne peut être négative'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if quantity_received > order_item.quantity_ordered:
        return Response(
            {'error': 'La quantité reçue ne peut dépasser la quantité commandée'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    order_item.quantity_received = quantity_received
    order_item.save()
    
    # Mettre à jour le stock de l'article
    if quantity_received > 0:
        article = order_item.article
        article.quantity += quantity_received
        article.save()
    
    serializer = OrderItemSerializer(order_item)
    return Response(serializer.data)


# =============================================================================
# ARTICLE SUPPLIER VIEWS
# =============================================================================

class ArticleSupplierListCreateView(generics.ListCreateAPIView):
    """
    Liste toutes les associations article-fournisseur ou en crée une nouvelle
    GET /api/article-suppliers/ - Liste des associations
    POST /api/article-suppliers/ - Créer une association
    """
    queryset = ArticleSupplier.objects.select_related('article', 'supplier').all()
    serializer_class = ArticleSupplierSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['article', 'supplier', 'is_preferred']
    search_fields = ['article__name', 'supplier__username', 'supplier_reference']
    ordering_fields = ['supplier_price', 'created_at']
    ordering = ['-created_at']


class ArticleSupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Récupère, met à jour ou supprime une association article-fournisseur
    GET /api/article-suppliers/{id}/ - Détails d'une association
    PUT /api/article-suppliers/{id}/ - Mise à jour complète
    PATCH /api/article-suppliers/{id}/ - Mise à jour partielle
    DELETE /api/article-suppliers/{id}/ - Suppression
    """
    queryset = ArticleSupplier.objects.select_related('article', 'supplier').all()
    serializer_class = ArticleSupplierSerializer
    permission_classes = [IsAuthenticated]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def article_suppliers_by_article(request, article_id):
    """
    Liste des fournisseurs pour un article donné
    GET /api/articles/{article_id}/suppliers/
    """
    article = get_object_or_404(Article, pk=article_id)
    article_suppliers = ArticleSupplier.objects.filter(article=article).select_related('supplier')
    serializer = ArticleSupplierSerializer(article_suppliers, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def supplier_articles(request, supplier_id):
    """
    Liste des articles pour un fournisseur donné
    GET /api/suppliers/{supplier_id}/articles/
    """
    supplier = get_object_or_404(User, pk=supplier_id)
    article_suppliers = ArticleSupplier.objects.filter(supplier=supplier).select_related('article')
    serializer = ArticleSupplierSerializer(article_suppliers, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def set_preferred_supplier(request, pk):
    """
    Définit un fournisseur comme préféré pour un article
    PATCH /api/article-suppliers/{id}/set-preferred/
    """
    article_supplier = get_object_or_404(ArticleSupplier, pk=pk)
    
    # Réinitialiser tous les autres fournisseurs de cet article
    ArticleSupplier.objects.filter(
        article=article_supplier.article
    ).update(is_preferred=False)
    
    # Définir ce fournisseur comme préféré
    article_supplier.is_preferred = True
    article_supplier.save()
    
    serializer = ArticleSupplierSerializer(article_supplier)
    return Response(serializer.data)


# =============================================================================
# VUES STATISTIQUES ET REPORTING
# =============================================================================
from django.db.models import Count, F

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Statistiques pour le tableau de bord
    GET /api/dashboard/stats/
    """
    from django.db.models import Count, Sum
    
    stats = {
        'total_articles': Article.objects.count(),
        'critical_articles':Article.objects.filter(quantity__lte=F('critical_threshold')).count(),
        'total_categories': Category.objects.count(),
        'pending_orders': Order.objects.filter(status='en_attente').count(),
        'total_orders': Order.objects.count(),
        'total_suppliers': User.objects.filter(groups__name='fournisseur').count(),
        'orders_by_status': list(
            Order.objects.values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        ),
        'top_articles': list(
            Article.objects.annotate(
                order_count=Count('order_items')
            ).order_by('-order_count')[:5]
            .values('id', 'name', 'order_count')
        )
    }
    
    return Response(stats)



class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.select_related("article", "user").all()
    serializer_class = StockMovementSerializer

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]  # tous les utilisateurs connectés peuvent lire
        return [IsAuthenticated(), IsGestionnaire()]  # seuls les gestionnaires modifient

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    

from rest_framework.decorators import action

class RestockRequestViewSet(viewsets.ModelViewSet):
    # queryset = RestockRequest.objects.all().order_by('-created_at')
    serializer_class = RestockRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.groups.filter(name='gestionnaire').exists():
            return RestockRequest.objects.all().order_by('-created_at')
        return RestockRequest.objects.filter(requester=user).order_by('-created_at')
    def perform_create(self, serializer):
        serializer.save(requester=self.request.user)
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        restock_request = self.get_object()
        if not request.user.groups.filter(name='gestionnaire').exists():
            return Response({"detail": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)

        restock_request.status = 'approved'
        restock_request.save()
        return Response({"message": "Demande approuvée"}, status=200)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        restock_request = self.get_object()
        if not request.user.groups.filter(name='gestionnaire').exists():
            return Response({"detail": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)

        restock_request.status = 'rejected'
        restock_request.save()
        return Response({"message": "Demande rejetée"}, status=200)