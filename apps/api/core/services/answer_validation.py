import re
from dataclasses import dataclass


NUMBER_PATTERN = re.compile(r"\b\d+(?:\.\d+)?%?\b")


@dataclass
class ValidatedAnswer:
    content: str
    evidence_summary: list[str]


class AnswerValidationError(ValueError):
    pass


def validate_generated_answer(
    *,
    content: str,
    evidence_summary: list[str],
    source_texts: list[str],
) -> ValidatedAnswer:
    normalized_content = content.strip()
    if not normalized_content:
        raise AnswerValidationError("Generated answer content cannot be empty")

    normalized_evidence = [item.strip() for item in evidence_summary if item.strip()]
    if not normalized_evidence:
        raise AnswerValidationError("Generated answers must include at least one evidence item")

    source_numbers = set()
    for text in source_texts:
        source_numbers.update(NUMBER_PATTERN.findall(text))

    content_numbers = set(NUMBER_PATTERN.findall(normalized_content))
    unsupported_numbers = sorted(number for number in content_numbers if number not in source_numbers)
    if unsupported_numbers:
        raise AnswerValidationError(
            f"Generated answer includes unsupported numeric claims: {', '.join(unsupported_numbers)}"
        )

    return ValidatedAnswer(content=normalized_content, evidence_summary=normalized_evidence)
