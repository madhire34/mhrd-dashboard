from django.db import models
from django.utils.text import slugify

class State(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Scheme(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=150, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Initiative(models.Model):
    name = models.CharField(max_length=255)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='initiatives')
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='initiatives')
    category = models.CharField(max_length=100)
    year = models.IntegerField()
    status = models.CharField(max_length=50)
    progress = models.FloatField(help_text='0.0 to 1.0')
    schools_impacted = models.IntegerField()
    students_impacted = models.IntegerField()
    scholarships_awarded = models.IntegerField()
    budget_utilized = models.FloatField(help_text='Crores')

    class Meta:
        indexes = [
            models.Index(fields=["year"]),
            models.Index(fields=["category"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.year})"


class Report(models.Model):
    report_id = models.SlugField(max_length=64, unique=True)
    status = models.CharField(max_length=32, default='queued')
    params = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["status"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return self.report_id
