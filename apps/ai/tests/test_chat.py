from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.ai.models import AIConversation, AIMessage
from apps.ai.tests.factories import AIConversationFactory
from apps.users.tests.factories import UserFactory


def authed_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


URL = "/api/v1/ai/chat/"


@pytest.mark.django_db
class TestChat:
    @patch("apps.ai.llm.generate")
    def test_new_conversation_is_created_and_messages_stored(self, mock_generate):
        user = UserFactory()
        mock_generate.return_value = "You have $100 available."

        response = authed_client(user).post(URL, {"message": "How much can I spend?"})

        assert response.status_code == 200
        data = response.data["data"]
        assert data["message"] == "You have $100 available."
        conversation = AIConversation.objects.get(id=data["conversation_id"])
        assert conversation.user == user
        messages = list(conversation.messages.order_by("created_at"))
        assert [m.role for m in messages] == [AIMessage.Role.USER, AIMessage.Role.ASSISTANT]
        assert messages[0].content == "How much can I spend?"

    @patch("apps.ai.llm.generate")
    def test_continues_an_existing_conversation(self, mock_generate):
        user = UserFactory()
        conversation = AIConversationFactory(user=user)
        mock_generate.return_value = "Sure."

        response = authed_client(user).post(
            URL, {"message": "Follow up", "conversation_id": str(conversation.id)}
        )

        assert response.status_code == 200
        assert response.data["data"]["conversation_id"] == str(conversation.id)
        assert conversation.messages.count() == 2

    @patch("apps.ai.llm.generate")
    def test_cannot_continue_another_users_conversation(self, mock_generate):
        owner = UserFactory()
        attacker = UserFactory()
        conversation = AIConversationFactory(user=owner)

        response = authed_client(attacker).post(
            URL, {"message": "hi", "conversation_id": str(conversation.id)}
        )

        assert response.status_code == 404
        mock_generate.assert_not_called()

    def test_requires_authentication(self):
        response = APIClient().post(URL, {"message": "hi"})

        assert response.status_code == 401
