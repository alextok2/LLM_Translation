# translations/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Count
from .models import Translation, TranslatorAssignment, AssignmentStatus
from stories.models import Story, StoryStatus

def recompute_translated_count(story: Story):
    if not story.assigned_to_id:
        story.translated_count = 0
        story.save(update_fields=["translated_count"])
        return
    finalized = Translation.objects.filter(
        paragraph__story=story,
        translator_id=story.assigned_to_id,
        is_finalized=True
    ).values("paragraph_id").distinct().count()
    if story.translated_count != finalized:
        story.translated_count = finalized
        story.save(update_fields=["translated_count"])

@receiver(post_save, sender=Translation)
def on_translation_saved(sender, instance: Translation, **kwargs):
    recompute_translated_count(instance.paragraph.story)

@receiver(post_delete, sender=Translation)
def on_translation_deleted(sender, instance: Translation, **kwargs):
    recompute_translated_count(instance.paragraph.story)

@receiver(post_save, sender=TranslatorAssignment)
def on_assignment_saved(sender, instance: TranslatorAssignment, created, **kwargs):
    story = instance.story
    if instance.status == AssignmentStatus.ACTIVE:
        # назначаем переводчика и ставим статус IN_TRANSLATION
        if not story.assigned_to_id or story.assigned_to_id != instance.translator_id:
            story.assigned_to_id = instance.translator_id
            story.status = StoryStatus.IN_TRANSLATION
            story.save(update_fields=["assigned_to", "status"])
        recompute_translated_count(story)