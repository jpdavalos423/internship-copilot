from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import CandidateProfile, GeneratedAnswer, Job, MatchReport
from core.serializers import (
    CandidateProfileSerializer,
    GeneratedAnswerListSerializer,
    GeneratedAnswerSerializer,
    GenerateAnswerRequestSerializer,
    JobCreateSerializer,
    JobDetailSerializer,
    JobIngestUrlSerializer,
    JobListSerializer,
    MatchReportSerializer,
)
from core.services.answer_generation import generate_answer_for_match_report
from core.services.answer_validation import AnswerValidationError
from core.services.job_ingestion import JobIngestionError, ingest_job_from_url
from core.services.job_parser import parse_job_text
from core.services.profile_parser import parse_profile_text
from core.services.scoring import score_job_fit


def error_response(message: str, *, code: str, status_code: int) -> Response:
    return Response({"error": {"code": code, "message": message}}, status=status_code)


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


class JobListCreateView(APIView):
    def get(self, request):
        jobs = Job.objects.all()
        return Response(JobListSerializer(jobs, many=True).data)

    def post(self, request):
        serializer = JobCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        parsed = parse_job_text(serializer.validated_data["raw_text"])
        job = serializer.save(
            normalized_requirements=parsed["requirements"],
            normalized_preferred=parsed["preferred"],
        )
        return Response(JobDetailSerializer(job).data, status=status.HTTP_201_CREATED)


class JobDetailView(APIView):
    def get(self, request, job_id):
        job = Job.objects.filter(id=job_id).first()
        if job is None:
            return error_response("Job not found", code="JOB_NOT_FOUND", status_code=404)
        return Response(JobDetailSerializer(job).data)


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
        return Response(JobDetailSerializer(result.job).data, status=status_code)


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
