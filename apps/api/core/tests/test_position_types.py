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
