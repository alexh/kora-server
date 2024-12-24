from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductIdeaViewSet, IssueViewSet
from .views.store import ProductViewSet, OrderViewSet

router = DefaultRouter()
router.register(r'product-ideas', ProductIdeaViewSet)
router.register(r'issues', IssueViewSet)
router.register(r'store/products', ProductViewSet, basename='products')
router.register(r'store/orders', OrderViewSet, basename='orders')

urlpatterns = [
    path('', include(router.urls)),
] 