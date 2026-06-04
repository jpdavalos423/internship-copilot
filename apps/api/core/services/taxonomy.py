from __future__ import annotations

import re

CATEGORY_ORDER = [
    "languages",
    "frontend",
    "backend",
    "databases",
    "cloud",
    "devops",
    "systems",
    "ai_ml",
]

SKILL_DEFINITIONS = {
    "python": {"category": "languages", "aliases": ["python"]},
    "java": {"category": "languages", "aliases": ["java"]},
    "c++": {"category": "languages", "aliases": ["c++", "cpp"]},
    "javascript": {"category": "languages", "aliases": ["javascript"]},
    "typescript": {"category": "languages", "aliases": ["typescript"]},
    "go": {"category": "languages", "aliases": ["golang", "go language"]},
    "rust": {"category": "languages", "aliases": ["rust"]},
    "sql": {"category": "languages", "aliases": ["sql"]},
    "react": {"category": "frontend", "aliases": ["react", "reactjs", "react.js"]},
    "next.js": {"category": "frontend", "aliases": ["next.js", "nextjs"]},
    "html": {"category": "frontend", "aliases": ["html", "html5"]},
    "css": {"category": "frontend", "aliases": ["css", "css3"]},
    "tailwind css": {"category": "frontend", "aliases": ["tailwind", "tailwind css"]},
    "redux": {"category": "frontend", "aliases": ["redux"]},
    "django": {"category": "backend", "aliases": ["django"]},
    "flask": {"category": "backend", "aliases": ["flask"]},
    "fastapi": {"category": "backend", "aliases": ["fastapi"]},
    "node.js": {"category": "backend", "aliases": ["node.js", "nodejs"]},
    "express": {"category": "backend", "aliases": ["express.js", "expressjs"]},
    "spring boot": {"category": "backend", "aliases": ["spring boot"]},
    "rest api": {
        "category": "backend",
        "aliases": ["rest api", "rest apis", "restful api", "restful apis"],
    },
    "graphql": {"category": "backend", "aliases": ["graphql"]},
    "microservices": {"category": "backend", "aliases": ["microservices", "microservice"]},
    "postgresql": {"category": "databases", "aliases": ["postgresql", "postgres", "postgre"]},
    "mysql": {"category": "databases", "aliases": ["mysql"]},
    "sqlite": {"category": "databases", "aliases": ["sqlite"]},
    "mongodb": {"category": "databases", "aliases": ["mongodb", "mongo db"]},
    "redis": {"category": "databases", "aliases": ["redis"]},
    "aws": {"category": "cloud", "aliases": ["aws", "amazon web services"]},
    "gcp": {"category": "cloud", "aliases": ["gcp", "google cloud", "google cloud platform"]},
    "azure": {"category": "cloud", "aliases": ["azure"]},
    "aws lambda": {"category": "cloud", "aliases": ["aws lambda"]},
    "s3": {"category": "cloud", "aliases": ["s3", "amazon s3"]},
    "ec2": {"category": "cloud", "aliases": ["ec2", "amazon ec2"]},
    "docker": {"category": "devops", "aliases": ["docker", "containerization", "containers"]},
    "kubernetes": {"category": "devops", "aliases": ["kubernetes", "k8s"]},
    "ci/cd": {"category": "devops", "aliases": ["ci/cd", "continuous integration", "continuous delivery"]},
    "github actions": {"category": "devops", "aliases": ["github actions"]},
    "git": {"category": "devops", "aliases": ["git"]},
    "terraform": {"category": "devops", "aliases": ["terraform"]},
    "linux": {"category": "systems", "aliases": ["linux"]},
    "distributed systems": {
        "category": "systems",
        "aliases": ["distributed systems", "distributed system"],
    },
    "operating systems": {"category": "systems", "aliases": ["operating systems"]},
    "networking": {"category": "systems", "aliases": ["networking", "computer networks"]},
    "concurrency": {"category": "systems", "aliases": ["concurrency", "concurrent programming"]},
    "multithreading": {"category": "systems", "aliases": ["multithreading", "multi-threading"]},
    "machine learning": {"category": "ai_ml", "aliases": ["machine learning"]},
    "deep learning": {"category": "ai_ml", "aliases": ["deep learning"]},
    "pytorch": {"category": "ai_ml", "aliases": ["pytorch", "torch"]},
    "tensorflow": {"category": "ai_ml", "aliases": ["tensorflow"]},
    "llms": {"category": "ai_ml", "aliases": ["llms", "large language models"]},
    "nlp": {"category": "ai_ml", "aliases": ["nlp", "natural language processing"]},
    "computer vision": {"category": "ai_ml", "aliases": ["computer vision"]},
}


def _compile_pattern(term: str) -> re.Pattern[str]:
    escaped = re.escape(term)
    escaped = escaped.replace(r"\ ", r"\s+")
    return re.compile(rf"(?<!\w){escaped}(?!\w)", flags=re.IGNORECASE)


SKILL_PATTERNS = {
    canonical: [_compile_pattern(term) for term in definition["aliases"]]
    for canonical, definition in SKILL_DEFINITIONS.items()
}


def get_skill_category(skill: str) -> str | None:
    definition = SKILL_DEFINITIONS.get(skill)
    if definition is None:
        return None
    return str(definition["category"])


def extract_skills(text: str) -> list[str]:
    normalized_text = text.lower()
    matches: list[str] = []
    for canonical, patterns in SKILL_PATTERNS.items():
        if any(pattern.search(normalized_text) for pattern in patterns):
            matches.append(canonical)
    return sorted(matches)


def group_skills_by_category(skills: list[str] | set[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for category in CATEGORY_ORDER:
        category_skills = sorted(skill for skill in skills if get_skill_category(skill) == category)
        if category_skills:
            grouped[category] = category_skills
    return grouped
