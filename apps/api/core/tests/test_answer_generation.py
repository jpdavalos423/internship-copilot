from django.test import SimpleTestCase

from core.services.answer_validation import (
    AnswerValidationError,
    validate_generated_answer,
)


class AnswerValidationTests(SimpleTestCase):
    def test_validation_rejects_unsupported_numeric_claims(self):
        with self.assertRaises(AnswerValidationError):
            validate_generated_answer(
                content="I improved performance by 200%.",
                evidence_summary=["Resume references Python"],
                source_texts=["Built REST APIs with Python.", "Backend Software Engineer Intern"],
            )

    def test_validation_allows_general_non_numeric_wording(self):
        result = validate_generated_answer(
            content="I have built backend projects with Python and Django.",
            evidence_summary=["Resume references Python and Django"],
            source_texts=["Built backend projects with Python and Django."],
        )

        assert result.content == "I have built backend projects with Python and Django."
        assert result.evidence_summary == ["Resume references Python and Django"]
