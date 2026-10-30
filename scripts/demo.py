import asyncio
import json
from unittest.mock import AsyncMock, patch
from src.agent.core import ResearchAgent
from src.agent.models import ResearchPlan, ResearchStep, FinalAnswer, ConfidenceLevel
from src.utils.config import get_settings

async def run_demo():
    settings = get_settings()
    agent = ResearchAgent(settings=settings)

    print("--- DEMO 1: Simulated Successful Research Query ---")
    question = "What are the latest developments in AI observability?"
    print(f"Query: {question}")

    # Use mocks for demo to avoid live API quota issues
    with patch("src.agent.tools.WebTools.search", new_callable=AsyncMock) as mock_search, \
         patch("src.agent.tools.WebTools.scrape", new_callable=AsyncMock) as mock_scrape, \
         patch("src.agent.gemini_client.GeminiClient.generate_structured", new_callable=AsyncMock) as mock_gen:

        mock_search.return_value = [{"url": "https://example.com", "title": "Example"}]
        mock_scrape.return_value = "Long valid content for AI observability."
        mock_gen.side_effect = [
            ResearchPlan(query=question, steps=[ResearchStep(step_number=1, description="search", tool="search")], estimated_effort="low"),
            FinalAnswer(
                question=question,
                short_answer="AI observability is advancing with new tracing standards.",
                key_findings=["Finding A", "Finding B"],
                source_urls=["https://example.com"],
                confidence_level=ConfidenceLevel.HIGH,
                assumptions=["none"],
                limitations=["none"],
                next_steps=["none"]
            )
        ]

        result = await agent.run(question)
        print(json.dumps(result.model_dump(mode='json'), indent=2))

    print("\n--- DEMO 2: Edge Case (Simulated Tool Failure) ---")
    # Simulate a failure in search results to trigger the fallback logic
    with patch("src.agent.tools.WebTools.search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = [] # Return empty to simulate failure/no results

        result = await agent.run("What is the speed of thought?")
        print(f"Confidence Level: {result.confidence_level}")
        print(f"Result: {result.short_answer}")
        print(f"Limitations: {result.limitations}")

if __name__ == "__main__":
    asyncio.run(run_demo())
