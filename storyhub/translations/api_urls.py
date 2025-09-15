# translations/api_urls.py
from django.urls import path
from .views import ParagraphTranslationView, NoteCreateView, NoteUpdateView, IllustrationSelectView
from .views_me import CompletedStoriesView, AvailableStoriesView

urlpatterns = [
    # Перевод абзаца (GET – HTML partial для HTMX; PUT/PATCH – сохранение)
    
    path("paragraphs/<int:pk>/translation/", ParagraphTranslationView.as_view(), name="paragraph-translation"),

    # Заметки
    path("notes/", NoteCreateView.as_view(), name="notes_create"),
    path("notes/<int:note_id>/", NoteUpdateView.as_view(), name="notes_update"),

    # Иллюстрации
    path("illustrations/<int:illustration_id>/select/", IllustrationSelectView.as_view(), name="illustration_select"),

    # Личный раздел переводчика
    path("me/completed-stories/", CompletedStoriesView.as_view(), name="me_completed_stories"),
    path("translate/available-stories/", AvailableStoriesView.as_view(), name="available_stories"),
]