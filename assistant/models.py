from django.db import models
from django.utils import timezone

class Conversation(models.Model):
    """
    Represents a discrete chat session.
    For the initial scope, a singleton row will be used.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation {self.id} ({self.created_at.date()})"


class Message(models.Model):
    """
    Represents a single message within a conversation.
    Role can be 'user' or 'model'.
    """
    ROLE_CHOICES = (
        ('user', 'User'),
        ('model', 'Model'),
    )

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.role}] {self.content[:50]}..."


class PendingAction(models.Model):
    """
    Stores a destructive command (e.g. shutdown, kill process) that is awaiting user confirmation.
    """
    action = models.CharField(max_length=100)
    context = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"PendingAction: {self.action} (Expires: {self.expires_at})"
