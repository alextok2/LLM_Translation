# stories/admin.py
from django.contrib import admin
from .models import Language, Tag, Story, Paragraph, Illustration, Chapter

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

class IllustrationInline(admin.TabularInline):
    model = Illustration
    extra = 0

class ParagraphAdmin(admin.ModelAdmin):
    list_display = ("story", "index")
    list_filter = ("story",)
    inlines = [IllustrationInline]

@admin.register(Paragraph)
class _Paragraph(ParagraphAdmin):
    pass

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ("story", "index", "title")
    list_filter = ("story",)
    search_fields = ("title",)

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "original_language", "target_language", "assigned_to", "paragraphs_count", "translated_count", "published_at")
    list_filter = ("status", "original_language", "target_language", "tags")
    search_fields = ("title", "description")
    filter_horizontal = ("tags",)