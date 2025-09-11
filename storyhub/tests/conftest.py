# translations/views_pages.py
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from users.permissions import in_group
from stories.models import Story, StoryStatus

class TranslatorDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "translations/dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if not in_group(request.user, "translator") and not in_group(request.user, "admin"):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        user = self.request.user
        ctx = super().get_context_data(**kwargs)
        ctx["available"] = Story.objects.filter(status__in=[StoryStatus.DRAFT, StoryStatus.IN_TRANSLATION], assigned_to__isnull=True)
        ctx["in_progress"] = Story.objects.filter(status=StoryStatus.IN_TRANSLATION, assigned_to=user)
        ctx["completed"] = Story.objects.filter(status__in=[StoryStatus.REVIEW, StoryStatus.PUBLISHED], assigned_to=user)
        return ctx

class EditorView(LoginRequiredMixin, TemplateView):
    template_name = "translations/editor.html"

    def dispatch(self, request, *args, **kwargs):
        if not in_group(request.user, "translator") and not in_group(request.user, "admin"):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, slug, **kwargs):
        ctx = super().get_context_data(**kwargs)
        story = get_object_or_404(Story, slug=slug)
        user = self.request.user
        if in_group(user, "translator") and story.assigned_to_id != user.id:
            self.raise_exception = True
            raise PermissionError("Not assigned")
        ctx["story"] = story
        ctx["paragraphs"] = story.paragraphs.all().prefetch_related("illustrations")
        return ctx