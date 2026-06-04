from django.urls import path

from core.views import (
    CandidateProfileView,
    JobAnswersListView,
    JobAnswerGenerateView,
    JobAnalysisView,
    JobAnalysisDetailView,
    JobAnalyzeView,
    JobDetailView,
    JobIngestUrlView,
    JobListCreateView,
    RecruitingPreferencesView,
)

urlpatterns = [
    path("profile", CandidateProfileView.as_view(), name="candidate-profile"),
    path(
        "preferences/recruiting",
        RecruitingPreferencesView.as_view(),
        name="recruiting-preferences",
    ),
    path("jobs", JobListCreateView.as_view(), name="job-list-create"),
    path("jobs/ingest-url", JobIngestUrlView.as_view(), name="job-ingest-url"),
    path("jobs/<uuid:job_id>", JobDetailView.as_view(), name="job-detail"),
    path("jobs/<uuid:job_id>/analyze", JobAnalyzeView.as_view(), name="job-analyze"),
    path("jobs/<uuid:job_id>/analysis", JobAnalysisView.as_view(), name="job-analysis"),
    path("jobs/<uuid:job_id>/answers", JobAnswersListView.as_view(), name="job-answers"),
    path(
        "jobs/<uuid:job_id>/answers/generate",
        JobAnswerGenerateView.as_view(),
        name="job-answer-generate",
    ),
    path(
        "jobs/<uuid:job_id>/analysis/<uuid:match_report_id>",
        JobAnalysisDetailView.as_view(),
        name="job-analysis-detail",
    ),
]
