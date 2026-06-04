from django.urls import path

from core.views import (
    CandidateProfileView,
    JobAnalysisView,
    JobAnalyzeView,
    JobDetailView,
    JobListCreateView,
)

urlpatterns = [
    path("profile", CandidateProfileView.as_view(), name="candidate-profile"),
    path("jobs", JobListCreateView.as_view(), name="job-list-create"),
    path("jobs/<uuid:job_id>", JobDetailView.as_view(), name="job-detail"),
    path("jobs/<uuid:job_id>/analyze", JobAnalyzeView.as_view(), name="job-analyze"),
    path("jobs/<uuid:job_id>/analysis", JobAnalysisView.as_view(), name="job-analysis"),
]
