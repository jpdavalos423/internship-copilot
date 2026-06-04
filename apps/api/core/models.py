import uuid

from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CandidateProfile(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume_text = models.TextField()
    normalized_skills = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-updated_at"]


class Job(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    raw_text = models.TextField()
    normalized_requirements = models.JSONField(default=list, blank=True)
    normalized_preferred = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-created_at"]


class MatchReport(TimestampedModel):
    class Recommendation(models.TextChoices):
        HIGH_PRIORITY_APPLY = "HIGH_PRIORITY_APPLY", "High Priority Apply"
        APPLY = "APPLY", "Apply"
        REVIEW = "REVIEW", "Review"
        LOW_PRIORITY = "LOW_PRIORITY", "Low Priority"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="match_reports")
    candidate_profile = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="match_reports",
    )
    match_score = models.PositiveIntegerField()
    recommendation = models.CharField(max_length=32, choices=Recommendation.choices)
    strengths = models.JSONField(default=list, blank=True)
    gaps = models.JSONField(default=list, blank=True)
    missing_keywords = models.JSONField(default=list, blank=True)
    matched_skills_by_category = models.JSONField(default=dict, blank=True)
    missing_skills_by_category = models.JSONField(default=dict, blank=True)
    reasoning = models.TextField(blank=True, default="")
    score_breakdown = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
