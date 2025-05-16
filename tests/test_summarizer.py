from hirag_mcp.summarization import TrancatedAggregateSummarizer
from hirag_mcp._llm import gpt_4o_mini_complete
import asyncio
import pytest


@pytest.mark.asyncio
async def test_summarizer():
    summarizer = TrancatedAggregateSummarizer(
        extract_func=gpt_4o_mini_complete,
    )
    summary = await summarizer.summarize_entity(
        entity_name="test",
        descriptions=[
            "This is a unit test for the summarizer",
            "Unit test for the summaring entity descriptions",
        ],
    )
    assert summary is not None
