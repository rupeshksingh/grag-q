from typing import Dict, List, Any, Optional, Union
import json
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np
from collections import defaultdict
import hashlib
import pickle
from contextlib import contextmanager
import time
import asyncio
from src.logging.logger import setup_logger
from src.models.schema import QueryResult, PipelineState
from src.config.settings import get_settings

settings = get_settings()
logger = setup_logger("pipeline_utils")

class PipelineUtils:
    @staticmethod
    def save_results(
        results: List[QueryResult],
        output_path: Union[str, Path],
        format: str = "json"
    ) -> Path:
        """
        Save pipeline results to file in specified format
        
        Args:
            results: List of QueryResult objects
            output_path: Path to save results
            format: Output format ('json' or 'pickle')
            
        Returns:
            Path object of saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if format == "json":
                output_path = output_path.with_suffix('.json')
                with output_path.open('w', encoding='utf-8') as f:
                    json.dump(
                        [r.model_dump() for r in results],
                        f,
                        indent=2,
                        default=str
                    )
            elif format == "pickle":
                output_path = output_path.with_suffix('.pkl')
                with output_path.open('wb') as f:
                    pickle.dump(results, f)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Results saved to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def load_results(
        input_path: Union[str, Path],
        format: Optional[str] = None
    ) -> List[QueryResult]:
        """
        Load saved results from file
        
        Args:
            input_path: Path to load results from
            format: File format (if None, inferred from extension)
            
        Returns:
            List of QueryResult objects
        """
        input_path = Path(input_path)
        if not format:
            format = input_path.suffix.lstrip('.')
        
        try:
            if format == "json":
                with input_path.open('r', encoding='utf-8') as f:
                    data = json.load(f)
                return [QueryResult.model_validate(r) for r in data]
            elif format == "pkl":
                with input_path.open('rb') as f:
                    return pickle.load(f)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Error loading results: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def analyze_results(results: List[QueryResult]) -> Dict[str, Any]:
        """
        Perform statistical analysis on query results
        
        Args:
            results: List of QueryResult objects
            
        Returns:
            Dictionary containing analysis metrics
        """
        try:
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame([r.model_dump() for r in results])
            
            analysis = {
                "total_results": len(results),
                "avg_relevance": float(df["relevance_score"].mean()),
                "min_relevance": float(df["relevance_score"].min()),
                "max_relevance": float(df["relevance_score"].max()),
                "relevance_std": float(df["relevance_score"].std()),
                "relationship_stats": {
                    "avg_relationships": float(df["relationships"].apply(len).mean()),
                    "max_relationships": int(df["relationships"].apply(len).max())
                },
                "timestamp_range": {
                    "start": df["timestamp"].min(),
                    "end": df["timestamp"].max()
                }
            }
            
            # Analyze relationship types
            all_rel_types = [
                rel["type"]
                for result in results
                for rel in result.relationships
            ]
            relationship_counts = defaultdict(int)
            for rel_type in all_rel_types:
                relationship_counts[rel_type] += 1
            
            analysis["relationship_distribution"] = dict(relationship_counts)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing results: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def cache_key(query: str, context: Dict[str, Any]) -> str:
        """
        Generate cache key for query and context
        
        Args:
            query: Original query string
            context: Query context dictionary
            
        Returns:
            Cache key string
        """
        # Create canonical representation of input
        canonical = {
            "query": query,
            "context": context
        }
        
        # Generate hash
        return hashlib.sha256(
            json.dumps(canonical, sort_keys=True).encode()
        ).hexdigest()

    @staticmethod
    async def cache_results(
        cache_dir: Union[str, Path],
        key: str,
        results: List[QueryResult]
    ) -> None:
        """
        Cache query results asynchronously
        
        Args:
            cache_dir: Directory to store cache
            key: Cache key
            results: Query results to cache
        """
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / f"{key}.pkl"
        
        try:
            # Use asyncio to write cache file without blocking
            await asyncio.to_thread(
                lambda: cache_path.write_bytes(pickle.dumps(results))
            )
            logger.debug(f"Results cached to {cache_path}")
            
        except Exception as e:
            logger.error(f"Error caching results: {str(e)}", exc_info=True)
            # Don't raise - caching errors shouldn't break the pipeline

    @staticmethod
    async def get_cached_results(
        cache_dir: Union[str, Path],
        key: str
    ) -> Optional[List[QueryResult]]:
        """
        Retrieve cached results if available
        
        Args:
            cache_dir: Cache directory
            key: Cache key
            
        Returns:
            Cached results if found, None otherwise
        """
        cache_path = Path(cache_dir) / f"{key}.pkl"
        
        try:
            if cache_path.exists():
                # Load cache file asynchronously
                data = await asyncio.to_thread(
                    lambda: pickle.loads(cache_path.read_bytes())
                )
                logger.debug(f"Retrieved cached results for key {key}")
                return data
            return None
            
        except Exception as e:
            logger.error(f"Error loading cached results: {str(e)}", exc_info=True)
            return None

    @staticmethod
    @contextmanager
    def timer(name: str) -> None:
        """
        Context manager for timing code blocks
        
        Args:
            name: Name of the timed operation
            
        Yields:
            None
        """
        start = time.perf_counter()
        yield
        duration = time.perf_counter() - start
        logger.debug(f"{name} took {duration:.2f} seconds")

    @staticmethod
    def get_performance_summary(state: PipelineState) -> Dict[str, Any]:
        """
        Generate performance summary from pipeline state
        
        Args:
            state: Pipeline state object
            
        Returns:
            Dictionary of performance metrics
        """
        metrics = state.performance_metrics
        
        return {
            "total_duration": state.get_duration(),
            "average_node_duration": np.mean([
                v for k, v in metrics.items()
                if k.endswith('_duration')
            ]),
            "slowest_node": max(
                [(k, v) for k, v in metrics.items()
                 if k.endswith('_duration')],
                key=lambda x: x[1]
            )[0],
            "results_count": len(state.results or []),
            "retry_count": state.retry_count,
            "error_count": sum(
                1 for h in state.history
                if isinstance(h, dict) and h.get("error")
            )
        }

    @staticmethod
    def export_metrics(
        metrics: Dict[str, Any],
        output_path: Union[str, Path],
        format: str = "json"
    ) -> None:
        """
        Export performance metrics to file
        
        Args:
            metrics: Dictionary of metrics
            output_path: Output file path
            format: Output format ('json' or 'csv')
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if format == "json":
                output_path = output_path.with_suffix('.json')
                with output_path.open('w', encoding='utf-8') as f:
                    json.dump(metrics, f, indent=2, default=str)
            
            elif format == "csv":
                output_path = output_path.with_suffix('.csv')
                # Flatten nested dictionary
                flat_metrics = {}
                for k, v in metrics.items():
                    if isinstance(v, dict):
                        for sub_k, sub_v in v.items():
                            flat_metrics[f"{k}_{sub_k}"] = sub_v
                    else:
                        flat_metrics[k] = v
                
                pd.DataFrame([flat_metrics]).to_csv(
                    output_path,
                    index=False
                )
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Metrics exported to {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting metrics: {str(e)}", exc_info=True)
            raise