# translations/views_pages.py
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from users.permissions import in_group
from stories.models import Story, StoryStatus
from .models import TranslatorAssignment, AssignmentStatus
from django.utils import timezone
from django.db import transaction
from django.db.models import Prefetch

from stories.models import Story, Paragraph, Illustration, StoryStatus
from translations.models import Translation

def _stories_for_status(user, status: str):
    is_admin = in_group(user, "admin")
    is_translator = in_group(user, "translator")

    qs = Story.objects.none()
    if status == StoryStatus.DRAFT:
        qs = Story.objects.filter(status=StoryStatus.DRAFT)
        if is_translator and not is_admin:
            qs = qs.filter(assigned_to__isnull=True)
    elif status == StoryStatus.IN_TRANSLATION:
        qs = Story.objects.filter(status=StoryStatus.IN_TRANSLATION)
        if is_translator and not is_admin:
            qs = qs.filter(assigned_to=user)
    elif status == StoryStatus.REVIEW:
        qs = Story.objects.filter(status=StoryStatus.REVIEW)
        if is_translator and not is_admin:
            qs = qs.filter(assigned_to=user)
    return qs.select_related("original_language", "target_language").prefetch_related("tags").order_by("-id")


def _counts(user):
    return {
        "DRAFT": _stories_for_status(user, StoryStatus.DRAFT).count(),
        "IN_TRANSLATION": _stories_for_status(user, StoryStatus.IN_TRANSLATION).count(),
        "REVIEW": _stories_for_status(user, StoryStatus.REVIEW).count(),
    }


class TranslatorDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "translations/dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if not (in_group(request.user, "translator") or in_group(request.user, "admin")):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        is_admin = in_group(user, "admin")
        is_translator = in_group(user, "translator")
        counts = _counts(user)

        # Логика выбора стартовой вкладки
        if is_admin:
            initial_status = StoryStatus.DRAFT
        else:
            if counts["IN_TRANSLATION"] > 0:
                initial_status = StoryStatus.IN_TRANSLATION
            elif counts["DRAFT"] > 0:
                initial_status = StoryStatus.DRAFT
            elif counts["REVIEW"] > 0:
                initial_status = StoryStatus.REVIEW
            else:
                initial_status = StoryStatus.IN_TRANSLATION

        ctx["initial_status"] = initial_status
        ctx["stories_initial"] = _stories_for_status(user, initial_status)
        ctx["counts"] = counts
        ctx["is_admin"] = is_admin
        ctx["is_translator"] = is_translator
        return ctx



class StoriesByStatusView(LoginRequiredMixin, TemplateView):
    template_name = "translations/_stories_list.html"

    def dispatch(self, request, *args, **kwargs):
        if not (in_group(request.user, "translator") or in_group(request.user, "admin")):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        status = self.request.GET.get("status", StoryStatus.IN_TRANSLATION)
        user = self.request.user
        ctx["status"] = status
        ctx["stories"] = _stories_for_status(user, status)
        ctx["is_admin"] = in_group(user, "admin")
        ctx["is_translator"] = in_group(user, "translator")
        return ctx


class StoryPreviewView(LoginRequiredMixin, TemplateView):
    template_name = "translations/preview.html"

    def dispatch(self, request, *args, **kwargs):
        if not (in_group(request.user, "translator") or in_group(request.user, "admin")):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, slug, **kwargs):
        ctx = super().get_context_data(**kwargs)
        story = get_object_or_404(
            Story.objects.prefetch_related(
                "tags",
                Prefetch(
                    "paragraphs",
                    queryset=Paragraph.objects.order_by("index").prefetch_related(
                        Prefetch("illustrations", queryset=Illustration.objects.order_by("position"))
                    )
                )
            ),
            slug=slug
        )
        ctx["story"] = story

        show_all = self.request.GET.get("show") == "all"
        mode = self.request.GET.get("mode", "original")  # по умолчанию безопаснее original
        draft = self.request.GET.get("draft") == "1"
        ctx["show_all"] = show_all
        ctx["mode"] = mode
        ctx["draft"] = draft

        paragraphs = list(story.paragraphs.all())

        if mode == "translated":
            translator_id = story.assigned_to_id or self.request.user.id
            trs = Translation.objects.filter(paragraph__story=story, translator_id=translator_id)
            if not draft:
                trs = trs.filter(is_finalized=True)
            by_pid = {t.paragraph_id: t for t in trs}

            items = []
            for p in paragraphs:
                t = by_pid.get(p.id)
                if not t:
                    continue  # если draft=1 и перевода нет — пропускаем; можно делать фоллбэк на MT по желанию
                items.append({
                    "text": t.text,
                    "illustrations": list(p.illustrations.filter(is_selected=True)[:5]),
                })

            ctx["content"] = items if show_all else items[:5]
        else:
            # original + machine translation
            ctx["paragraphs"] = paragraphs if show_all else paragraphs[:5]

        return ctx



class EditorView(LoginRequiredMixin, TemplateView):
    template_name = "translations/editor.html"

    def dispatch(self, request, *args, **kwargs):
        if not (in_group(request.user, "translator") or in_group(request.user, "admin")):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, slug, **kwargs):
        ctx = super().get_context_data(**kwargs)
        story = get_object_or_404(Story, slug=slug)
        user = self.request.user

        is_translator_only = in_group(user, "translator") and not in_group(user, "admin")

        if is_translator_only:
            # Если история не назначена этому переводчику, пытаемся её "захватить".
            if story.assigned_to_id != user.id:
                # Вся логика назначения должна быть в одной транзакции.
                with transaction.atomic():
                    # 1. Создаем или обновляем запись о назначении.
                    TranslatorAssignment.objects.update_or_create(
                        story=story,
                        translator=user,
                        defaults={'status': AssignmentStatus.ACTIVE, 'accepted_at': timezone.now()}
                    )

                    # 2. ЯВНО обновляем саму историю. Не полагаемся на сигнал.
                    story.assigned_to = user
                    story.status = StoryStatus.IN_TRANSLATION
                    story.save(update_fields=["assigned_to", "status"])

            # Финальная проверка. После нашей логики история ДОЛЖНА быть назначена.
            # Если нет - значит, что-то пошло не так (например, конфликт с другим процессом).
            if story.assigned_to_id != user.id:
                raise PermissionError("Could not assign story. It might be taken by another translator.")

        ctx["story"] = story
        chapters = story.chapters.all().prefetch_related("paragraphs__illustrations").order_by("index")
        if chapters.exists():
            ctx["chapters"] = chapters
        else:
            ctx["paragraphs"] = story.paragraphs.all().prefetch_related("illustrations")
        return ctx



class StoryPreviewByIdView(LoginRequiredMixin, TemplateView):
    template_name = "translations/preview.html"
    def dispatch(self, request, *args, **kwargs):
        if not (in_group(request.user, "translator") or in_group(request.user, "admin")):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    def get_context_data(self, pk, **kwargs):
        ctx = super().get_context_data(**kwargs)
        story = get_object_or_404(Story.objects.prefetch_related("tags", "paragraphs__illustrations"), pk=pk)
        ctx["story"] = story
        show_all = self.request.GET.get("show") == "all"
        paragraphs = story.paragraphs.all().order_by("index")
        ctx["paragraphs"] = paragraphs if show_all else paragraphs[:5]
        ctx["show_all"] = show_all
        return ctx
    
class EditorByIdView(LoginRequiredMixin, TemplateView):
    template_name = "translations/editor.html"

    def dispatch(self, request, *args, **kwargs):
        if not (in_group(request.user, "translator") or in_group(request.user, "admin")):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
        
    def get_context_data(self, pk, **kwargs):
        ctx = super().get_context_data(**kwargs)
        story = get_object_or_404(Story, pk=pk)
        user = self.request.user

        is_translator_only = in_group(user, "translator") and not in_group(user, "admin")

        if is_translator_only:
            # Точно такая же явная логика, как в EditorView
            if story.assigned_to_id != user.id:
                with transaction.atomic():
                    TranslatorAssignment.objects.update_or_create(
                        story=story,
                        translator=user,
                        defaults={'status': AssignmentStatus.ACTIVE, 'accepted_at': timezone.now()}
                    )
                    story.assigned_to = user
                    story.status = StoryStatus.IN_TRANSLATION
                    story.save(update_fields=["assigned_to", "status"])

            if story.assigned_to_id != user.id:
                raise PermissionError("Could not assign story. It might be taken by another translator.")

        ctx["story"] = story
        chapters = story.chapters.all().prefetch_related("paragraphs__illustrations").order_by("index")
        ctx["chapters"] = chapters if chapters.exists() else None
        if not ctx["chapters"]:
            ctx["paragraphs"] = story.paragraphs.all().prefetch_related("illustrations")
        return ctx

