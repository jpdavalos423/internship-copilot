import uuid

from django.db import migrations, models


def seed_recruiting_preferences(apps, schema_editor):
    RecruitingPreferences = apps.get_model("core", "RecruitingPreferences")
    if RecruitingPreferences.objects.exists():
        return

    RecruitingPreferences.objects.create(
        target_terms=["Fall 2026", "Winter 2027", "Spring 2027", "Summer 2027"],
        role_types=["Backend", "Full-stack", "Platform", "Infrastructure", "AI/ML"],
        preferred_locations=[],
        remote_preference="ANY",
        preferred_industries=[],
        excluded_keywords=[],
        minimum_match_score=60,
        include_sponsorship_required_roles=False,
        include_clearance_required_roles=False,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_job_recruiting_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="RecruitingPreferences",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                ("target_terms", models.JSONField(blank=True, default=list)),
                ("role_types", models.JSONField(blank=True, default=list)),
                ("preferred_locations", models.JSONField(blank=True, default=list)),
                (
                    "remote_preference",
                    models.CharField(
                        choices=[
                            ("REMOTE", "Remote"),
                            ("HYBRID", "Hybrid"),
                            ("ONSITE", "Onsite"),
                            ("ANY", "Any"),
                        ],
                        default="ANY",
                        max_length=16,
                    ),
                ),
                ("preferred_industries", models.JSONField(blank=True, default=list)),
                ("excluded_keywords", models.JSONField(blank=True, default=list)),
                ("minimum_match_score", models.PositiveIntegerField(default=60)),
                ("include_sponsorship_required_roles", models.BooleanField(default=False)),
                ("include_clearance_required_roles", models.BooleanField(default=False)),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.AddField(
            model_name="job",
            name="relevance",
            field=models.CharField(
                choices=[
                    ("HIGHLY_RELEVANT", "Highly Relevant"),
                    ("RELEVANT", "Relevant"),
                    ("REVIEW", "Review"),
                    ("NOT_RELEVANT", "Not Relevant"),
                ],
                default="REVIEW",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="job",
            name="relevance_flags",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="job",
            name="relevance_last_evaluated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="job",
            name="relevance_reasons",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(seed_recruiting_preferences, migrations.RunPython.noop),
    ]
