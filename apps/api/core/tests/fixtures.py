from pathlib import Path


SAMPLES_DIR = Path(__file__).resolve().parents[4] / "data" / "samples"


def load_sample(name: str) -> str:
    return (SAMPLES_DIR / name).read_text()
