from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator, ConfigDict
from datetime import datetime
import json

class QueryContext(BaseModel):
    """Enhanced context information for query processing with validation"""
    timestamp: datetime = Field(default_factory=datetime.now)
    search_scope: List[str] = Field(
        default_factory=list,
        description="List of document types to search through"
    )
    relevance_threshold: float = Field(
        default=0.7,
        ge=0,
        le=1,
        description="Minimum relevance score for results"
    )
    max_results: int = Field(
        default=100,
        ge=1,
        description="Maximum number of results to return"
    )
    include_metadata: bool = Field(
        default=True,
        description="Whether to include document metadata in results"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "search_scope": ["Technical", "Requirements"],
                "relevance_threshold": 0.8,
                "max_results": 50,
                "include_metadata": True
            }
        }
    )

class TemporalAspects(BaseModel):
    """Temporal constraints for document validity"""
    valid_from: Optional[str] = Field(
        None,
        description="Start date in YYYY-MM-DD format"
    )
    valid_to: Optional[str] = Field(
        None,
        description="End date in YYYY-MM-DD format"
    )
    is_current: bool = Field(
        True,
        description="Whether the document is currently valid"
    )
    
    @validator('valid_from', 'valid_to')
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")

class QueryResult(BaseModel):
    """Enhanced query result with detailed metadata"""
    node_id: str = Field(..., description="Unique identifier of the node")
    content: Dict = Field(..., description="Node properties and content")
    relevance_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Relevance score of the result"
    )
    metadata: Optional[Dict] = Field(
        None,
        description="Additional metadata about the result"
    )
    relationships: List[Dict] = Field(
        default_factory=list,
        description="Related nodes and their relationships"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Time when the result was generated"
    )
    
    def to_json(self) -> str:
        """Convert the result to a JSON string"""
        return json.dumps(self.model_dump(), default=str)
    
    @validator('relationships')
    def validate_relationships(cls, v: List[Dict]) -> List[Dict]:
        """Validate relationship structure"""
        required_keys = {'type', 'target'}
        for rel in v:
            if not required_keys.issubset(rel.keys()):
                raise ValueError(f"Relationship missing required keys: {required_keys}")
        return v

class PipelineState(BaseModel):
    """Enhanced state management with performance tracking"""
    original_query: str
    query_context: QueryContext
    enhanced_query: Optional[str] = None
    cypher_query: Optional[str] = None
    validation_status: Optional[bool] = None
    results: Optional[List[QueryResult]] = None
    current_node: str
    history: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    retry_count: int = Field(default=0, ge=0)
    performance_metrics: Dict = Field(default_factory=dict)
    start_time: datetime = Field(default_factory=datetime.now)
    
    def add_metric(self, name: str, value: Union[float, int, str]) -> None:
        """Add a performance metric"""
        self.performance_metrics[name] = value
    
    def get_duration(self) -> float:
        """Get total pipeline duration in seconds"""
        return (datetime.now() - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict:
        """Convert state to dictionary with proper datetime handling"""
        return json.loads(self.model_dump_json())