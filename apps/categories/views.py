from django.db.models import Q
from rest_framework import permissions, viewsets

from .models import Category
from .permissions import IsCategoryOwnerOrReadOnlyDefault
from .serializers import CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsCategoryOwnerOrReadOnlyDefault]

    def get_queryset(self):
        return Category.objects.filter(Q(user=self.request.user) | Q(user__isnull=True))
