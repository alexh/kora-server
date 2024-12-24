from rest_framework import viewsets
from rest_framework.response import Response
from ..models import ProductIdea
from ..serializers.product import ProductIdeaSerializer

class ProductIdeaViewSet(viewsets.ModelViewSet):
    queryset = ProductIdea.objects.all()
    serializer_class = ProductIdeaSerializer 