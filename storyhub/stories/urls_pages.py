from django.urls import path
from .views_pages import CatalogView, StoryDetailView

urlpatterns = [
    path("", CatalogView.as_view(), name="catalog"),
    path("stories/<str:slug>/", StoryDetailView.as_view(), name="story_detail"),
]