import typer
import asyncio
from src.agent.core import ResearchAgent
from src.utils.logging import logger
from src.utils.config import get_settings
import json

# Initialize settings once
settings = get_settings()

app = typer.Typer()

@app.command()
def research(question: str):
    """Run a research task via CLI."""
    async def _run():
        agent = ResearchAgent(settings=settings)
        try:
            result = await agent.run(question)
            print("\n" + "="*50)
            print("RESEARCH RESULT")
            print("="*50)
            print(json.dumps(result.model_dump(mode='json'), indent=2))
        except Exception as e:
            logger.error(f"Execution failed: {e}")

    asyncio.run(_run())

if __name__ == "__main__":
    app()
