# translations/serializers.py
from rest_framework import serializers
from .models import Translation, ParagraphNote, TranslatorAssignment
from stories.models import Paragraph

class TranslationSerializer(serializers.ModelSerializer):
    paragraph = serializers.PrimaryKeyRelatedField(queryset=Paragraph.objects.all())
    class Meta:
        model = Translation
        fields = ["id", "paragraph", "text", "is_finalized", "updated_at"]
        read_only_fields = ["updated_at"]

class ParagraphNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParagraphNote
        fields = ["id", "paragraph", "author", "text", "resolved", "created_at"]
        read_only_fields = ["author", "created_at"]

class TranslatorAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranslatorAssignment
        fields = ["id", "story", "translator", "status", "accepted_at", "completed_at"]
        read_only_fields = ["accepted_at", "completed_at"]