from django.contrib import admin

from core.models import CandidateProfile, Job, JobSource, MatchReport, RecruitingPreferences


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "updated_at")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "title",
        "workflow_status",
        "relevance",
        "applied_date",
        "is_archived",
        "created_at",
    )
    list_filter = ("workflow_status", "relevance", "source_type", "is_archived")
    search_fields = ("company_name", "title", "next_action", "notes")


@admin.register(JobSource)
class JobSourceAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "name",
        "source_type",
        "is_active",
        "scan_interval_hours",
        "last_scanned_at",
        "last_success_at",
    )
    list_filter = ("source_type", "is_active")
    search_fields = ("company_name", "name", "base_url")


@admin.register(MatchReport)
class MatchReportAdmin(admin.ModelAdmin):
    list_display = ("job", "match_score", "recommendation", "created_at")


@admin.register(RecruitingPreferences)
class RecruitingPreferencesAdmin(admin.ModelAdmin):
    list_display = ("id", "remote_preference", "minimum_match_score", "updated_at")
