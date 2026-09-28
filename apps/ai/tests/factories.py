import factory

from apps.ai.models import AIConversation, AIMessage
from apps.users.tests.factories import UserFactory


class AIConversationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AIConversation

    user = factory.SubFactory(UserFactory)


class AIMessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AIMessage

    conversation = factory.SubFactory(AIConversationFactory)
    role = AIMessage.Role.USER
    content = "Hello"
