import pytest

from src.agent.models import FinalAnswer
from src.api import main as api


def _job(job_id, final_answer):
    return {
        "job_id": job_id,
        "question": "Research question",
        "status": "completed",
        "current_stage": "done",
        "logs": [],
        "updated_at": "2026-10-30T12:00:00",
        "error": None,
        "final_answer": final_answer,
    }


def _valid_final_answer():
    return {
        "question": "Research question",
        "short_answer": "Grounded summary.",
        "findings": [],
        "source_urls": [],
        "confidence_level": "low",
        "assumptions": [],
        "limitations": [],
        "unanswered_questions": [],
    }


@pytest.mark.asyncio
async def test_list_jobs_keeps_legacy_report_from_failing_the_entire_response(monkeypatch):
    legacy_report = {
        "question": "Research question",
        "short_answer": "Older report format.",
        "key_findings": ["A claim with no structured evidence."],
        "source_urls": [],
        "confidence_level": "low",
        "assumptions": [],
        "limitations": [],
        "confidence_breakdown": {
            "source_relevance": 0.8,
            "citation_support": 1.0,
        },
    }

    class Store:
        def list_jobs(self):
            return [
                _job("legacy", legacy_report),
                _job("current", _valid_final_answer()),
            ]

    monkeypatch.setattr(api, "store", Store())

    response = await api.list_jobs()

    assert len(response) == 2
    assert response[0].job_id == "legacy"
    assert response[0].result is None
    assert response[0].error == "Stored report is incompatible with the current report schema."
    assert isinstance(response[1].result, FinalAnswer)
    assert response[1].error is None


@pytest.mark.asyncio
async def test_get_job_status_reports_incompatible_stored_report(monkeypatch):
    class Store:
        def get_job(self, job_id):
            return _job(
                job_id,
                {
                    "question": "Research question",
                    "short_answer": "Incomplete report.",
                },
            )

    monkeypatch.setattr(api, "store", Store())

    response = await api.get_job_status("legacy")

    assert response.result is None
    assert response.error == "Stored report is incompatible with the current report schema."
