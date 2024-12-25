from rest_framework import viewsets
from ..models import Product
from ..serializers.product import ProductSerializer

class ProductView(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer 