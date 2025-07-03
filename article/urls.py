# urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include


from django.conf.urls.static import static


from django.conf import settings
from . import views
from .views import CategoryViewSet, ArticleViewSet
from .views import StockMovementViewSet, Article,RestockRequestViewSet


router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"articles", ArticleViewSet, basename="article")

router.register(r"stock-movements", StockMovementViewSet, basename="stock-movement")

router.register(r'restock-requests', RestockRequestViewSet, basename='restockrequest')
urlpatterns = [
    path("", include(router.urls)),
    # path("article/", views.Article, name="art"),
    path('article/', views.list_articles, name='article-list'),

    
    # =============================================================================
    # ORDER URLS
    # =============================================================================
    path("orders/", views.OrderListCreateView.as_view(), name="order-list-create"),
    path("orders/<int:pk>/", views.OrderDetailView.as_view(), name="order-detail"),
    path(
        "orders/<int:pk>/status/", views.update_order_status, name="update-order-status"
    ),
    # =============================================================================
    # ORDER ITEM URLS
    # =============================================================================
    path("order-items/", views.OrderItemListView.as_view(), name="orderitem-list"),
    path(
        "order-items/<int:pk>/",
        views.OrderItemDetailView.as_view(),
        name="orderitem-detail",
    ),
    path(
        "order-items/<int:pk>/received-quantity/",
        views.update_received_quantity,
        name="update-received-quantity",
    ),
    # =============================================================================
    # ARTICLE SUPPLIER URLS
    # =============================================================================
    path(
        "article-suppliers/",
        views.ArticleSupplierListCreateView.as_view(),
        name="articlesupplier-list-create",
    ),
    path(
        "article-suppliers/<int:pk>/",
        views.ArticleSupplierDetailView.as_view(),
        name="articlesupplier-detail",
    ),
    path(
        "article-suppliers/<int:pk>/set-preferred/",
        views.set_preferred_supplier,
        name="set-preferred-supplier",
    ),
    path(
        "suppliers/<int:supplier_id>/articles/",
        views.supplier_articles,
        name="supplier-articles",
    ),
    # =============================================================================
    # DASHBOARD & STATS URLS
    # =============================================================================
    path("dashboard/stats/", views.dashboard_stats, name="dashboard-stats"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
