# stories/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.urls import reverse

from .models import Story, StoryStatus, Paragraph, Illustration
from .serializers import StoryListSerializer, StoryDetailSerializer, ParagraphSerializer, IllustrationSerializer, StoryCreateSerializer
from .filters import StoryFilter
from users.permissions import IsAdminGroup, IsTranslatorGroup
from .services import parse_story_paragraphs, parse_story_with_chapters
from translations.models import TranslatorAssignment, AssignmentStatus, Translation
from rest_framework.permissions import IsAuthenticatedOrReadOnly


class StoryViewSet(viewsets.ModelViewSet):
    queryset = Story.objects.all().prefetch_related("tags")
    filterset_class = StoryFilter
    search_fields = ["title"]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ["list"]:
            return StoryListSerializer
        return StoryDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated or not (user.groups.filter(name__in=["admin", "translator"]).exists()):
            qs = qs.filter(status=StoryStatus.PUBLISHED)
        return qs

    def create(self, request, *args, **kwargs):
        if not IsAdminGroup().has_permission(request, self):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = StoryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        story = serializer.save(status=StoryStatus.DRAFT)
        return Response(StoryDetailSerializer(story).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="preview-paragraphs")
    def preview_paragraphs(self, request, pk=None):
        if not (IsAdminGroup().has_permission(request, self) or IsTranslatorGroup().has_permission(request, self)):
            return Response(status=status.HTTP_403_FORBIDDEN)
        story = self.get_object()
        qs = story.paragraphs.all().prefetch_related("illustrations")
        return Response(ParagraphSerializer(qs, many=True).data)

    @action(detail=False, methods=["post"], url_path="import")
    def import_story(self, request):
        # admin only
        if not IsAdminGroup().has_permission(request, self):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # 1) создаём историю
        create_ser = StoryCreateSerializer(data=request.data)
        create_ser.is_valid(raise_exception=True)
        story = create_ser.save(status=StoryStatus.DRAFT)

        # 2) парсим абзацы
        chapters = request.data.get("chapters")
        if isinstance(chapters, list) and chapters:
            count = parse_story_with_chapters(story, chapters)
            ch_count = len(chapters)
        else:
            original_text = request.data.get("original_text", "") or ""
            machine_text = request.data.get("machine_text", "") or ""  # если пусто — ок, «без перевода»
            count = parse_story_paragraphs(story, original_text, machine_text)
            ch_count = 1 if original_text or machine_text else 0

        return Response({
            "ok": True,
            "story": StoryDetailSerializer(story).data,
            "paragraphs": count,
            "chapters": ch_count
        }, status=status.HTTP_201_CREATED)


    @action(detail=True, methods=["post"])
    def parse(self, request, pk=None):
        if not IsAdminGroup().has_permission(request, self):
            return Response(status=status.HTTP_403_FORBIDDEN)
        story = self.get_object()
        chapters = request.data.get("chapters")
        if isinstance(chapters, list) and chapters:
            count = parse_story_with_chapters(story, chapters)
            return Response({"ok": True, "paragraphs": count, "chapters": len(chapters)})
        original_text = request.data.get("original_text", "") or ""
        machine_text = request.data.get("machine_text", "") or ""
        parse_story_paragraphs(story, original_text, machine_text)
        return Response({"ok": True, "paragraphs": story.paragraphs_count, "chapters": 1 if (original_text or machine_text) else 0})


    @action(detail=True, methods=["post"])
    def claim(self, request, pk=None):
        if not IsTranslatorGroup().has_permission(request, self):
            return Response(status=status.HTTP_403_FORBIDDEN)
        story = self.get_object()
        if story.assigned_to_id:
            return Response({"detail": "Story already assigned"}, status=status.HTTP_409_CONFLICT)

        with transaction.atomic():
            ass, created = TranslatorAssignment.objects.get_or_create(
                story=story,
                translator=request.user,
                defaults={"status": AssignmentStatus.ACTIVE, "accepted_at": timezone.now()},
            )
            if not created and ass.status == AssignmentStatus.COMPLETED:
                return Response({"detail": "Already completed by you"}, status=status.HTTP_409_CONFLICT)

        # Редирект в редактор
        if story.slug:
            editor_url = reverse("editor", kwargs={"slug": story.slug})
        else:
            editor_url = reverse("editor_by_id", kwargs={"pk": story.pk})

        return Response({"ok": True}, headers={"HX-Redirect": editor_url})

    @action(detail=True, methods=["get"])
    def paragraphs(self, request, pk=None):
        story = self.get_object()
        user = request.user
        if not (user.is_authenticated and (user.groups.filter(name="admin").exists() or (user.groups.filter(name="translator").exists() and story.assigned_to_id == user.id))):
            return Response(status=status.HTTP_403_FORBIDDEN)
        qs = story.paragraphs.all().prefetch_related("illustrations")
        return Response(ParagraphSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        # translator: все абзацы финализированы
        if not IsTranslatorGroup().has_permission(request, self):
            return Response(status=status.HTTP_403_FORBIDDEN)
        story = self.get_object()
        if story.assigned_to_id != request.user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        total = story.paragraphs_count
        finalized = Translation.objects.filter(paragraph__story=story, translator=request.user, is_finalized=True).values("paragraph_id").distinct().count()
        if finalized != total:
            return Response({"detail": "Not all paragraphs finalized"}, status=status.HTTP_400_BAD_REQUEST)
        # помечаем assignment COMPLETED и story -> REVIEW
        TranslatorAssignment.objects.filter(story=story, translator=request.user, status=AssignmentStatus.ACTIVE).update(status=AssignmentStatus.COMPLETED, completed_at=timezone.now())
        story.status = StoryStatus.REVIEW
        story.save(update_fields=["status"])
        return Response({"ok": True, "status": story.status})

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        # admin only
        if not IsAdminGroup().has_permission(request, self):
            return Response(status=status.HTTP_403_FORBIDDEN)
        story = self.get_object()
        if story.status not in [StoryStatus.REVIEW, StoryStatus.PUBLISHED]:
            return Response({"detail": "Story must be in REVIEW"}, status=status.HTTP_400_BAD_REQUEST)
        total = story.paragraphs_count
        if story.assigned_to_id is None:
            return Response({"detail": "No assigned translator"}, status=400)
        finalized = Translation.objects.filter(paragraph__story=story, translator_id=story.assigned_to_id, is_finalized=True).values("paragraph_id").distinct().count()
        if finalized != total:
            return Response({"detail": "Not all paragraphs finalized"}, status=status.HTTP_400_BAD_REQUEST)
        story.status = StoryStatus.PUBLISHED
        story.published_at = timezone.now()
        story.save(update_fields=["status", "published_at"])
        return Response({"ok": True, "status": story.status})