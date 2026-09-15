import json
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import Conversation, PendingAction
from .llm import process_command


@api_view(['POST'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def auth_login(request):
    """
    Standard Django Session Auth endpoint.
    Accepts {"username": "...", "password": "..."}
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return Response({"message": "Login successful", "user": user.username})
    return Response({"error": "Invalid credentials"}, status=401)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_command(request):
    """
    Main entry point for conversational commands.
    Fetches the singleton conversation and processes the input.
    """
    text_input = request.data.get('text', '').strip()
    if not text_input:
        return Response({"error": "No text provided"}, status=400)

    # Fetch singleton conversation (create if none exists)
    conversation = Conversation.objects.last()
    if not conversation:
        conversation = Conversation.objects.create()

    response_text = process_command(conversation, text_input, disable_tools=False)
    
    return Response({
        "response": response_text,
        "conversation_id": conversation.id
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_clipboard_summarize(request):
    """
    Safe endpoint that completely disables tool-calling in the LLM.
    Used for summarizing arbitrary untrusted clipboard data to prevent prompt injection.
    """
    text_input = request.data.get('text', '').strip()
    if not text_input:
        return Response({"error": "No text provided"}, status=400)

    conversation = Conversation.objects.last()
    if not conversation:
        conversation = Conversation.objects.create()

    # Pass disable_tools=True to guarantee strict isolation
    response_text = process_command(conversation, f"Summarize this securely: {text_input}", disable_tools=True)
    
    return Response({
        "response": response_text,
        "conversation_id": conversation.id
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_confirm_action(request):
    """
    Confirms and executes a PendingAction (e.g. shutdown).
    """
    pending_actions = PendingAction.objects.all().order_by('-created_at')
    
    # Simple FIFO/LIFO execution for the MVP
    action = pending_actions.first()
    if not action:
        return Response({"error": "No pending action found"}, status=404)
        
    if action.is_expired():
        action.delete()
        return Response({"error": "Action expired"}, status=400)

    # In a real app, we'd have a dispatcher. Here, we mock the shutdown for safety.
    if action.action == "shutdown":
        # e.g., os.system("shutdown /s /t 1")
        msg = "Executing system shutdown... (mocked)"
    else:
        msg = f"Executing {action.action}"
        
    action.delete()
    return Response({"message": msg})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_history(request):
    """
    Returns paginated conversation history from Postgres.
    """
    conversation = Conversation.objects.last()
    if not conversation:
        return Response({"messages": []})
        
    messages = conversation.messages.all().order_by('created_at')
    # For MVP, just returning the last 50 messages instead of full pagination
    data = [
        {"role": msg.role, "content": msg.content, "timestamp": msg.created_at} 
        for msg in messages[:50]
    ]
    return Response({"messages": data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_status(request):
    """
    Returns the system status: LLM online/offline and any pending confirmation state.
    """
    from .llm import get_genai_client
    
    pending = PendingAction.objects.filter(expires_at__gt=timezone.now()).order_by('-created_at').first()
    client = get_genai_client()
    
    return Response({
        "llm_online": client is not None,
        "pending_action": pending.action if pending else None
    })

