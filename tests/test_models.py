import pytest
from django.utils import timezone
from datetime import timedelta
from assistant.models import Conversation, Message, PendingAction

@pytest.mark.django_db
def test_conversation_and_message_ordering():
    conv = Conversation.objects.create()
    msg1 = Message.objects.create(conversation=conv, role='user', content='First')
    msg2 = Message.objects.create(conversation=conv, role='model', content='Second')
    
    # Validate ordering is by created_at ascending
    messages = list(conv.messages.all())
    assert messages == [msg1, msg2]
    
    # Validate string representation
    assert str(msg1) == "[user] First..."
    assert str(msg2) == "[model] Second..."

@pytest.mark.django_db
def test_pending_action_expiration():
    # Valid action
    valid_action = PendingAction.objects.create(
        action='shutdown',
        expires_at=timezone.now() + timedelta(minutes=5)
    )
    assert not valid_action.is_expired()
    
    # Expired action
    expired_action = PendingAction.objects.create(
        action='shutdown',
        expires_at=timezone.now() - timedelta(minutes=5)
    )
    assert expired_action.is_expired()
