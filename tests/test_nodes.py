import pytest
from typing import Dict, List
from src.pipeline.nodes import PipelineNodes
from src.models.schema import PipelineState, QueryContext

@pytest.mark.asyncio
async def test_query_analysis(
    sample_pipeline_state,
    mock_llm_clients
):
    """Test query analysis node"""
    nodes = PipelineNodes()
    
    result = await nodes.query_analysis(sample_pipeline_state)
    
    assert result is not None
    assert result.enhanced_query is not None
    assert "analysis_results" in result.model_dump()
    assert result.error is None

@pytest.mark.asyncio
async def test_query_enhancement(
    sample_pipeline_state,
    mock_llm_clients
):
    """Test query enhancement node"""
    nodes = PipelineNodes()
    
    # First run analysis to get required state
    state_with_analysis = await nodes.query_analysis(sample_pipeline_state)
    result = await nodes.query_enhancement(state_with_analysis)
    
    assert result is not None
    assert result.enhanced_query is not None
    assert isinstance(result.enhanced_query, str)
    assert result.error is None

@pytest.mark.asyncio
async def test_cypher_generation(
    sample_pipeline_state,
    mock_llm_clients
):
    """Test Cypher query generation node"""
    nodes = PipelineNodes()
    
    # Prepare state with required previous steps
    state_with_analysis = await nodes.query_analysis(sample_pipeline_state)
    state_with_enhancement = await nodes.query_enhancement(state_with_analysis)
    
    result = await nodes.cypher_generation(state_with_enhancement)
    
    assert result is not None
    assert result.cypher_query is not None
    assert isinstance(result.cypher_query, str)
    assert "MATCH" in result.cypher_query.upper()
    assert result.error is None

@pytest.mark.asyncio
async def test_query_execution(
    sample_pipeline_state,
    mock_neo4j_client,
    mock_llm_clients
):
    """Test query execution node"""
    nodes = PipelineNodes()
    
    # Prepare state with required previous steps
    state_with_analysis = await nodes.query_analysis(sample_pipeline_state)
    state_with_enhancement = await nodes.query_enhancement(state_with_analysis)
    state_with_cypher = await nodes.cypher_generation(state_with_enhancement)
    
    result = await nodes.query_execution(state_with_cypher)
    
    assert result is not None
    assert result.results is not None
    assert len(result.results) > 0
    assert result.error is None

@pytest.mark.asyncio
async def test_error_handling(
    sample_pipeline_state,
    mock_neo4j_client,
    mock_llm_clients,
    monkeypatch
):
    """Test error handling in nodes"""
    nodes = PipelineNodes()
    
    # Mock error in Neo4j client
    class ErroringNeo4jClient:
        def execute_query(self, *args, **kwargs):
            raise Exception("Database error")
    
    monkeypatch.setattr(nodes, "neo4j_client", ErroringNeo4jClient())
    
    # Prepare state with required previous steps
    state_with_analysis = await nodes.query_analysis(sample_pipeline_state)
    state_with_enhancement = await nodes.query_enhancement(state_with_analysis)
    state_with_cypher = await nodes.cypher_generation(state_with_enhancement)
    
    with pytest.raises(Exception) as exc_info:
        await nodes.query_execution(state_with_cypher)
    
    assert "Database error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_progress_tracking(
    sample_pipeline_state,
    mock_neo4j_client,
    mock_llm_clients
):
    """Test progress bar functionality"""
    nodes = PipelineNodes()
    
    # Monitor progress bars during execution
    progress_bars_before = len(nodes.progress_bars)
    
    result = await nodes.query_analysis(sample_pipeline_state)
    
    progress_bars_after = len(nodes.progress_bars)
    assert progress_bars_after >= progress_bars_before

@pytest.mark.asyncio
async def test_performance_metrics(
    sample_pipeline_state,
    mock_neo4j_client,
    mock_llm_clients
):
    """Test performance metrics collection"""
    nodes = PipelineNodes()
    
    result = await nodes.query_analysis(sample_pipeline_state)
    
    assert "performance_metrics" in result.model_dump()
    metrics = result.performance_metrics
    assert "analysis_duration" in metrics
    assert isinstance(metrics["analysis_duration"], float)

@pytest.mark.asyncio
async def test_retry_logic(
    sample_pipeline_state,
    mock_neo4j_client,
    mock_llm_clients,
    monkeypatch
):
    """Test retry logic in nodes"""
    nodes = PipelineNodes()
    
    # Mock intermittent failures
    failure_count = 0
    
    class IntermittentClient:
        def execute_query(self, *args, **kwargs):
            nonlocal failure_count
            if failure_count < 2:
                failure_count += 1
                raise Exception("Temporary error")
            return [{"id": "123", "properties": {}}]
    
    monkeypatch.setattr(nodes, "neo4j_client", IntermittentClient())
    
    # Should succeed after retries
    state_with_analysis = await nodes.query_analysis(sample_pipeline_state)
    state_with_enhancement = await nodes.query_enhancement(state_with_analysis)
    state_with_cypher = await nodes.cypher_generation(state_with_enhancement)
    
    result = await nodes.query_execution(state_with_cypher)
    
    assert result is not None
    assert result.error is None
    assert failure_count == 2  # Verify retry occurred