from pathlib import Path

from models import Company
from resume import ResumeState


def test_resume_state_tracks_completed_rows():

    path = Path("resume_state_test.json")
    company = Company(row_number=5, company_name="Example Finance")

    try:
        if path.exists():
            path.unlink()

        state = ResumeState(path)
        assert not state.should_skip(company)

        state.mark_completed(company)

        restored = ResumeState(path)
        assert restored.should_skip(company)
    finally:
        if path.exists():
            path.unlink()
