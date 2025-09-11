# stories/serializers.py
from rest_framework import serializers
from .models import Language, Tag, Story, Paragraph, Illustration, Chapter
from translations.models import Translation

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ["id", "code", "name"]

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]

class IllustrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Illustration
        fields = ["id", "image_url", "position", "is_selected"]

class ParagraphSerializer(serializers.ModelSerializer):
    illustrations = IllustrationSerializer(many=True, read_only=True)

    class Meta:
        model = Paragraph
        fields = ["id", "index", "original_text", "machine_text", "illustrations"]

class StoryListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Story
        fields = ["id", "title", "slug", "status", "paragraphs_count", "translated_count", "tags", "poster_url"]


class ChapterSerializer(serializers.ModelSerializer):
    paragraphs = ParagraphSerializer(many=True, read_only=True)
    class Meta:
        model = Chapter
        fields = ["id", "index", "title", "paragraphs"]

class StoryDetailSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    paragraphs = ParagraphSerializer(many=True, read_only=True)

    class Meta:
        model = Story
        fields = [
            "id", "title", "slug", "description", "status",
            "paragraphs_count", "translated_count", "tags", "published_at",
            "poster_url", "paragraphs"
        ]


class StoryCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all(), required=False)

    class Meta:
        model = Story
        fields = ["title", "description", "original_language", "target_language", "tags"]

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        story = Story.objects.create(**validated_data)
        if tags:
            story.tags.set(tags)
        return story
