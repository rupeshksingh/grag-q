from neo4j import GraphDatabase, Session, Transaction
from neo4j.exceptions import ServiceUnavailable, SessionExpired
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
import backoff
from src.config.settings import get_settings
from src.logging.logger import setup_logger

settings = get_settings()
logger = setup_logger("neo4j_client")

class Neo4jClient:
    def __init__(self):
        self._driver = None
        self.connect()
    
    def connect(self) -> None:
        """Establish connection to Neo4j database with retry logic"""
        @backoff.on_exception(
            backoff.expo,
            (ServiceUnavailable, SessionExpired),
            max_tries=settings.MAX_RETRIES
        )
        def _connect():
            self._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
                max_connection_lifetime=300,  # 5 minutes
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )
        
        _connect()
        logger.info("Successfully connected to Neo4j database")
    
    @contextmanager
    def get_session(self) -> Session:
        """Get a Neo4j session with automatic cleanup"""
        if not self._driver:
            self.connect()
        
        session = None
        try:
            session = self._driver.session()
            yield session
        finally:
            if session:
                session.close()
    
    @backoff.on_exception(
        backoff.expo,
        (ServiceUnavailable, SessionExpired),
        max_tries=settings.MAX_RETRIES
    )
    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> List[Dict]:
        """Execute a Cypher query with retry logic"""
        with self.get_session() as session:
            result = session.run(query, parameters, database=database)
            return [record.data() for record in result]
    
    def close(self) -> None:
        """Close the Neo4j driver"""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")