from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsCategoryOwnerOrReadOnlyDefault(BasePermission):
    """Default categories (user=None) are shared, read-only reference data.

    Anyone authenticated can read a default category; only the owner of a
    custom category may read/edit/delete it. Editing/deleting is never
    allowed on a default category, even by its "reader".
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return obj.user_id is None or obj.user_id == request.user.id
        return obj.user_id == request.user.id
