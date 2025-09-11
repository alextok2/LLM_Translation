# translations/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from stories.models import Paragraph, Story

User = get_user_model()

class Translation(models.Model):
    paragraph = models.ForeignKey(Paragraph, related_name="translations", on_delete=models.CASCADE)
    translator = models.ForeignKey(User, related_name="translations", on_delete=models.CASCADE)
    text = models.TextField()
    is_finalized = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("paragraph", "translator")]
        indexes = [
            models.Index(fields=["paragraph"]),
            models.Index(fields=["translator"]),
            models.Index(fields=["is_finalized"]),
        ]

    def __str__(self):
        return f"Tr p{self.paragraph_id} by {self.translator_id}"


class ParagraphNote(models.Model):
    paragraph = models.ForeignKey(Paragraph, related_name="notes", on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name="paragraph_notes", on_delete=models.CASCADE)
    text = models.TextField()
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class AssignmentStatus(models.TextChoices):
    REQUESTED = "REQUESTED", "Requested"
    ACTIVE = "ACTIVE", "Active"
    COMPLETED = "COMPLETED", "Completed"


class TranslatorAssignment(models.Model):
    story = models.ForeignKey(Story, related_name="assignments", on_delete=models.CASCADE)
    translator = models.ForeignKey(User, related_name="assignments", on_delete=models.CASCADE)
    status = models.CharField(max_length=12, choices=AssignmentStatus.choices, default=AssignmentStatus.ACTIVE)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("story", "translator")]
        indexes = [
            models.Index(fields=["story", "status"]),
            models.Index(fields=["translator", "status"]),
        ]

    def __str__(self):
        return f"{self.story_id} -> {self.translator_id} ({self.status})"