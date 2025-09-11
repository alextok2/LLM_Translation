from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.shortcuts import redirect
from stories.models import Story, StoryStatus
from translations.models import Translation, ParagraphNote

def _in_group(user, name: str) -> bool:
    if not user.is_authenticated:
        return False
    if name == "admin":
        return user.is_superuser or user.is_staff or user.groups.filter(name="admin").exists()
    return user.groups.filter(name=name).exists()

class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "users/account.html"

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        user = request.user
        if action == "update_profile":
            email = (request.POST.get("email") or "").strip()
            if email:
                user.email = email
                user.save(update_fields=["email"])
            return redirect("user_account")
        if action == "become_translator":
            grp, _ = Group.objects.get_or_create(name="translator")
            user.groups.add(grp)
            return redirect("user_account")
        if action == "become_reader":
            grp, _ = Group.objects.get_or_create(name="reader")
            user.groups.add(grp)
            return redirect("user_account")
        if action == "become_admin":
            user.is_staff = True
            user.save(update_fields=["is_staff"])
            grp, _ = Group.objects.get_or_create(name="admin")
            user.groups.add(grp)
            return redirect("user_account")
        return redirect("user_account")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        is_admin = _in_group(u, "admin")
        is_translator = _in_group(u, "translator") or is_admin

        # Статистика
        available = Story.objects.filter(status=StoryStatus.DRAFT, assigned_to__isnull=True).count()
        my_in_progress = Story.objects.filter(status=StoryStatus.IN_TRANSLATION, assigned_to=u).count()
        my_review = Story.objects.filter(status=StoryStatus.REVIEW, assigned_to=u).count()
        my_published = Story.objects.filter(status=StoryStatus.PUBLISHED, assigned_to=u).count()
        review_queue = Story.objects.filter(status=StoryStatus.REVIEW).count() if is_admin else 0
        drafts_all = Story.objects.filter(status=StoryStatus.DRAFT).count() if is_admin else 0

        # Списки
        ctx["available_list"] = Story.objects.filter(status=StoryStatus.DRAFT, assigned_to__isnull=True).order_by("-id")[:6]
        ctx["in_progress_list"] = Story.objects.filter(status=StoryStatus.IN_TRANSLATION, assigned_to=u).order_by("-id")[:6]
        ctx["review_list"] = Story.objects.filter(status=StoryStatus.REVIEW, assigned_to=u).order_by("-id")[:6]

        ctx["recent_translations"] = Translation.objects.select_related("paragraph__story").filter(
            translator=u
        ).order_by("-updated_at")[:10]

        ctx["my_open_notes"] = ParagraphNote.objects.select_related("paragraph__story").filter(
            author=u, resolved=False
        ).order_by("-created_at")[:10]

        # Контекст для шаблона
        ctx["is_admin"] = is_admin
        ctx["is_translator"] = is_translator
        ctx["roles"] = list(u.groups.values_list("name", flat=True))
        ctx["stats"] = {
            "available": available,
            "in_progress": my_in_progress,
            "review": my_review,
            "published": my_published,
            "review_queue": review_queue,
            "drafts_all": drafts_all,
        }
        return ctx

class RoleSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "users/roles.html"

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        user = request.user
        if action == "become_translator":
            grp, _ = Group.objects.get_or_create(name="translator")
            user.groups.add(grp)
        if action == "become_reader":
            grp, _ = Group.objects.get_or_create(name="reader")
            user.groups.add(grp)
        if action == "become_admin":
            user.is_staff = True
            user.save(update_fields=["is_staff"])
            grp, _ = Group.objects.get_or_create(name="admin")
            user.groups.add(grp)
        return redirect("role_settings")
