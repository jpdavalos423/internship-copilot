from django.core.management.base import BaseCommand

from core.services.job_discovery import scan_all_sources


class Command(BaseCommand):
    help = "Scan active job sources that are due for discovery."

    def handle(self, *args, **options):
        result = scan_all_sources(due_only=True)
        summary = result.summary
        self.stdout.write(
            self.style.SUCCESS(
                "Scanned active due sources: "
                f"discovered={summary.discovered_count}, "
                f"created={summary.created_count}, "
                f"duplicates={summary.duplicate_count}, "
                f"failed={summary.failed_count}, "
                f"skipped={summary.skipped_count}"
            )
        )
