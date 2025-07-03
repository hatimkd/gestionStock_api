from rest_framework.pagination import PageNumberPagination

class CustomUsersPagination(PageNumberPagination):
    page_size = 5  # nombre d’objets retournés par défaut (5 recettes par page)
    page_size_query_param = 'page_size'  # permet d’ajuster dynamiquement avec ?page_size=10
    max_page_size = 100  # limite max pour éviter les abus
