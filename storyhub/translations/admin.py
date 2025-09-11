# translations/admin.py
from django.contrib import admin
from .models import Translation, ParagraphNote, TranslatorAssignment

@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    list_display = ("paragraph", "translator", "is_finalized", "updated_at")
    list_filter = ("is_finalized", "translator")
    search_fields = ("text",)

@admin.register(ParagraphNote)
class ParagraphNoteAdmin(admin.ModelAdmin):
    list_display = ("paragraph", "author", "resolved", "created_at")
    list_filter = ("resolved",)

@admin.register(TranslatorAssignment)
class TranslatorAssignmentAdmin(admin.ModelAdmin):
    list_display = ("story", "translator", "status", "accepted_at", "completed_at")
    list_filter = ("status",)