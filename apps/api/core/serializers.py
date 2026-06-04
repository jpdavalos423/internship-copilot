from rest_framework import serializers

from core.models import CandidateProfile, GeneratedAnswer, Job, MatchReport


class CandidateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateProfile
        fields = ["id", "resume_text", "normalized_skills", "created_at", "updated_at"]
        read_only_fields = ["id", "normalized_skills", "created_at", "updated_at"]


class JobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            "id",
            "company_name",
            "title",
            "location",
            "raw_text",
            "normalized_requirements",
            "normalized_preferred",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "normalized_requirements",
            "normalized_preferred",
            "created_at",
            "updated_at",
        ]


class JobListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            "id",
            "company_name",
            "title",
            "location",
            "normalized_requirements",
            "normalized_preferred",
            "created_at",
            "updated_at",
        ]


class JobDetailSerializer(JobListSerializer):
    class Meta(JobListSerializer.Meta):
        fields = JobListSerializer.Meta.fields + ["raw_text"]


class MatchReportSerializer(serializers.ModelSerializer):
    match_report_id = serializers.UUIDField(source="id", read_only=True)
    job_id = serializers.UUIDField(source="job.id", read_only=True)
    candidate_profile_id = serializers.UUIDField(source="candidate_profile.id", read_only=True)

    class Meta:
        model = MatchReport
        fields = [
            "id",
            "match_report_id",
            "job_id",
            "candidate_profile_id",
            "match_score",
            "recommendation",
            "strengths",
            "gaps",
            "missing_keywords",
            "matched_skills_by_category",
            "missing_skills_by_category",
            "reasoning",
            "score_breakdown",
            "created_at",
            "updated_at",
        ]


class GenerateAnswerRequestSerializer(serializers.Serializer):
    answer_type = serializers.ChoiceField(choices=GeneratedAnswer.AnswerType.choices)
    match_report_id = serializers.UUIDField()


class GeneratedAnswerSerializer(serializers.ModelSerializer):
    job_id = serializers.UUIDField(source="job.id", read_only=True)
    candidate_profile_id = serializers.UUIDField(source="candidate_profile.id", read_only=True)
    match_report_id = serializers.UUIDField(source="match_report.id", read_only=True)

    class Meta:
        model = GeneratedAnswer
        fields = [
            "id",
            "job_id",
            "candidate_profile_id",
            "match_report_id",
            "answer_type",
            "content",
            "evidence_summary",
            "generator_version",
            "created_at",
            "updated_at",
        ]


class GeneratedAnswerListSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    candidate_profile_id = serializers.UUIDField(allow_null=True)
    match_report_id = serializers.UUIDField()
    answers = GeneratedAnswerSerializer(many=True)
