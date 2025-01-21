from typing import Dict, List, Optional, Any
from datetime import datetime
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from src.models.schema import (
    QueryContext, QueryResult, PipelineState,
    QueryAnalysis, TemporalAspects
)
from src.logging.logger import setup_logger
from src.config.settings import get_settings
from src.database.neo4j_client import Neo4jClient

settings = get_settings()
logger = setup_logger("pipeline_nodes")

class PipelineNodes:
    def __init__(self):
        self.neo4j_client = Neo4jClient()
        self.claude = ChatAnthropic(
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            model="claude-3-5-sonnet-latest",
            temperature=0
        )
        self.gpt4 = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model="chatgpt-4o-latest",
            temperature=0
        )
        self.progress_bars = {}

    def _create_progress_bar(self, desc: str, total: int = 100) -> tqdm:
        """Create a progress bar for a pipeline stage"""
        return tqdm(total=total, desc=desc, position=len(self.progress_bars))

    def _update_metrics(self, state: PipelineState, metrics: Dict[str, Any]) -> None:
        """Update performance metrics with timing information"""
        for key, value in metrics.items():
            state.add_metric(key, value)

    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=settings.RETRY_DELAY)
    )
    async def query_analysis(self, state: PipelineState) -> PipelineState:
        """Enhanced query analysis with progress tracking"""
        logger.info(f"Starting query analysis for: {state.original_query}")
        progress = self._create_progress_bar("Query Analysis")
        
        try:
            parser = PydanticOutputParser(pydantic_object=QueryAnalysis)
            
            system_prompt = """You are an expert system specialized in analyzing queries 
            for a tender document knowledge graph. Your task is to analyze queries and 
            provide structured output that strictly follows the specified JSON format."""
            
            # Enhanced prompt template with clear instructions
            prompt_template = PromptTemplate(
                template="""
                {system_prompt}

                ANALYSIS REQUIREMENTS:
                1. Query Intent: {query}
                2. Key Concepts: Extract main entities and concepts
                3. Temporal Aspects: Identify time-related constraints
                4. Document Scope: Specify relevant document types
                5. Relationship Patterns: Define document connections
                6. Compliance Checks: List compliance requirements

                Format Instructions:
                {format_instructions}
                
                Return the analysis in the exact format specified.
                """,
                input_variables=["query"],
                partial_variables={
                    "system_prompt": system_prompt,
                    "format_instructions": parser.get_format_instructions()
                }
            )

            progress.update(30)
            
            # Create messages for the model
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt_template.format(query=state.original_query))
            ]
            
            progress.update(60)
            
            # Get response from GPT-4
            response = await self.gpt4.ainvoke(messages)
            analysis = parser.parse(response.content)
            
            progress.update(100)
            progress.close()
            
            # Update state with parsed data and metrics
            updated_state = state.model_copy(
                update={
                    "query_context": QueryContext(
                        search_scope=analysis.document_scope,
                        timestamp=datetime.now()
                    ),
                    "enhanced_query": analysis.query_intent,
                    "analysis_results": analysis.model_dump(),
                    "history": state.history + [str(m) for m in messages] + [str(response)]
                }
            )
            
            self._update_metrics(updated_state, {
                "analysis_duration": updated_state.get_duration(),
                "analysis_confidence": 0.95  # Example metric
            })
            
            logger.info("Query analysis completed successfully")
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in query analysis: {str(e)}", exc_info=True)
            raise

    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=settings.RETRY_DELAY)
    )
    async def query_enhancement(self, state: PipelineState) -> PipelineState:
        """Enhanced query enhancement with context awareness"""
        logger.info("Starting query enhancement")
        progress = self._create_progress_bar("Query Enhancement")
        
        try:
            system_prompt = """You are an expert in enhancing queries for tender document 
            retrieval. Transform the analyzed query into a more comprehensive search 
            specification."""
            
            enhancement_prompt = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"""
                Original query: {state.original_query}
                Analysis results: {state.analysis_results}
                
                Enhance this query by:
                1. Adding relevant contextual parameters
                2. Specifying document type constraints
                3. Including temporal considerations
                4. Adding relationship patterns
                
                Return the enhanced query specification.
                """)
            ]
            
            progress.update(50)
            
            response = await self.claude.ainvoke(enhancement_prompt)
            
            progress.update(100)
            progress.close()
            
            updated_state = state.model_copy(
                update={
                    "enhanced_query": response.content,
                    "history": state.history + [str(m) for m in enhancement_prompt] + [str(response)]
                }
            )
            
            self._update_metrics(updated_state, {
                "enhancement_duration": updated_state.get_duration(),
                "enhancement_quality_score": 0.9  # Example metric
            })
            
            logger.info("Query enhancement completed successfully")
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in query enhancement: {str(e)}", exc_info=True)
            raise

    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=settings.RETRY_DELAY)
    )
    async def cypher_generation(self, state: PipelineState) -> PipelineState:
        """Generate optimized Cypher query with modern features"""
        logger.info("Starting Cypher query generation")
        progress = self._create_progress_bar("Cypher Generation")
        
        try:
            cypher_prompt = f"""Generate an optimized Cypher query for: {state.enhanced_query}
            
            Requirements:
            1. Use modern Cypher features (pattern comprehension, list comprehension)
            2. Implement efficient path finding
            3. Use graph projections where appropriate
            4. Include proper parameter usage for security
            5. Optimize for performance with appropriate indexes
            
            Document types: {state.query_context.search_scope}
            Relevance threshold: {state.query_context.relevance_threshold}
            """
            
            progress.update(40)
            
            messages = [
                SystemMessage(content="You are an expert in Neo4j and Cypher query optimization."),
                HumanMessage(content=cypher_prompt)
            ]
            
            response = await self.claude.ainvoke(messages)
            
            progress.update(100)
            progress.close()
            
            updated_state = state.model_copy(
                update={
                    "cypher_query": response.content,
                    "history": state.history + [str(m) for m in messages] + [str(response)]
                }
            )
            
            self._update_metrics(updated_state, {
                "cypher_generation_duration": updated_state.get_duration(),
                "query_complexity_score": 0.85  # Example metric
            })
            
            logger.info("Cypher query generation completed successfully")
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in Cypher generation: {str(e)}", exc_info=True)
            raise

    async def query_execution(self, state: PipelineState) -> PipelineState:
        """Execute query with advanced result processing and progress tracking"""
        logger.info("Starting query execution")
        progress = self._create_progress_bar("Query Execution")
        
        try:
            # Prepare query parameters
            params = {
                "document_types": state.query_context.search_scope,
                "threshold": state.query_context.relevance_threshold,
                "max_results": state.query_context.max_results
            }
            
            progress.update(30)
            
            # Execute query with Neo4j client
            results = self.neo4j_client.execute_query(
                query=state.cypher_query,
                parameters=params
            )
            
            progress.update(60)
            
            # Process results into structured format
            processed_results = [
                QueryResult(
                    node_id=str(r.get("id")),
                    content=r.get("properties", {}),
                    relevance_score=r.get("score", 1.0),
                    metadata=r.get("metadata") if state.query_context.include_metadata else None,
                    relationships=[{
                        "type": rel.get("type"),
                        "target": rel.get("end_node"),
                        "properties": rel.get("properties", {})
                    } for rel in r.get("relationships", [])]
                )
                for r in results
            ]
            
            progress.update(100)
            progress.close()
            
            updated_state = state.model_copy(
                update={
                    "results": processed_results,
                    "performance_metrics": state.performance_metrics | {
                        "execution_time": state.get_duration(),
                        "result_count": len(processed_results)
                    }
                }
            )
            
            logger.info(f"Query execution completed with {len(processed_results)} results")
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in query execution: {str(e)}", exc_info=True)
            raise