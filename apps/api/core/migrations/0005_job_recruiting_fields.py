from django.db import migrations, models


def backfill_job_recruiting_fields(apps, schema_editor):
    Job = apps.get_model("core", "Job")

    for job in Job.objects.all():
        if job.is_saved:
            workflow_status = "SAVED"
        elif job.ingestion_status == "MANUAL":
            workflow_status = "SAVED"
        else:
            workflow_status = "DISCOVERED"

        job.workflow_status = workflow_status
        job.is_saved = workflow_status != "DISCOVERED"
        job.save(update_fields=["workflow_status", "is_saved", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_job_content_hash_job_external_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="job",
            name="applied_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="job",
            name="next_action",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="job",
            name="next_action_due_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="job",
            name="notes",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="job",
            name="workflow_status",
            field=models.CharField(
                choices=[
                    ("DISCOVERED", "Discovered"),
                    ("SAVED", "Saved"),
                    ("APPLIED", "Applied"),
                    ("OA", "OA"),
                    ("INTERVIEW", "Interview"),
                    ("FINAL_ROUND", "Final Round"),
                    ("OFFER", "Offer"),
                    ("REJECTED", "Rejected"),
                    ("WITHDRAWN", "Withdrawn"),
                ],
                default="DISCOVERED",
                max_length=32,
            ),
        ),
        migrations.RunPython(backfill_job_recruiting_fields, migrations.RunPython.noop),
    ]
