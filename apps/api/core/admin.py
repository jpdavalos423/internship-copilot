from django.contrib import admin

from core.models import CandidateProfile, Job, MatchReport


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "updated_at")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("company_name", "title", "workflow_status", "applied_date", "is_archived", "created_at")
    list_filter = ("workflow_status", "source_type", "is_archived")
    search_fields = ("company_name", "title", "next_action", "notes")


@admin.register(MatchReport)
class MatchReportAdmin(admin.ModelAdmin):
    list_display = ("job", "match_score", "recommendation", "created_at")
