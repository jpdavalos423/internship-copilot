from django.contrib import admin

from core.models import CandidateProfile, Job, MatchReport, RecruitingPreferences


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


@admin.register(MatchReport)
class MatchReportAdmin(admin.ModelAdmin):
    list_display = ("job", "match_score", "recommendation", "created_at")


@admin.register(RecruitingPreferences)
class RecruitingPreferencesAdmin(admin.ModelAdmin):
    list_display = ("id", "remote_preference", "minimum_match_score", "updated_at")
