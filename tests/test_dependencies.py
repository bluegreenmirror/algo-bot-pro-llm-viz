from pathlib import Path

REQUIREMENTS = Path(__file__).resolve().parent.parent / "requirements.txt"


def test_requirements_are_exactly_pinned():
    """Reproducible installs: every dependency pinned with == so pip-audit results hold."""
    lines = [
        line.strip() for line in REQUIREMENTS.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert lines
    unpinned = [line for line in lines if "==" not in line]
    assert unpinned == []
