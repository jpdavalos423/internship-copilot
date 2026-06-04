from django.db import migrations, models


DEFAULT_POSITION_TYPES = ["INTERN"]


def infer_position_type(title: str, location: str, raw_text: str, source_url: str | None) -> str:
    search_text = " ".join([title or "", location or "", raw_text or "", source_url or ""]).lower()

    if "part-time" in search_text or "part time" in search_text:
        return "PART_TIME"
    if (
        "intern" in search_text
        or "internship" in search_text
        or "co-op" in search_text
        or "coop" in search_text
    ):
        return "INTERN"
    if (
        "full-time" in search_text
        or "full time" in search_text
        or "new grad" in search_text
        or "graduate" in search_text
    ):
        return "FULL_TIME"
    return "UNKNOWN"


def backfill_position_types(apps, schema_editor):
    RecruitingPreferences = apps.get_model("core", "RecruitingPreferences")
    Job = apps.get_model("core", "Job")

    for preferences in RecruitingPreferences.objects.all():
        preferences.position_types = preferences.position_types or DEFAULT_POSITION_TYPES
        preferences.save(update_fields=["position_types", "updated_at"])

    for job in Job.objects.all():
        job.position_type = infer_position_type(
            job.title,
            job.location,
            job.raw_text,
            job.source_url,
        )
        job.save(update_fields=["position_type", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_jobsource"),
    ]

    operations = [
        migrations.AddField(
            model_name="job",
            name="position_type",
            field=models.CharField(
                choices=[
                    ("INTERN", "Intern"),
                    ("FULL_TIME", "Full-time"),
                    ("PART_TIME", "Part-time"),
                    ("UNKNOWN", "Unknown"),
                ],
                default="UNKNOWN",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="recruitingpreferences",
            name="position_types",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(backfill_position_types, migrations.RunPython.noop),
    ]
