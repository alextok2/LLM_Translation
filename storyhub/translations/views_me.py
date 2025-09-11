# translations/views_me.py
from rest_framework.views import APIView
from rest_framework.response import Response
from users.permissions import IsTranslatorGroup
from stories.models import Story, StoryStatus
from stories.serializers import StoryListSerializer

class CompletedStoriesView(APIView):
    def get(self, request):
        if not IsTranslatorGroup().has_permission(request, self):
            return Response(status=403)
        user = request.user
        qs = Story.objects.filter(assigned_to=user, status__in=[StoryStatus.REVIEW, StoryStatus.PUBLISHED])
        return Response(StoryListSerializer(qs, many=True).data)

class AvailableStoriesView(APIView):
    def get(self, request):
        if not IsTranslatorGroup().has_permission(request, self):
            return Response(status=403)
        qs = Story.objects.filter(status__in=[StoryStatus.DRAFT, StoryStatus.IN_TRANSLATION], assigned_to__isnull=True)
        return Response(StoryListSerializer(qs, many=True).data)