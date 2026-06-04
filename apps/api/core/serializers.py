from rest_framework import serializers

from core.models import CandidateProfile, GeneratedAnswer, Job, MatchReport, RecruitingPreferences


class JobComputedFieldsSerializerMixin(serializers.ModelSerializer):
    latest_match_score = serializers.IntegerField(read_only=True, allow_null=True)
    latest_recommendation = serializers.CharField(read_only=True, allow_null=True)
    latest_match_report_id = serializers.UUIDField(read_only=True, allow_null=True)
    latest_analysis_created_at = serializers.DateTimeField(read_only=True, allow_null=True)
    relevance_score = serializers.IntegerField(read_only=True, allow_null=True)


class CandidateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateProfile
        fields = ["id", "resume_text", "normalized_skills", "created_at", "updated_at"]
        read_only_fields = ["id", "normalized_skills", "created_at", "updated_at"]


class RecruitingPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecruitingPreferences
        fields = [
            "id",
            "target_terms",
            "role_types",
            "preferred_locations",
            "remote_preference",
            "preferred_industries",
            "excluded_keywords",
            "minimum_match_score",
            "include_sponsorship_required_roles",
            "include_clearance_required_roles",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class JobCreateSerializer(JobComputedFieldsSerializerMixin):
    class Meta:
        model = Job
        fields = [
            "id",
            "company_name",
            "title",
            "location",
            "raw_text",
            "source_type",
            "source_url",
            "external_id",
            "content_hash",
            "last_seen_at",
            "ingestion_status",
            "workflow_status",
            "applied_date",
            "notes",
            "next_action",
            "next_action_due_date",
            "is_archived",
            "is_hidden",
            "is_saved",
            "normalized_requirements",
            "normalized_preferred",
            "relevance",
            "relevance_reasons",
            "relevance_flags",
            "relevance_last_evaluated_at",
            "created_at",
            "updated_at",
            "latest_match_score",
            "latest_recommendation",
            "latest_match_report_id",
            "latest_analysis_created_at",
            "relevance_score",
        ]
        read_only_fields = [
            "id",
            "source_type",
            "source_url",
            "external_id",
            "content_hash",
            "last_seen_at",
            "ingestion_status",
            "workflow_status",
            "applied_date",
            "notes",
            "next_action",
            "next_action_due_date",
            "is_archived",
            "is_hidden",
            "is_saved",
            "normalized_requirements",
            "normalized_preferred",
            "relevance",
            "relevance_reasons",
            "relevance_flags",
            "relevance_last_evaluated_at",
            "created_at",
            "updated_at",
            "latest_match_score",
            "latest_recommendation",
            "latest_match_report_id",
            "latest_analysis_created_at",
            "relevance_score",
        ]


class JobIngestUrlSerializer(serializers.Serializer):
    url = serializers.URLField()


class JobListSerializer(JobComputedFieldsSerializerMixin):
    class Meta:
        model = Job
        fields = [
            "id",
            "company_name",
            "title",
            "location",
            "source_type",
            "source_url",
            "external_id",
            "content_hash",
            "last_seen_at",
            "ingestion_status",
            "workflow_status",
            "applied_date",
            "notes",
            "next_action",
            "next_action_due_date",
            "is_archived",
            "is_hidden",
            "is_saved",
            "normalized_requirements",
            "normalized_preferred",
            "relevance",
            "relevance_reasons",
            "relevance_flags",
            "relevance_last_evaluated_at",
            "created_at",
            "updated_at",
            "latest_match_score",
            "latest_recommendation",
            "latest_match_report_id",
            "latest_analysis_created_at",
            "relevance_score",
        ]


class JobDetailSerializer(JobListSerializer):
    class Meta(JobListSerializer.Meta):
        fields = JobListSerializer.Meta.fields + ["raw_text"]


class JobUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            "workflow_status",
            "applied_date",
            "notes",
            "next_action",
            "next_action_due_date",
            "is_archived",
        ]


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
