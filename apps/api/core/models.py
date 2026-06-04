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
    class SourceType(models.TextChoices):
        MANUAL = "MANUAL", "Manual"
        GREENHOUSE = "GREENHOUSE", "Greenhouse"
        LEVER = "LEVER", "Lever"
        ASHBY = "ASHBY", "Ashby"
        OTHER = "OTHER", "Other"

    class IngestionStatus(models.TextChoices):
        MANUAL = "MANUAL", "Manual"
        INGESTED = "INGESTED", "Ingested"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    raw_text = models.TextField()
    source_type = models.CharField(
        max_length=32,
        choices=SourceType.choices,
        default=SourceType.MANUAL,
    )
    source_url = models.URLField(blank=True, null=True)
    external_id = models.CharField(max_length=255, blank=True, null=True)
    content_hash = models.CharField(max_length=255, blank=True, null=True)
    last_seen_at = models.DateTimeField(blank=True, null=True)
    ingestion_status = models.CharField(
        max_length=32,
        choices=IngestionStatus.choices,
        default=IngestionStatus.MANUAL,
    )
    is_archived = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    is_saved = models.BooleanField(default=False)
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


class GeneratedAnswer(TimestampedModel):
    class AnswerType(models.TextChoices):
        WHY_COMPANY = "WHY_COMPANY", "Why Company"
        WHY_ROLE = "WHY_ROLE", "Why Role"
        GOOD_FIT = "GOOD_FIT", "Good Fit"
        SELF_INTRODUCTION = "SELF_INTRODUCTION", "Self Introduction"
        MOST_IMPRESSIVE_ACCOMPLISHMENT = (
            "MOST_IMPRESSIVE_ACCOMPLISHMENT",
            "Most Impressive Accomplishment",
        )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="generated_answers")
    candidate_profile = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="generated_answers",
    )
    match_report = models.ForeignKey(
        MatchReport,
        on_delete=models.CASCADE,
        related_name="generated_answers",
    )
    answer_type = models.CharField(max_length=64, choices=AnswerType.choices)
    content = models.TextField()
    evidence_summary = models.JSONField(default=list, blank=True)
    generator_version = models.CharField(max_length=64, default="phase1-local-v1")

    class Meta:
        ordering = ["answer_type", "-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["job", "match_report", "answer_type"],
                name="unique_generated_answer_per_analysis_type",
            )
        ]
