# stories/filters.py
import django_filters
from .models import Story, Tag

class StoryFilter(django_filters.FilterSet):
    tags = django_filters.CharFilter(method="filter_tags")
    status = django_filters.CharFilter(field_name="status")
    search = django_filters.CharFilter(method="filter_search")

    def filter_tags(self, qs, name, value):
        # OR логика по слагам через запятую
        slugs = [s.strip() for s in value.split(",") if s.strip()]
        if not slugs:
            return qs
        return qs.filter(tags__slug__in=slugs).distinct()

    def filter_search(self, qs, name, value):
        return qs.filter(title__icontains=value)

    class Meta:
        model = Story
        fields = ["status"]