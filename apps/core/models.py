import uuid

from django.db import models


class BaseModel(models.Model):
    """Abstract base for domain models added from Phase 2 onward.

    UUID primary keys avoid leaking sequential IDs (e.g. transaction counts)
    to clients, which matters once financial resources are exposed over the
    API.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
