from typing import Dict, Any, Callable
from langgraph.graph import StateGraph, END
from src.models.schema import PipelineState
from src.pipeline.nodes import PipelineNodes
from src.logging.logger import setup_logger
from src.config.settings import get_settings

settings = get_settings()
logger = setup_logger("pipeline_graph")

class TenderPipelineGraph:
    def __init__(self):
        self.nodes = PipelineNodes()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build an enhanced pipeline graph with proper error handling"""
        workflow = StateGraph(PipelineState)
        
        # Add all pipeline nodes
        workflow.add_node("query_analysis", self.nodes.query_analysis)
        workflow.add_node("query_enhancement", self.nodes.query_enhancement)
        workflow.add_node("cypher_generation", self.nodes.cypher_generation)
        workflow.add_node("query_execution", self.nodes.query_execution)
        
        # Define conditional routing functions
        def check_success(state: Dict) -> bool:
            return state.get("error") is None
        
        def handle_error(state: Dict) -> str:
            """Determine appropriate error recovery path"""
            current_node = state.get("current_node")
            retry_count = state.get("retry_count", 0)
            
            if retry_count >= settings.MAX_RETRIES:
                logger.error(f"Max retries exceeded at node: {current_node}")
                return "end"
            
            # Map current node to recovery path
            recovery_paths = {
                "query_analysis": "retry_analysis",
                "query_enhancement": "retry_enhancement",
                "cypher_generation": "retry_cypher",
                "query_execution": "retry_execution"
            }
            
            return recovery_paths.get(current_node, "end")
        
        # Add edges with conditional routing
        workflow.add_conditional_edges(
            "query_analysis",
            check_success,
            {
                True: "query_enhancement",
                False: "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "query_enhancement",
            check_success,
            {
                True: "cypher_generation",
                False: "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "cypher_generation",
            check_success,
            {
                True: "query_execution",
                False: "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "query_execution",
            check_success,
            {
                True: END,
                False: "error_handler"
            }
        )
        
        # Add error handling edges
        workflow.add_conditional_edges(
            "error_handler",
            handle_error,
            {
                "retry_analysis": "query_analysis",
                "retry_enhancement": "query_enhancement",
                "retry_cypher": "cypher_generation",
                "retry_execution": "query_execution",
                "end": END
            }
        )
        
        return workflow.compile()
    
    async def run_pipeline(
        self,
        query: str,
        context: QueryContext = None
    ) -> Dict[str, Any]:
        """Run the pipeline with progress tracking and metrics"""
        logger.info(f"Starting pipeline execution for query: {query}")
        
        try:
            # Initialize state
            initial_state = PipelineState(
                original_query=query,
                query_context=context or QueryContext(),
                current_node="query_analysis",
                retry_count=0
            )
            
            # Execute pipeline
            result = await self.graph.ainvoke(initial_state.model_dump())
            
            # Log completion metrics
            logger.info(
                "Pipeline completed successfully",
                extra={
                    "duration": result.get("performance_metrics", {}).get("total_duration"),
                    "result_count": len(result.get("results", []))
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
            raise