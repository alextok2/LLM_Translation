# stories/models.py
from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator, URLValidator
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

validate_http_https = URLValidator(schemes=["http", "https"])

class Chapter(models.Model):
    story = models.ForeignKey("stories.Story", related_name="chapters", on_delete=models.CASCADE)
    index = models.PositiveIntegerField()  # порядковый номер главы внутри истории (1..N)
    title = models.CharField(max_length=255, blank=True, default="")  # название главы

    class Meta:
        unique_together = [("story", "index")]
        ordering = ["index"]

    def __str__(self):
        return f"{self.story.title} / Глава {self.index}: {self.title or 'Без названия'}"




class Language(models.Model):
    code = models.CharField(max_length=8, unique=True)  # ISO 639-1 по умолчанию
    name = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Tag(models.Model):
    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=72, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:72]
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class StoryStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    IN_TRANSLATION = "IN_TRANSLATION", "In translation"
    REVIEW = "REVIEW", "Review"
    PUBLISHED = "PUBLISHED", "Published"


class Story(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=260, unique=True)
    original_language = models.ForeignKey(Language, related_name="stories_original", on_delete=models.PROTECT)
    target_language = models.ForeignKey(Language, related_name="stories_target", on_delete=models.PROTECT)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=StoryStatus.choices, default=StoryStatus.DRAFT)
    tags = models.ManyToManyField(Tag, related_name="stories", blank=True)
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_stories")
    paragraphs_count = models.PositiveIntegerField(default=0)
    translated_count = models.PositiveIntegerField(default=0)
    published_at = models.DateTimeField(null=True, blank=True)
    poster_url = models.URLField(blank=True, default="")


    class Meta:
        ordering = ["-id"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title, allow_unicode=True)[:240] or "story"
            slug = base
            n = 1
            while Story.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)


    @property
    def is_published(self):
        return self.status == StoryStatus.PUBLISHED

    def __str__(self):
        return self.title




class Paragraph(models.Model):
    story = models.ForeignKey(Story, related_name="paragraphs", on_delete=models.CASCADE)
    index = models.PositiveIntegerField()
    original_text = models.TextField()
    machine_text = models.TextField(blank=True)
    chapter = models.ForeignKey(Chapter, related_name="paragraphs", on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = [("story", "index")]
        ordering = ["index"]

    def __str__(self):
        return f"{self.story.title} #{self.index}"


class Illustration(models.Model):
    paragraph = models.ForeignKey(Paragraph, related_name="illustrations", on_delete=models.CASCADE)
    image_url = models.URLField(validators=[validate_http_https])
    position = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    is_selected = models.BooleanField(default=False)

    class Meta:
        unique_together = [("paragraph", "position")]
        ordering = ["position"]

    def __str__(self):
        return f"Illu p{self.paragraph_id} pos{self.position}"