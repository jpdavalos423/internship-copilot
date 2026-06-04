from rest_framework import serializers

from core.models import CandidateProfile, GeneratedAnswer, Job, JobSource, MatchReport, RecruitingPreferences
from core.services.job_discovery import normalize_source_base_url


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
            "position_types",
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


class DiscoveryScanSummarySerializer(serializers.Serializer):
    discovered_count = serializers.IntegerField()
    created_count = serializers.IntegerField()
    duplicate_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    skipped_count = serializers.IntegerField()
    errors = serializers.ListField(child=serializers.CharField())


class JobSourceSerializer(serializers.ModelSerializer):
    last_scan_summary = DiscoveryScanSummarySerializer(read_only=True)

    class Meta:
        model = JobSource
        fields = [
            "id",
            "name",
            "source_type",
            "base_url",
            "company_name",
            "is_active",
            "last_scanned_at",
            "last_success_at",
            "last_error",
            "scan_interval_hours",
            "last_scan_summary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "last_scanned_at",
            "last_success_at",
            "last_error",
            "last_scan_summary",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        source_type = attrs.get("source_type")
        base_url = attrs.get("base_url")
        if source_type and base_url:
            _normalized_type, normalized_url = normalize_source_base_url(base_url, source_type)
            attrs["base_url"] = normalized_url
        elif base_url and self.instance is not None:
            _normalized_type, normalized_url = normalize_source_base_url(
                base_url,
                source_type or self.instance.source_type,
            )
            attrs["base_url"] = normalized_url
        return attrs

    def validate_scan_interval_hours(self, value):
        if value <= 0:
            raise serializers.ValidationError("Scan interval must be at least 1 hour.")
        return value


class JobCreateSerializer(JobComputedFieldsSerializerMixin):
    class Meta:
        model = Job
        fields = [
            "id",
            "company_name",
            "title",
            "location",
            "position_type",
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
            "position_type",
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
            "position_type",
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
            "position_type",
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
