from rest_framework import serializers
from ..models import ProductIdea

class ProductIdeaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductIdea
        fields = '__all__' 