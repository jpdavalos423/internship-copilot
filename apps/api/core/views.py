from datetime import timedelta

from django.db.models import F, OuterRef, Subquery
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import CandidateProfile, GeneratedAnswer, Job, MatchReport, RecruitingPreferences
from core.serializers import (
    CandidateProfileSerializer,
    GeneratedAnswerListSerializer,
    GeneratedAnswerSerializer,
    GenerateAnswerRequestSerializer,
    JobCreateSerializer,
    JobDetailSerializer,
    JobIngestUrlSerializer,
    JobListSerializer,
    JobUpdateSerializer,
    MatchReportSerializer,
    RecruitingPreferencesSerializer,
)
from core.services.answer_generation import generate_answer_for_match_report
from core.services.answer_validation import AnswerValidationError
from core.services.job_ingestion import JobIngestionError, ingest_job_from_url
from core.services.job_parser import parse_job_text
from core.services.profile_parser import parse_profile_text
from core.services.relevance import (
    evaluate_job_relevance,
    get_or_create_preferences,
    refresh_all_job_relevance,
    refresh_job_relevance,
)
from core.services.scoring import score_job_fit


def error_response(message: str, *, code: str, status_code: int) -> Response:
    return Response({"error": {"code": code, "message": message}}, status=status_code)


def annotate_jobs_with_latest_match(job_queryset):
    latest_reports = MatchReport.objects.filter(job_id=OuterRef("pk")).order_by("-created_at")
    return job_queryset.annotate(
        latest_match_score=Subquery(latest_reports.values("match_score")[:1]),
        latest_recommendation=Subquery(latest_reports.values("recommendation")[:1]),
        latest_match_report_id=Subquery(latest_reports.values("id")[:1]),
        latest_analysis_created_at=Subquery(latest_reports.values("created_at")[:1]),
    )


def attach_relevance_scores(jobs, preferences):
    for job in jobs:
        evaluation = evaluate_job_relevance(
            job,
            preferences=preferences,
            latest_match_score=getattr(job, "latest_match_score", None),
        )
        job.relevance_score = evaluation.score
        if not job.relevance_reasons:
            job.relevance_reasons = evaluation.reasons
        if not job.relevance_flags:
            job.relevance_flags = evaluation.flags
    return jobs


def get_is_saved_for_workflow_status(workflow_status: str) -> bool:
    return workflow_status != Job.WorkflowStatus.DISCOVERED


def apply_job_filters(job_queryset, request):
    view_name = request.query_params.get("view", "all").lower()
    hide_not_relevant_param = request.query_params.get("hide_not_relevant")
    hide_not_relevant = (
        hide_not_relevant_param.lower() == "true"
        if hide_not_relevant_param is not None
        else view_name == "relevant"
    )
    if hide_not_relevant:
        job_queryset = job_queryset.exclude(relevance=Job.Relevance.NOT_RELEVANT)

    include_archived = request.query_params.get("include_archived", "false").lower() == "true"
    if not include_archived:
        job_queryset = job_queryset.filter(is_archived=False)

    relevance_filter = request.query_params.get("relevance")
    if relevance_filter:
        relevances = [item.strip().upper() for item in relevance_filter.split(",") if item.strip()]
        valid_relevances = {choice for choice, _label in Job.Relevance.choices}
        selected_relevances = [item for item in relevances if item in valid_relevances]
        if selected_relevances:
            job_queryset = job_queryset.filter(relevance__in=selected_relevances)
    elif view_name == "relevant":
        job_queryset = job_queryset.filter(
            relevance__in=[Job.Relevance.HIGHLY_RELEVANT, Job.Relevance.RELEVANT]
        )

    status_filter = request.query_params.get("status")
    if status_filter:
        statuses = [item.strip().upper() for item in status_filter.split(",") if item.strip()]
        valid_statuses = {choice for choice, _label in Job.WorkflowStatus.choices}
        selected_statuses = [item for item in statuses if item in valid_statuses]
        if selected_statuses:
            job_queryset = job_queryset.filter(workflow_status__in=selected_statuses)

    recently_added = request.query_params.get("recently_added", "false").lower() == "true"
    if recently_added:
        cutoff = timezone.now() - timedelta(days=7)
        job_queryset = job_queryset.filter(created_at__gte=cutoff)

    return job_queryset


def apply_job_sorting(job_queryset, request):
    sort = request.query_params.get("sort", "match_score_desc")
    sort_mapping = {
        "match_score_desc": (F("latest_match_score").desc(nulls_last=True), F("updated_at").desc()),
        "match_score_asc": (F("latest_match_score").asc(nulls_last=True), F("updated_at").desc()),
        "newest_first": ("-created_at",),
        "updated_at_desc": ("-updated_at",),
        "created_at_desc": ("-created_at",),
        "company_asc": ("company_name", "-updated_at"),
    }
    return job_queryset.order_by(*sort_mapping.get(sort, sort_mapping["match_score_desc"]))


class CandidateProfileView(APIView):
    def get(self, request):
        profile = CandidateProfile.objects.order_by("-updated_at").first()
        if profile is None:
            return error_response(
                "Candidate profile not found",
                code="CANDIDATE_PROFILE_NOT_FOUND",
                status_code=404,
            )
        return Response(CandidateProfileSerializer(profile).data)

    def post(self, request):
        profile = CandidateProfile.objects.order_by("-updated_at").first()
        serializer = CandidateProfileSerializer(instance=profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        normalized_skills = parse_profile_text(serializer.validated_data["resume_text"])
        profile = serializer.save(normalized_skills=normalized_skills)
        return Response(CandidateProfileSerializer(profile).data, status=status.HTTP_200_OK)


class RecruitingPreferencesView(APIView):
    def get(self, request):
        preferences = get_or_create_preferences()
        return Response(RecruitingPreferencesSerializer(preferences).data)

    def post(self, request):
        preferences = RecruitingPreferences.objects.order_by("-updated_at").first()
        serializer = RecruitingPreferencesSerializer(instance=preferences, data=request.data)
        serializer.is_valid(raise_exception=True)
        preferences = serializer.save()
        refresh_all_job_relevance(preferences=preferences)
        return Response(RecruitingPreferencesSerializer(preferences).data, status=status.HTTP_200_OK)


class JobListCreateView(APIView):
    def get(self, request):
        preferences = get_or_create_preferences()
        jobs = annotate_jobs_with_latest_match(Job.objects.all())
        jobs = apply_job_filters(jobs, request)
        jobs = apply_job_sorting(jobs, request)
        job_list = attach_relevance_scores(list(jobs), preferences)
        return Response(JobListSerializer(job_list, many=True).data)

    def post(self, request):
        serializer = JobCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        parsed = parse_job_text(serializer.validated_data["raw_text"])
        job = serializer.save(
            workflow_status=Job.WorkflowStatus.SAVED,
            is_saved=True,
            normalized_requirements=parsed["requirements"],
            normalized_preferred=parsed["preferred"],
        )
        refresh_job_relevance(job)
        job = annotate_jobs_with_latest_match(Job.objects.filter(id=job.id)).get()
        preferences = get_or_create_preferences()
        attach_relevance_scores([job], preferences)
        return Response(JobDetailSerializer(job).data, status=status.HTTP_201_CREATED)


class JobDetailView(APIView):
    def get(self, request, job_id):
        job = annotate_jobs_with_latest_match(Job.objects.filter(id=job_id)).first()
        if job is None:
            return error_response("Job not found", code="JOB_NOT_FOUND", status_code=404)
        preferences = get_or_create_preferences()
        attach_relevance_scores([job], preferences)
        return Response(JobDetailSerializer(job).data)

    def patch(self, request, job_id):
        job = Job.objects.filter(id=job_id).first()
        if job is None:
            return error_response("Job not found", code="JOB_NOT_FOUND", status_code=404)

        serializer = JobUpdateSerializer(instance=job, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data.copy()
        workflow_status = validated_data.get("workflow_status", job.workflow_status)

        if (
            workflow_status == Job.WorkflowStatus.APPLIED
            and "applied_date" not in validated_data
            and job.applied_date is None
        ):
            validated_data["applied_date"] = timezone.localdate()

        validated_data["is_saved"] = get_is_saved_for_workflow_status(workflow_status)
        serializer.save(**validated_data)
        refreshed_job = annotate_jobs_with_latest_match(Job.objects.filter(id=job_id)).get()
        preferences = get_or_create_preferences()
        attach_relevance_scores([refreshed_job], preferences)
        return Response(JobDetailSerializer(refreshed_job).data)


class JobIngestUrlView(APIView):
    def post(self, request):
        serializer = JobIngestUrlSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                "Enter a valid http or https job posting URL.",
                code="INVALID_URL",
                status_code=400,
            )

        try:
            result = ingest_job_from_url(serializer.validated_data["url"])
        except JobIngestionError as exc:
            return error_response(exc.message, code=exc.code, status_code=exc.status_code)

        status_code = status.HTTP_201_CREATED if result.created else status.HTTP_200_OK
        if result.created:
            result.job.workflow_status = Job.WorkflowStatus.DISCOVERED
            result.job.is_saved = False
            result.job.save(update_fields=["workflow_status", "is_saved", "updated_at"])
        refresh_job_relevance(result.job)
        job = annotate_jobs_with_latest_match(Job.objects.filter(id=result.job.id)).get()
        preferences = get_or_create_preferences()
        attach_relevance_scores([job], preferences)
        return Response(JobDetailSerializer(job).data, status=status_code)


class JobAnalyzeView(APIView):
    def post(self, request, job_id):
        profile = CandidateProfile.objects.order_by("-updated_at").first()
        if profile is None:
            return error_response(
                "Candidate profile is required before analysis",
                code="CANDIDATE_PROFILE_REQUIRED",
                status_code=400,
            )

        job = Job.objects.filter(id=job_id).first()
        if job is None:
            return error_response("Job not found", code="JOB_NOT_FOUND", status_code=404)

        result = score_job_fit(profile=profile, job=job)
        report = MatchReport.objects.create(
            job=job,
            candidate_profile=profile,
            match_score=result["match_score"],
            recommendation=result["recommendation"],
            strengths=result["strengths"],
            gaps=result["gaps"],
            missing_keywords=result["missing_keywords"],
            matched_skills_by_category=result["matched_skills_by_category"],
            missing_skills_by_category=result["missing_skills_by_category"],
            reasoning=result["reasoning"],
            score_breakdown=result["score_breakdown"],
        )
        refresh_job_relevance(job, latest_match_score=report.match_score)
        return Response(MatchReportSerializer(report).data, status=status.HTTP_201_CREATED)


class JobAnalysisView(APIView):
    def get(self, request, job_id):
        job = Job.objects.filter(id=job_id).first()
        if job is None:
            return error_response("Job not found", code="JOB_NOT_FOUND", status_code=404)

        report = job.match_reports.order_by("-created_at").first()
        if report is None:
            return error_response(
                "Match report not found",
                code="MATCH_REPORT_NOT_FOUND",
                status_code=404,
            )
        return Response(MatchReportSerializer(report).data)


class JobAnalysisDetailView(APIView):
    def get(self, request, job_id, match_report_id):
        job = Job.objects.filter(id=job_id).first()
        if job is None:
            return error_response("Job not found", code="JOB_NOT_FOUND", status_code=404)

        report = job.match_reports.filter(id=match_report_id).first()
        if report is None:
            return error_response(
                "Match report not found",
                code="MATCH_REPORT_NOT_FOUND",
                status_code=404,
            )
        return Response(MatchReportSerializer(report).data)


def get_job_or_error(job_id):
    job = Job.objects.filter(id=job_id).first()
    if job is None:
        return None, error_response("Job not found", code="JOB_NOT_FOUND", status_code=404)
    return job, None


def get_match_report_for_job_or_error(*, job, match_report_id):
    report = job.match_reports.filter(id=match_report_id).first()
    if report is None:
        return None, error_response(
            "Match report not found",
            code="MATCH_REPORT_NOT_FOUND",
            status_code=404,
        )
    return report, None


class JobAnswerGenerateView(APIView):
    def post(self, request, job_id):
        job, job_error = get_job_or_error(job_id)
        if job_error is not None:
            return job_error

        serializer = GenerateAnswerRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        match_report, report_error = get_match_report_for_job_or_error(
            job=job,
            match_report_id=serializer.validated_data["match_report_id"],
        )
        if report_error is not None:
            return report_error

        if match_report.candidate_profile_id is None:
            return error_response(
                "Candidate profile is required before generating answers",
                code="CANDIDATE_PROFILE_REQUIRED",
                status_code=400,
            )

        try:
            result = generate_answer_for_match_report(
                job=job,
                match_report=match_report,
                answer_type=serializer.validated_data["answer_type"],
            )
        except AnswerValidationError as exc:
            return error_response(
                str(exc),
                code="ANSWER_GENERATION_FAILED",
                status_code=500,
            )

        status_code = status.HTTP_201_CREATED if result.created else status.HTTP_200_OK
        return Response(GeneratedAnswerSerializer(result.answer).data, status=status_code)


class JobAnswersListView(APIView):
    def get(self, request, job_id):
        job, job_error = get_job_or_error(job_id)
        if job_error is not None:
            return job_error

        match_report_id = request.query_params.get("match_report_id")
        if match_report_id:
            match_report, report_error = get_match_report_for_job_or_error(
                job=job,
                match_report_id=match_report_id,
            )
            if report_error is not None:
                return report_error
        else:
            match_report = job.match_reports.order_by("-created_at").first()
            if match_report is None:
                return error_response(
                    "Match report not found",
                    code="MATCH_REPORT_NOT_FOUND",
                    status_code=404,
                )

        answers = GeneratedAnswer.objects.filter(
            job=job,
            match_report=match_report,
        ).order_by("answer_type")
        payload = {
            "job_id": job.id,
            "candidate_profile_id": match_report.candidate_profile_id,
            "match_report_id": match_report.id,
            "answers": answers,
        }
        return Response(GeneratedAnswerListSerializer(payload).data)
