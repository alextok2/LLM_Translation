from django.db import migrations

def create_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    reader, _ = Group.objects.get_or_create(name="reader")
    translator, _ = Group.objects.get_or_create(name="translator")
    admin, _ = Group.objects.get_or_create(name="admin")

    # Базовые права по моделям (для админа — всё)
    for perm in Permission.objects.all():
        admin.permissions.add(perm)

    # Транслятор: может смотреть stories/paragraphs, работать с translations, notes
    stories_ct = ContentType.objects.get_by_natural_key("stories", "story")
    paragraph_ct = ContentType.objects.get_by_natural_key("stories", "paragraph")
    translation_ct = ContentType.objects.get_by_natural_key("translations", "translation")
    note_ct = ContentType.objects.get_by_natural_key("translations", "paragraphnote")
    ill_ct = ContentType.objects.get_by_natural_key("stories", "illustration")

    def grant(model_ct, codenames):
        for codename in codenames:
            try:
                p = Permission.objects.get(content_type=model_ct, codename=codename)
                translator.permissions.add(p)
            except Permission.DoesNotExist:
                pass

    grant(stories_ct, ["view_story"])
    grant(paragraph_ct, ["view_paragraph"])
    grant(translation_ct, ["add_translation", "change_translation", "view_translation"])
    grant(note_ct, ["add_paragraphnote", "change_paragraphnote", "view_paragraphnote"])
    grant(ill_ct, ["change_illustration", "view_illustration"])

    # Ридер: только просмотр Story (опубликованных мы ограничим в представлениях)
    try:
        p = Permission.objects.get(content_type=stories_ct, codename="view_story")
        reader.permissions.add(p)
    except Permission.DoesNotExist:
        pass

def drop_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=["reader", "translator", "admin"]).delete()

class Migration(migrations.Migration):
    dependencies = [("users", "0001_initial"), ("stories", "0001_initial"), ("translations", "0001_initial"), ("auth", "0012_alter_user_first_name_max_length")]
    operations = [migrations.RunPython(create_groups, reverse_code=drop_groups)]