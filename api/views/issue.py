from rest_framework import viewsets
from rest_framework.response import Response
from ..models import Issue
from ..serializers.issue import IssueSerializer

class IssueViewSet(viewsets.ModelViewSet):
    queryset = Issue.objects.all()
    serializer_class = IssueSerializer 