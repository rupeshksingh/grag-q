import pytest
from typing import Dict, List
from datetime import datetime
import json
from src.models.schema import QueryContext, PipelineState
from src.pipeline.nodes import PipelineNodes
from src.pipeline.graph import TenderPipelineGraph
from src.database.neo4j_client import Neo4jClient

@pytest.fixture
def mock_neo4j_response() -> List[Dict]:
    """Mock Neo4j query response"""
    return [
        {
            "id": "123",
            "properties": {
                "title": "Network Infrastructure Tender",
                "description": "Specifications for network setup",
                "created_at": "2024-01-15"
            },
            "score": 0.95,
            "metadata": {
                "document_type": "Technical",
                "version": "1.0"
            },
            "relationships": [
                {
                    "type": "REQUIRES",
                    "end_node": "456",
                    "properties": {"priority": "high"}
                }
            ]
        }
    ]

@pytest.fixture
def mock_claude_response():
    """Mock Claude API response"""
    class MockResponse:
        def __init__(self):
            self.content = json.dumps({
                "query_intent": "Find network infrastructure requirements",
                "key_concepts": ["network", "infrastructure", "requirements"],
                "temporal_aspects": {
                    "valid_from": "2024-01-01",
                    "valid_to": "2024-12-31",
                    "is_current": True
                }
            })
    return MockResponse()

@pytest.fixture
def mock_gpt4_response():
    """Mock GPT-4 API response"""
    class MockResponse:
        def __init__(self):
            self.content = "Enhanced query with technical specifications"
    return MockResponse()

@pytest.fixture
def sample_query_context() -> QueryContext:
    """Sample query context for testing"""
    return QueryContext(
        search_scope=["Technical", "Requirements"],
        relevance_threshold=0.8,
        max_results=50,
        include_metadata=True
    )

@pytest.fixture
def sample_pipeline_state(sample_query_context) -> PipelineState:
    """Sample pipeline state for testing"""
    return PipelineState(
        original_query="What are the network infrastructure requirements?",
        query_context=sample_query_context,
        current_node="query_analysis",
        retry_count=0,
        start_time=datetime.now()
    )

@pytest.fixture
def mock_neo4j_client(mock_neo4j_response, monkeypatch):
    """Mock Neo4j client for testing"""
    class MockNeo4jClient:
        def execute_query(self, query: str, parameters: Dict = None) -> List[Dict]:
            return mock_neo4j_response
            
        def close(self):
            pass
    
    monkeypatch.setattr("src.database.neo4j_client.Neo4jClient", MockNeo4jClient)
    return MockNeo4jClient()

@pytest.fixture
def mock_llm_clients(mock_claude_response, mock_gpt4_response, monkeypatch):
    """Mock LLM clients for testing"""
    class MockClaude:
        async def ainvoke(self, messages):
            return mock_claude_response
    
    class MockGPT4:
        async def ainvoke(self, messages):
            return mock_gpt4_response
    
    monkeypatch.setattr("langchain_anthropic.ChatAnthropic", MockClaude)
    monkeypatch.setattr("langchain_openai.ChatOpenAI", MockGPT4)
    return (MockClaude(), MockGPT4())