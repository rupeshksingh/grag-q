# Tender Document Retrieval Pipeline

A robust and scalable pipeline for querying and analyzing tender documents using Neo4j graph database, LangGraph, and LLM-powered analysis.

## Features

- 🚀 High-performance Neo4j query execution with connection pooling

- 🤖 LLM-powered query analysis and enhancement using Claude and GPT-4

- 📊 Advanced progress tracking and performance monitoring

- 🔄 Robust error handling and retry mechanisms

- 📝 Comprehensive logging system

- ✨ Type-safe data models using Pydantic

- 🧪 Automated testing setup

## Architecture

The pipeline consists of several key components:

1\. **Query Analysis**: Analyzes user queries using LLMs to understand intent and requirements

2\. **Query Enhancement**: Enriches queries with additional context and constraints

3\. **Cypher Generation**: Generates optimized Cypher queries for Neo4j

4\. **Query Execution**: Executes queries with connection pooling and retry logic

5\. **Result Processing**: Processes and formats results with relevance scoring

## Installation

### Prerequisites

- Python 3.9+

- Neo4j 5.x+

- API keys for Anthropic Claude and OpenAI GPT-4

### Setup

1\. Clone the repository:

```bash

git clone https://github.com/yourusername/tender-retrieval-pipeline.git

cd tender-retrieval-pipeline

```

2\. Create and activate a virtual environment:

```bash

python -m venv venv

source venv/bin/activate  # On Windows: venv\Scripts\activate

```

3\. Install dependencies:

```bash

pip install -r requirements.txt

```

4\. Copy the environment template and fill in your credentials:

```bash

cp .env.example .env

```

5\. Configure your environment variables in `.env`:

```plaintext

NEO4J_URI=neo4j://localhost:7687

NEO4J_USERNAME=neo4j

NEO4J_PASSWORD=your_password

ANTHROPIC_API_KEY=your_anthropic_key

OPENAI_API_KEY=your_openai_key

```

## Usage

### Basic Usage

```python

from src.pipeline.graph import TenderPipelineGraph

from src.models.schema import QueryContext

# Initialize the pipeline

pipeline = TenderPipelineGraph()

# Create a query context (optional)

context = QueryContext(

    search_scope=["Technical", "Requirements"],

    relevance_threshold=0.8,

    max_results=50,

    include_metadata=True

)

# Run the pipeline

query = "What are the network infrastructure requirements with redundancy specifications?"

results = await pipeline.run_pipeline(query=query, context=context)

# Access results

for result in results.get('results', []):

    print(f"Document ID: {result.node_id}")

    print(f"Content: {result.content}")

    print(f"Relevance Score: {result.relevance_score}")

```

### Advanced Configuration

You can customize various aspects of the pipeline through the settings in `src/config/settings.py`:

```python

# Pipeline Settings

DEFAULT_SEARCH_SCOPE=["Technical", "Requirements"]

DEFAULT_RELEVANCE_THRESHOLD=0.7

DEFAULT_MAX_RESULTS=100

DEFAULT_INCLUDE_METADATA=True

# Retry Settings

MAX_RETRIES=3

RETRY_DELAY=1.0

# Logging Settings

LOG_LEVEL="INFO"

LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"

```

## Project Structure

```

tender-retrieval-pipeline/

├── src/

│   ├── config/          # Configuration settings

│   ├── database/        # Neo4j client and database utilities

│   ├── logging/         # Logging configuration

│   ├── models/          # Pydantic data models

│   └── pipeline/        # Core pipeline components

├── tests/               # Test suite

├── .env.example         # Environment template

├── requirements.txt     # Project dependencies

└── README.md           # This file

```

## Testing

Run the test suite:

```bash

pytest tests/

```

Run tests with coverage:

```bash

pytest --cov=src tests/

```

## Logging

Logs are written to both console and file (if configured). The default log file is `tender_pipeline.log`. You can customize logging behavior in `src/config/settings.py`.

Example log output:

```

2025-01-21 10:15:30,123 - tender_pipeline - INFO - Starting pipeline execution for query: network requirements

2025-01-21 10:15:31,234 - neo4j_client - INFO - Successfully connected to Neo4j database

2025-01-21 10:15:32,345 - pipeline_nodes - INFO - Query analysis completed successfully

```

## Performance Monitoring

The pipeline includes comprehensive performance monitoring:

- Query execution time

- LLM response latency

- Database connection metrics

- Memory usage

- Result processing time

Access metrics through the pipeline state:

```python

results = await pipeline.run_pipeline(query)

performance_metrics = results.get('performance_metrics')

```

## Error Handling

The pipeline includes robust error handling with:

- Automatic retries for transient failures

- Exponential backoff

- Detailed error logging

- Graceful degradation

- State preservation during failures

## Contributing

1\. Fork the repository

2\. Create a feature branch: `git checkout -b feature-name`

3\. Commit your changes: `git commit -am 'Add feature'`

4\. Push to the branch: `git push origin feature-name`

5\. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.