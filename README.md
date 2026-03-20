# clearCites
clearCites is an open-source platform designed to break down the barriers of academia. By treating research papers as nodes in a massive, interconnected web, it allows users to visually navigate the "lineage of ideas." Traditional research tools are built for experts; clearCites is built for transparency.

---

# 🕸️ ScholarGraph

**Mapping the DNA of Human Knowledge.**

ScholarGraph is the core engine of clearCites – an open-source visual discovery tool that turns academic research into an interactive, navigable map. By treating papers as **Nodes** and citations/authors as **Edges**, it provides a transparent look into how science is funded, built, and validated.

## 💡 Why ScholarGraph?

The current academic landscape is siloed and difficult for the public to navigate. ScholarGraph solves this by:

- **Visualizing Relationships** – See how papers "build on" or "validate" each other through a dynamic graph interface.
- **Taxpayer Transparency** – Easily identify research funded by public grants (NIH, NSF, etc.) to see the real-world impact of tax dollars.
- **AI-Driven Discovery** – Use "correlation values" and "keyword relevance" to find the most impactful research in any field.

## 🏛️ The Mission: Democratizing the Ivory Tower

- **Follow the Money** – Tag papers with their funding sources so users can see what their tax dollars produced.
- **The "Validation" Edge** – Use relationship types (`validates`, `builds_on`, `challenges`) to show when research is being checked by others.
- **Plain-English Summaries** – AI converts dense abstracts into 3-sentence summaries for non-scientists.

---

## 📂 Project Structure

```
scholargraph/
├── data_pipeline/          # The "Ingestor"
│   ├── api_clients/        # Connectors for Semantic Scholar & CrossRef
│   ├── parser.py           # Extracts keywords, authors, funding sources
│   └── graph_pusher.py     # Converts papers into Neo4j Nodes/Edges
├── services/
│   ├── graph_api/          # FastAPI logic for traversing the graph
│   └── ai_summarizer/      # LLM logic to evaluate relationship types
├── web/
│   ├── components/
│   │   ├── GraphCanvas.tsx # The React Flow visualization canvas
│   │   └── PaperDetail.tsx # Sidebar showing the Paper Object details
│   └── hooks/              # Custom hooks for graph navigation
├── db/
│   └── schema.cypher       # Neo4j graph schema (Cypher DDL)
├── docker-compose.yml
└── .env.example
```

---

## 🛠️ Tech Stack

| Component      | Choice                      | Reason |
|----------------|-----------------------------|--------|
| Database       | Neo4j                       | Native graph DB – treats relationships as first-class citizens |
| Backend        | Python (FastAPI)            | Async performance + data-science ecosystem |
| Graph Visuals  | React Flow                  | Interactive node/edge canvas with drag & click |
| AI Integration | LangChain + OpenAI          | Generates summaries and evaluates paper relationships |
| APIs           | Semantic Scholar + CrossRef | Paper metadata, citation counts, funding info |

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- An OpenAI API key

### 1. Clone and configure

```bash
git clone https://github.com/Qrytics/clearCites.git
cd clearCites/scholargraph
cp .env.example .env
# Edit .env and set OPENAI_API_KEY (and optionally SEMANTIC_SCHOLAR_API_KEY)
```

### 2. Start all services

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Neo4j Browser | http://localhost:7474 |
| Graph API (Swagger) | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |

### 3. Apply the Neo4j schema

Once Neo4j is running, open the browser at http://localhost:7474 and run the contents of `db/schema.cypher`.

---

## 🧠 Key Features

### Metric-Based Node Scaling
Node size in the graph is scaled by the paper's `impact_score` (0–1), derived by the AI evaluator.

### Keyword Graph Search
`GET /search/by-keyword?keyword=transformer` returns all papers tagged with a matching keyword node.

### The "Pedigree" View
`GET /papers/{doi}/pedigree` returns the full ancestor citation chain – see which 50-year-old paper started a modern breakthrough.

### Author Overlap
`GET /authors/{name}/papers` surfaces all papers from a researcher, enabling cross-lab influence analysis.

### AI Relationship Evaluation
`POST /ai/relationship` takes two abstracts and returns:
```json
{
  "relationship": "builds_on",
  "correlation_value": 0.87
}
```

---

## 🤖 API Reference

Full interactive docs available at **http://localhost:8000/docs** when running locally.

Key endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/papers/{doi}` | Full paper node with authors, keywords, funders |
| `GET`  | `/papers/{doi}/citations` | Papers cited by this paper (up to 3 hops) |
| `GET`  | `/papers/{doi}/cited-by` | Papers that cite this paper |
| `GET`  | `/papers/{doi}/pedigree` | Full citation lineage |
| `GET`  | `/graph?doi=…&depth=…` | Node/edge JSON for the React Flow canvas |
| `GET`  | `/search?q=…` | Full-text search |
| `GET`  | `/search/by-keyword?keyword=…` | Keyword-based discovery |
| `POST` | `/ai/summary` | Generate a plain-English paper summary |
| `POST` | `/ai/relationship` | Evaluate relationship between two abstracts |

---

## 🧪 Running Tests

```bash
pip install -e ".[dev]"
pytest
```

---

## 📝 Neo4j Graph Schema

Core node types:

- `Paper` – `doi`, `title`, `year`, `abstract`, `plain_summary`, `funding_source`, `cited_by_count`, `impact_score`
- `Author` – `name`, `orcid`
- `Keyword` – `text`
- `Funder` – `name`

Core relationship types:

- `(Author)-[:WROTE]->(Paper)`
- `(Paper)-[:CITES]->(Paper)`
- `(Paper)-[:VALIDATES {correlation_value}]->(Paper)`
- `(Paper)-[:BUILDS_ON]->(Paper)`
- `(Paper)-[:CHALLENGES]->(Paper)`
- `(Paper)-[:HAS_KEYWORD]->(Keyword)`
- `(Paper)-[:FUNDED_BY]->(Funder)`

