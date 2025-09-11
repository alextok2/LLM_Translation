# translations/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.permissions import IsTranslatorGroup, IsAdminGroup
from .models import Translation, ParagraphNote
from stories.models import Paragraph, Illustration
from .serializers import TranslationSerializer, ParagraphNoteSerializer
from django.template.loader import render_to_string


def _to_bool(v):
    if isinstance(v, bool):
        return v
    return str(v).lower() in ["true", "1", "yes", "on"]


class ParagraphTranslationView(APIView):
    def get(self, request, paragraph_id: int):
        p = Paragraph.objects.select_related("story").get(pk=paragraph_id)
        user = request.user
        if not user.is_authenticated:
            return Response(status=401)
        if not (IsAdminGroup().has_permission(request, self) or (IsTranslatorGroup().has_permission(request, self) and p.story.assigned_to_id == user.id)):
            return Response(status=403)
        tr = Translation.objects.filter(paragraph=p, translator=user).first()
        if tr:
            data = TranslationSerializer(tr).data
        else:
            # подсказка: если нет перевода, подставить machine_text
            data = {"id": None, "paragraph": p.id, "text": p.machine_text, "is_finalized": False, "updated_at": None}
        context = {
            "paragraph": p,
            "text": tr.text if tr else p.machine_text,
            "is_finalized": tr.is_finalized if tr else False
        }
        html = render_to_string("translations/_translation_form.html", context, request=request)
        return Response(html)

    def put(self, request, paragraph_id: int):
        return self._upsert(request, paragraph_id, full=True)

    def patch(self, request, paragraph_id: int):
        return self._upsert(request, paragraph_id, full=False)


    def _upsert(self, request, paragraph_id: int, full: bool):
        p = Paragraph.objects.select_related("story").get(pk=paragraph_id)
        user = request.user
        if not user.is_authenticated:
            return Response(status=401)
        if not (IsAdminGroup().has_permission(request, self) or (IsTranslatorGroup().has_permission(request, self) and p.story.assigned_to_id == user.id)):
            return Response(status=403)
        tr, created = Translation.objects.get_or_create(paragraph=p, translator=user, defaults={"text": "", "is_finalized": False})
        data = request.data
        if full:
            if "text" in data:
                tr.text = data.get("text", tr.text)
            if "is_finalized" in data:
                tr.is_finalized = _to_bool(data.get("is_finalized", tr.is_finalized))
        else:
            if "text" in data:
                tr.text = data["text"]
            if "is_finalized" in data:
                tr.is_finalized = _to_bool(data["is_finalized"])

        tr.save()
        return Response(TranslationSerializer(tr).data, status=201 if created else 200)

class NoteCreateView(APIView):
    def post(self, request):
        user = request.user
        if not (IsAdminGroup().has_permission(request, self) or IsTranslatorGroup().has_permission(request, self)):
            return Response(status=403)

        paragraph_id = request.data.get("paragraph")
        try:
            p = Paragraph.objects.select_related("story").get(pk=paragraph_id)
        except Paragraph.DoesNotExist:
            return Response({"detail": "Paragraph not found"}, status=404)

        # Переводчик может комментировать только назначенные ему истории
        if IsTranslatorGroup().has_permission(request, self) and p.story.assigned_to_id != user.id:
            return Response(status=403)

        serializer = ParagraphNoteSerializer(data=request.data)
        if serializer.is_valid():
            note = serializer.save(author=user)
            return Response(ParagraphNoteSerializer(note).data, status=201)
        return Response(serializer.errors, status=400)


class NoteUpdateView(APIView):
    def patch(self, request, note_id: int):
        note = ParagraphNote.objects.select_related("paragraph__story").get(pk=note_id)
        user = request.user
        is_owner = note.author_id == user.id
        # владелец-«переводчик» может править свои заметки только в своих историях
        if IsTranslatorGroup().has_permission(request, self):
            if not is_owner or note.paragraph.story.assigned_to_id != user.id:
                return Response(status=403)
        elif not IsAdminGroup().has_permission(request, self):
            return Response(status=403)

        if "text" in request.data:
            note.text = request.data["text"]
        if "resolved" in request.data:
            v = request.data["resolved"]
            note.resolved = str(v).lower() in ["true", "1", "yes", "on"]
        note.save()
        return Response(ParagraphNoteSerializer(note).data)


class IllustrationSelectView(APIView):
    def post(self, request, illustration_id: int):
        ill = Illustration.objects.select_related("paragraph__story").get(pk=illustration_id)
        user = request.user
        if not (IsAdminGroup().has_permission(request, self) or (IsTranslatorGroup().has_permission(request, self) and ill.paragraph.story.assigned_to_id == user.id)):
            return Response(status=403)
        ill.is_selected = bool(request.data.get("is_selected", True))
        ill.save(update_fields=["is_selected"])
        return Response({"ok": True, "is_selected": ill.is_selected})