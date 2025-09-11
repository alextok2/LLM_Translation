# stories/views_pages.py
from django.views.generic import ListView, DetailView
from .models import Story, StoryStatus
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import Group

class CatalogView(ListView):
    template_name = "stories/catalog.html"
    context_object_name = "stories"
    paginate_by = 20

    def get_queryset(self):
        qs = Story.objects.filter(status=StoryStatus.PUBLISHED).prefetch_related("tags")
        tags = self.request.GET.get("tags")
        search = self.request.GET.get("search")
        if tags:
            slugs = [s.strip() for s in tags.split(",") if s.strip()]
            qs = qs.filter(tags__slug__in=slugs).distinct()
        if search:
            qs = qs.filter(title__icontains=search)
        return qs
    




class StoryDetailView(DetailView):
    template_name = "stories/story_detail.html"
    context_object_name = "story"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_object(self):
        return get_object_or_404(Story, slug=self.kwargs["slug"], status=StoryStatus.PUBLISHED)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        story = self.object
        user_id = story.assigned_to_id

        chapters_qs = story.chapters.all().prefetch_related("paragraphs__illustrations", "paragraphs__translations")
        if chapters_qs.exists():
            ch_list = []
            for ch in chapters_qs:
                items = []
                for p in ch.paragraphs.all().order_by("index"):
                    tr = p.translations.filter(translator_id=user_id, is_finalized=True).first()
                    text = tr.text if tr else ""
                    items.append({"text": text, "illustrations": p.illustrations.filter(is_selected=True)[:5]})
                ch_list.append({"index": ch.index, "title": ch.title, "items": items})
            ctx["chapters"] = ch_list
        else:
            items = []
            for p in story.paragraphs.all().prefetch_related("illustrations"):
                tr = p.translations.filter(translator_id=user_id, is_finalized=True).first()
                items.append({"text": tr.text if tr else "", "illustrations": p.illustrations.filter(is_selected=True)[:5]})
            ctx["content"] = items
        return ctx