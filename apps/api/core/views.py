from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import CandidateProfile, Job, MatchReport
from core.serializers import (
    CandidateProfileSerializer,
    JobCreateSerializer,
    JobDetailSerializer,
    JobListSerializer,
    MatchReportSerializer,
)
from core.services.job_parser import parse_job_text
from core.services.profile_parser import parse_profile_text
from core.services.scoring import score_job_fit


class CandidateProfileView(APIView):
    def get(self, request):
        profile = CandidateProfile.objects.order_by("-updated_at").first()
        if profile is None:
            return Response({"error": {"message": "Candidate profile not found"}}, status=404)
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
            return Response({"error": {"message": "Job not found"}}, status=404)
        return Response(JobDetailSerializer(job).data)


class JobAnalyzeView(APIView):
    def post(self, request, job_id):
        profile = CandidateProfile.objects.order_by("-updated_at").first()
        if profile is None:
            return Response(
                {"error": {"message": "Candidate profile is required before analysis"}},
                status=400,
            )

        job = Job.objects.filter(id=job_id).first()
        if job is None:
            return Response({"error": {"message": "Job not found"}}, status=404)

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
            return Response({"error": {"message": "Job not found"}}, status=404)

        report = job.match_reports.order_by("-created_at").first()
        if report is None:
            return Response({"error": {"message": "Match report not found"}}, status=404)
        return Response(MatchReportSerializer(report).data)
