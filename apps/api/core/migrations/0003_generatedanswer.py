from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_matchreport_matched_skills_by_category_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="GeneratedAnswer",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "answer_type",
                    models.CharField(
                        choices=[
                            ("WHY_COMPANY", "Why Company"),
                            ("WHY_ROLE", "Why Role"),
                            ("GOOD_FIT", "Good Fit"),
                            ("SELF_INTRODUCTION", "Self Introduction"),
                            (
                                "MOST_IMPRESSIVE_ACCOMPLISHMENT",
                                "Most Impressive Accomplishment",
                            ),
                        ],
                        max_length=64,
                    ),
                ),
                ("content", models.TextField()),
                ("evidence_summary", models.JSONField(blank=True, default=list)),
                ("generator_version", models.CharField(default="phase1-local-v1", max_length=64)),
                (
                    "candidate_profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="generated_answers",
                        to="core.candidateprofile",
                    ),
                ),
                (
                    "job",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="generated_answers",
                        to="core.job",
                    ),
                ),
                (
                    "match_report",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="generated_answers",
                        to="core.matchreport",
                    ),
                ),
            ],
            options={
                "ordering": ["answer_type", "-updated_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="generatedanswer",
            constraint=models.UniqueConstraint(
                fields=("job", "match_report", "answer_type"),
                name="unique_generated_answer_per_analysis_type",
            ),
        ),
    ]
