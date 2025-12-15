# HospitalAssistant-AI

## Overview
HospitalAssistant-AI is a Retrieval-Augmented Generation (RAG) agent designed for Hospital Clínico Magallanes. It allows hospital staff and patients to query a SQL database using natural language.

## Architecture
The project follows **Clean Architecture** and **SOLID principles** to ensure modularity and scalability.

### Layers
1.  **Domain (`src/domain`)**: Contains core business entities and repository interfaces. Independent of external libraries.
2.  **Application (`src/application`)**: Implement business use cases and application logic (e.g., RAG orchestration).
3.  **Infrastructure (`src/infrastructure`)**: Implements interfaces defined in the Domain layer. Content generic database adapters and LLM clients (Ollama).
4.  **UI (`src/ui`)**: The presentation layer, built with Streamlit.

### Tech Stack
-   **Language**: Python 3.11+
-   **Frontend**: Streamlit
-   **LLM Integration**: LangChain + Ollama
-   **Database**: SQLite (Dev) / PostgreSQL (Prod) via SQLAlchemy, use hospital.db as database.
-   **Containerization**: Docker

## Setup
### Prerequisites
- Python 3.11+
- Ollama (running locally)

### Installation
1.  Install dependencies:
    ```bash
    pip install -e .[dev]
    ```

2.  Run the application:
    ```bash
    streamlit run src/ui/main.py
    ```

3.  Run tests:
    ```bash
    pytest
    ```
