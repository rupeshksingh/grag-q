import pytest
from typing import Dict, List
import json
from datetime import datetime
from src.pipeline.graph import TenderPipelineGraph
from src.models.schema import QueryContext, PipelineState

@pytest.mark.asyncio
async def test_pipeline_initialization():
    """Test pipeline initialization"""
    pipeline = TenderPipelineGraph()
    assert pipeline.nodes is not None
    assert pipeline.graph is not None

@pytest.mark.asyncio
async def test_pipeline_execution(
    sample_query_context,
    mock_neo4j_client,
    mock_llm_clients
):
    """Test complete pipeline execution"""
    pipeline = TenderPipelineGraph()
    query = "What are the network infrastructure requirements?"
    
    result = await pipeline.run_pipeline(
        query=query,
        context=sample_query_context
    )
    
    assert result is not None
    assert "results" in result
    assert len(result["results"]) > 0
    assert "performance_metrics" in result

@pytest.mark.asyncio
async def test_pipeline_error_handling(
    sample_query_context,
    mock_neo4j_client,
    monkeypatch
):
    """Test pipeline error handling and retry logic"""
    # Mock error in query analysis
    class ErroringNode:
        async def query_analysis(self, state: PipelineState):
            raise Exception("Simulated error")
    
    monkeypatch.setattr("src.pipeline.nodes.PipelineNodes", ErroringNode)
    
    pipeline = TenderPipelineGraph()
    query = "What are the network infrastructure requirements?"
    
    with pytest.raises(Exception) as exc_info:
        await pipeline.run_pipeline(
            query=query,
            context=sample_query_context
        )
    
    assert "Simulated error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_pipeline_metrics(
    sample_query_context,
    mock_neo4j_client,
    mock_llm_clients
):
    """Test pipeline performance metrics collection"""
    pipeline = TenderPipelineGraph()
    query = "What are the network infrastructure requirements?"
    
    result = await pipeline.run_pipeline(
        query=query,
        context=sample_query_context
    )
    
    metrics = result["performance_metrics"]
    assert "total_duration" in metrics
    assert isinstance(metrics["total_duration"], float)
    assert metrics["total_duration"] > 0

@pytest.mark.asyncio
async def test_pipeline_context_handling(
    mock_neo4j_client,
    mock_llm_clients
):
    """Test pipeline handling of different query contexts"""
    pipeline = TenderPipelineGraph()
    query = "What are the network infrastructure requirements?"
    
    # Test with default context
    result1 = await pipeline.run_pipeline(query=query)
    assert result1 is not None
    
    # Test with custom context
    custom_context = QueryContext(
        search_scope=["Technical"],
        relevance_threshold=0.9,
        max_results=10,
        include_metadata=False
    )
    
    result2 = await pipeline.run_pipeline(
        query=query,
        context=custom_context
    )
    
    assert result2 is not None
    assert len(result2["results"]) <= custom_context.max_results

@pytest.mark.asyncio
async def test_pipeline_result_format(
    sample_query_context,
    mock_neo4j_client,
    mock_llm_clients
):
    """Test pipeline result format and structure"""
    pipeline = TenderPipelineGraph()
    query = "What are the network infrastructure requirements?"
    
    result = await pipeline.run_pipeline(
        query=query,
        context=sample_query_context
    )
    
    # Check result structure
    assert isinstance(result, dict)
    assert "results" in result
    assert "performance_metrics" in result
    
    # Check result content
    for item in result["results"]:
        assert "node_id" in item
        assert "content" in item
        assert "relevance_score" in item
        assert isinstance(item["relevance_score"], float)
        assert 0 <= item["relevance_score"] <= 1