from django.urls import path
from .views_pages import TranslatorDashboardView, EditorView, StoriesByStatusView, StoryPreviewView, StoryPreviewByIdView, EditorByIdView

urlpatterns = [
    path("translator/dashboard/", TranslatorDashboardView.as_view(), name="translator_dashboard"),
    path("translator/stories/", StoriesByStatusView.as_view(), name="translator_stories_by_status"),
    path("translator/story/<str:slug>/", StoryPreviewView.as_view(), name="translator_story_preview"),
    path("translator/story/id/<int:pk>/", StoryPreviewByIdView.as_view(), name="translator_story_preview_by_id"),
    path("translator/editor/<str:slug>/", EditorView.as_view(), name="editor"),
    path("translator/editor/id/<int:pk>/", EditorByIdView.as_view(), name="editor_by_id"),
]