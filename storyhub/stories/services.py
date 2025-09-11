# stories/services.py
from typing import List
from django.db import transaction
from .models import Story, Paragraph, Illustration
from django.utils.text import slugify

PLACEHOLDER_URL = "https://picsum.photos/seed/{seed}/400/300"

def _split_paragraphs(text: str) -> List[str]:
    if not text:
        return []
    parts = [p.strip() for p in text.strip().split("\n\n")]
    return [p for p in parts if p != ""]

@transaction.atomic
def parse_story_paragraphs(story: Story, original_text: str, machine_text: str):
    # Простой режим без глав (совместим с текущей БД даже если нет таблицы Chapter)
    Paragraph.objects.filter(story=story).delete()

    orig = _split_paragraphs(original_text)
    mach = _split_paragraphs(machine_text)

    n = max(len(orig), len(mach))
    created = 0
    for i in range(n):
        o = orig[i] if i < len(orig) else ""
        m = mach[i] if i < len(mach) else ""
        p = Paragraph.objects.create(story=story, index=i+1, original_text=o, machine_text=m)
        for pos in range(1, 6):
            Illustration.objects.create(
                paragraph=p,
                position=pos,
                image_url=PLACEHOLDER_URL.format(seed=f"{story.id}-{i+1}-{pos}")
            )
        created += 1

    story.paragraphs_count = created
    story.translated_count = 0
    story.save(update_fields=["paragraphs_count", "translated_count"])
    return created

@transaction.atomic
def parse_story_with_chapters(story: Story, chapters_payload: List[dict]):
    # Импортируем Chapter лениво, чтобы отсутствие модели/таблицы не ломало parse_story_paragraphs
    from .models import Chapter

    Paragraph.objects.filter(story=story).delete()
    Chapter.objects.filter(story=story).delete()

    global_index = 0
    created = 0
    for ch_idx, ch in enumerate(chapters_payload, start=1):
        chapter = Chapter.objects.create(
            story=story, index=ch_idx, title=(ch.get("title") or "").strip()
        )
        orig = _split_paragraphs(ch.get("original_text") or "")
        mach = _split_paragraphs(ch.get("machine_text") or "")
        n = max(len(orig), len(mach))
        for i in range(n):
            global_index += 1
            o = orig[i] if i < len(orig) else ""
            m = mach[i] if i < len(mach) else ""
            p = Paragraph.objects.create(
                story=story,
                chapter=chapter,
                index=global_index,
                original_text=o,
                machine_text=m,
            )
            for pos in range(1, 6):
                Illustration.objects.create(
                    paragraph=p,
                    position=pos,
                    image_url=PLACEHOLDER_URL.format(seed=f"{story.id}-{global_index}-{pos}")
                )
            created += 1

    story.paragraphs_count = created
    story.translated_count = 0
    story.save(update_fields=["paragraphs_count", "translated_count"])
    return created