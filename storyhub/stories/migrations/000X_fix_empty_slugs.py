from django.db import migrations
from django.utils.text import slugify

def fill_slugs(apps, schema_editor):
    Story = apps.get_model("stories", "Story")
    for s in Story.objects.filter(slug__in=["", None, "-", "-1", "-2"]):
        base = slugify(s.title or "", allow_unicode=True)[:240] or f"story-{s.pk}"
        slug = base
        n = 1
        exists = Story.objects.exclude(pk=s.pk).filter(slug=slug).exists()
        while exists:
            slug = f"{base}-{n}"
            n += 1
            exists = Story.objects.exclude(pk=s.pk).filter(slug=slug).exists()
        s.slug = slug
        s.save(update_fields=["slug"])

class Migration(migrations.Migration):
    dependencies = [("stories", "0001_initial")]
    operations = [migrations.RunPython(fill_slugs, migrations.RunPython.noop)]