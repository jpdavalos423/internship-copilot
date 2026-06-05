from django.test import TestCase

from core.models import Job
from core.services.position_types import infer_position_type


class PositionTypeInferenceTests(TestCase):
    def test_infers_intern_from_common_keywords(self):
        result = infer_position_type(
            title="Software Engineer Intern",
            location="Remote",
            raw_text="Summer internship role working on backend systems.",
        )

        assert result == Job.PositionType.INTERN

    def test_infers_full_time_for_new_grad_roles(self):
        result = infer_position_type(
            title="New Grad Software Engineer",
            location="Remote",
            raw_text="Entry-level graduate role for 2027 candidates.",
        )

        assert result == Job.PositionType.FULL_TIME

    def test_infers_part_time_when_explicit(self):
        result = infer_position_type(
            title="IT Support Assistant",
            location="San Francisco, CA",
            raw_text="Part-time role supporting internal IT operations.",
        )

        assert result == Job.PositionType.PART_TIME

    def test_does_not_treat_internal_or_integral_as_intern(self):
        result = infer_position_type(
            title="Security Engineer, Infrastructure",
            location="Remote",
            raw_text="This role is integral to our internal distributed platform and international expansion.",
        )

        assert result == Job.PositionType.UNKNOWN

    def test_prefers_title_and_early_description_over_footer_internships_text(self):
        result = infer_position_type(
            title="Software Engineer, Distributed Systems",
            location="San Francisco, CA",
            raw_text=(
                "This is a full time role that can be held from one of our US hubs or remotely in the United States. "
                + ("x" * 2200)
                + " Learn more about our internships program."
            ),
            source_url="https://job-boards.greenhouse.io/figma/jobs/5552549004",
        )

        assert result == Job.PositionType.FULL_TIME

    def test_does_not_infer_intern_from_footer_only_mentions(self):
        result = infer_position_type(
            title="Backend Software Engineer (Evals)",
            location="San Francisco, CA",
            raw_text=(
                "We are looking for a backend engineer to build eval infrastructure for production systems."
                + ("x" * 2200)
                + " Learn more about our internships."
            ),
            source_url="https://jobs.ashbyhq.com/openai/3d064454-c0c3-4225-bc2c-6d8c0f8735b2",
        )

        assert result == Job.PositionType.UNKNOWN
