import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from assistant.models import Conversation, Message, PendingAction
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import timedelta

@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def auth_client(client):
    user = User.objects.create_user(username='admin', password='password')
    client.force_authenticate(user=user)
    return client

@pytest.mark.django_db
def test_auth_login(client):
    User.objects.create_user(username='admin', password='password')
    response = client.post(reverse('auth-login'), {'username': 'admin', 'password': 'password'})
    assert response.status_code == 200
    assert response.json()['message'] == 'Login successful'
    
    # Test invalid login
    bad_response = client.post(reverse('auth-login'), {'username': 'admin', 'password': 'wrong'})
    assert bad_response.status_code == 401

@pytest.mark.django_db
def test_unauthenticated_access(client):
    response = client.post(reverse('api-command'), {'text': 'hello'})
    # DRF defaults to 401 Unauthorized or 403 Forbidden based on exact setup, usually 403 when session is missing
    assert response.status_code in [401, 403]

@pytest.mark.django_db
@patch('assistant.llm.get_genai_client')
def test_api_command(mock_get_client, auth_client):
    mock_genai = MagicMock()
    mock_get_client.return_value = mock_genai

    # Mock Gemini response
    mock_response = MagicMock()
    mock_response.text = "Hello sir."
    mock_response.function_calls = None
    mock_genai.models.generate_content.return_value = mock_response

    response = auth_client.post(reverse('api-command'), {'text': 'Wake up'}, format='json')
    
    assert response.status_code == 200
    assert response.json()['response'] == "Hello sir."
    
    # Verify DB records
    assert Conversation.objects.count() == 1
    conv = Conversation.objects.first()
    msgs = conv.messages.all()
    assert msgs.count() == 2
    assert msgs[0].role == 'user'
    assert msgs[0].content == 'Wake up'
    assert msgs[1].role == 'model'
    assert msgs[1].content == 'Hello sir.'

@pytest.mark.django_db
@patch('assistant.llm.get_genai_client')
def test_api_command_with_tools(mock_get_client, auth_client):
    mock_genai = MagicMock()
    mock_get_client.return_value = mock_genai

    # Mock Gemini response with function calls
    mock_response = MagicMock()
    mock_response.text = None
    
    mock_call = MagicMock()
    mock_call.name = "tool_volume_mute"
    mock_call.args = {}
    
    mock_shutdown = MagicMock()
    mock_shutdown.name = "tool_request_pc_shutdown"
    mock_shutdown.args = {}
    
    mock_response.function_calls = [mock_call, mock_shutdown]
    mock_genai.models.generate_content.return_value = mock_response

    response = auth_client.post(reverse('api-command'), {'text': 'Mute and shutdown'}, format='json')
    assert response.status_code == 200
    
    # Verify results combined correctly
    text_resp = response.json()['response']
    assert "muted" in text_resp.lower()
    assert "Shutdown requested" in text_resp
    
    # Verify PendingAction was created
    assert PendingAction.objects.filter(action="shutdown").count() == 1

@pytest.mark.django_db
@patch('assistant.llm.get_genai_client')
def test_clipboard_summarize_isolation(mock_get_client, auth_client):
    mock_genai = MagicMock()
    mock_get_client.return_value = mock_genai

    # Mock response
    mock_response = MagicMock()
    mock_response.text = "Summary text."
    mock_response.function_calls = None
    mock_genai.models.generate_content.return_value = mock_response

    response = auth_client.post(reverse('api-clipboard-summarize'), {'text': 'Huge code block'}, format='json')
    assert response.status_code == 200
    
    # Verify the LLM was called with empty tools array
    call_args = mock_genai.models.generate_content.call_args
    config_arg = call_args[1]['config']
    assert config_arg.tools == []

@pytest.mark.django_db
def test_pending_action_persistence(auth_client):
    # Create action directly in DB (simulating a previous request)
    action = PendingAction.objects.create(
        action='shutdown',
        expires_at=timezone.now() + timedelta(minutes=5)
    )
    
    # Hit confirm endpoint in a separate request
    response = auth_client.post(reverse('api-confirm-action'))
    assert response.status_code == 200
    assert "shutdown" in response.json()['message']
    
    # Verify action is deleted after execution
    assert PendingAction.objects.count() == 0

@pytest.mark.django_db
def test_pending_action_expired(auth_client):
    # Create expired action
    action = PendingAction.objects.create(
        action='shutdown',
        expires_at=timezone.now() - timedelta(minutes=5)
    )
    
    response = auth_client.post(reverse('api-confirm-action'))
    assert response.status_code == 400
    assert response.json()['error'] == 'Action expired'
    assert PendingAction.objects.count() == 0
