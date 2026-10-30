import pytest
import asyncio
import tempfile
import os
import sqlite3
import json
from unittest.mock import AsyncMock, patch
from src.agent.core import ResearchAgent
from src.agent.models import ResearchPlan, ResearchStep, FinalAnswer, ConfidenceLevel
from src.agent.store import JobStore
from src.utils.config import Settings

@pytest.fixture
def mock_settings():
    return Settings(
        GEMINI_API_KEY="test_gemini_key",
        FIRECRAWL_API_KEY="test_firecrawl_key",
        GEMINI_MODEL="gemini-2.5-flash"
    )

@pytest.fixture
def temp_store():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    store = JobStore(db_path=db_path)
    yield store
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.mark.asyncio
async def test_startup_timeout_triggered(mock_settings, temp_store):
    agent = ResearchAgent(settings=mock_settings, store=temp_store)
    # Simulate startup timeout by passing 0s threshold
    result = await agent.run("test question", startup_timeout_seconds=-1.0)
    assert result.confidence_level == ConfidenceLevel.LOW
    assert "Startup timeout" in result.short_answer

@pytest.mark.asyncio
async def test_startup_timeout_cancelled_once_planning_starts(mock_settings, temp_store):
    with patch("src.agent.tools.WebTools.search", new_callable=AsyncMock) as mock_search, \
         patch("src.agent.tools.WebTools.scrape", new_callable=AsyncMock) as mock_scrape, \
         patch("src.agent.gemini_client.GeminiClient.generate_structured", new_callable=AsyncMock) as mock_gen:

        mock_search.return_value = [{"url": "https://example.com/page", "title": "Example"}]
        mock_scrape.return_value = "Detailed mock content for search and scrape verification."

        agent = ResearchAgent(settings=mock_settings, store=temp_store)

        mock_gen.side_effect = [
            ResearchPlan(query="test", steps=[ResearchStep(step_number=1, description="search", tool="search")], estimated_effort="low"),
            FinalAnswer(
                question="test question",
                short_answer="Answer completed beyond 3 minutes without getting killed.",
                findings=[],
                source_urls=["https://example.com/page"],
                confidence_level=ConfidenceLevel.HIGH,
                assumptions=["none"],
                limitations=["none"],
                unanswered_questions=["none"]
            )
        ]

        result = await agent.run("test question", startup_timeout_seconds=180.0)
        assert result.short_answer == "Answer completed beyond 3 minutes without getting killed."

@pytest.mark.asyncio
async def test_agent_checkpointing_and_resume(mock_settings, temp_store):
    job_id = "job-resume-test"
    with patch("src.agent.tools.WebTools.search", new_callable=AsyncMock) as mock_search, \
         patch("src.agent.tools.WebTools.scrape", new_callable=AsyncMock) as mock_scrape, \
         patch("src.agent.gemini_client.GeminiClient.generate_structured", new_callable=AsyncMock) as mock_gen:

        mock_search.return_value = [{"url": "https://example.com", "title": "Example"}]
        mock_scrape.return_value = "Valid content."

        agent = ResearchAgent(settings=mock_settings, store=temp_store)

        mock_gen.side_effect = [
            ResearchPlan(query="test", steps=[ResearchStep(step_number=1, description="search", tool="search")], estimated_effort="low"),
            FinalAnswer(
                question="test question",
                short_answer="Synthesized answer",
                findings=[],
                source_urls=["https://example.com"],
                confidence_level=ConfidenceLevel.HIGH,
                assumptions=[],
                limitations=[],
                unanswered_questions=[]
            )
        ]

        await agent.run("test question", job_id=job_id)
        saved_job = temp_store.get_job(job_id)
        assert saved_job["status"] == "completed"
        assert len(saved_job["logs"]) > 0

def test_legacy_database_migration_and_repeated_init():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        legacy_db_path = f.name

    try:
        # Create legacy table without 'logs' column
        conn = sqlite3.connect(legacy_db_path)
        conn.execute("""
            CREATE TABLE jobs (
                job_id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                status TEXT NOT NULL,
                current_stage TEXT NOT NULL,
                plan TEXT,
                sources TEXT,
                final_answer TEXT,
                error TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            INSERT INTO jobs (job_id, question, status, current_stage)
            VALUES ('legacy-job-1', 'Legacy question?', 'completed', 'done')
        """)
        conn.commit()
        conn.close()

        # Initialize JobStore on legacy database
        store = JobStore(db_path=legacy_db_path)

        # Retrieve legacy job
        legacy_job = store.get_job("legacy-job-1")
        assert legacy_job is not None
        assert legacy_job["job_id"] == "legacy-job-1"
        assert legacy_job["logs"] == []

        # Add log to legacy job
        store.add_log("legacy-job-1", "Added new log after migration.")
        updated_job = store.get_job("legacy-job-1")
        assert updated_job["logs"] == ["Added new log after migration."]

        # Ensure repeated initialization causes no errors
        store_again = JobStore(db_path=legacy_db_path)
        repeated_job = store_again.get_job("legacy-job-1")
        assert repeated_job["logs"] == ["Added new log after migration."]

    finally:
        if os.path.exists(legacy_db_path):
            os.remove(legacy_db_path)
