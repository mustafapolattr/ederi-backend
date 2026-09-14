from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Object-level check that a resource belongs to the requesting user.

    Every future model exposing user-owned data (accounts, transactions,
    budgets, ...) must be filtered by owner at the queryset level AND checked
    here, to defend against IDOR (spec §42).
    """

    owner_field = "user_id"

    def has_object_permission(self, request, view, obj):
        owner_id = getattr(obj, self.owner_field, None)
        return owner_id is not None and owner_id == request.user.id
