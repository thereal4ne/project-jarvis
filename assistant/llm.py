import os
import logging
from google import genai
from google.genai import types
from datetime import timedelta
from django.utils import timezone
from .models import Message, PendingAction
from .tools import ALL_TOOLS, TOOL_MAP

logger = logging.getLogger(__name__)

# Initialize client using standard GEMINI_API_KEY from environment
try:
    genai_client = genai.Client()
except Exception as e:
    genai_client = None
    logger.warning(f"Could not initialize Gemini Client: {e}")

LLM_MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """You are Jarvis, a powerful AI assistant running locally via a web interface.
You have access to tools that can control the user's PC (volume, windows, power).
Always be concise, professional, and helpful."""


def format_history_for_gemini(messages):
    """Converts Django Message models into Google GenAI history format."""
    history = []
    for msg in messages:
        # GenAI uses "user" and "model" roles
        history.append({"role": msg.role, "parts": [{"text": msg.content}]})
    return history


def process_command(conversation, text_input: str, disable_tools: bool = False) -> str:
    """
    Main orchestration loop:
    1. Fetch history.
    2. Call LLM (with or without tools).
    3. Execute tools if requested, tracking results.
    4. Return the final string.
    """
    if not genai_client:
        return "Error: Gemini Client is not initialized (missing API Key)."

    # Save user message to DB
    Message.objects.create(conversation=conversation, role='user', content=text_input)

    # Fetch last 10 messages for context window
    recent_msgs = conversation.messages.all().order_by('created_at')[:10]
    history = format_history_for_gemini(recent_msgs)

    # Prepare config
    tools_to_pass = [] if disable_tools else ALL_TOOLS
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=tools_to_pass,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=True
        ),
        temperature=0.4
    )

    try:
        response = genai_client.models.generate_content(
            model=LLM_MODEL,
            contents=history,
            config=config
        )
    except Exception as e:
        logger.error(f"LLM Error: {e}")
        return "I encountered an error connecting to my neural network."

    final_text = ""

    # Handle Tool Calls
    if response.function_calls:
        results = []
        for call in response.function_calls:
            fn = TOOL_MAP.get(call.name)
            if fn:
                args_dict = getattr(call, 'args', {})
                if hasattr(args_dict, 'to_dict'):
                    args_dict = args_dict.to_dict()
                elif not isinstance(args_dict, dict):
                    args_dict = dict(args_dict) if args_dict else {}

                try:
                    msg_result = fn(**args_dict)
                    
                    # Intercept special PendingAction signals
                    if msg_result == "__PENDING_ACTION_SHUTDOWN__":
                        PendingAction.objects.create(
                            action="shutdown",
                            expires_at=timezone.now() + timedelta(minutes=1)
                        )
                        msg_result = "Shutdown requested. Please confirm this action."
                        
                    results.append(msg_result)
                except Exception as e:
                    logger.error(f"Tool {call.name} error: {e}")
                    results.append(f"Failed to execute {call.name}.")
                    
        final_text = ", and ".join(results)
    
    elif response.text:
        final_text = response.text
    else:
        final_text = "Done."

    # Save assistant response to DB
    Message.objects.create(conversation=conversation, role='model', content=final_text)

    return final_text
