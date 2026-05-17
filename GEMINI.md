# Semiconductor Agent with Dual-Track Memory

This project implements a semiconductor production line agent with a multi-tenant isolation architecture and a dual-track memory mechanism (Soft Update & Sleep Update), based on the `SPEC.MD` requirements.

## Architecture

- **Hot Path (Immediate Path):** 
    - Diagnostic agent analyzes equipment data and history.
    - Captures raw interaction logs via a `soft_update_node` in LangGraph.
    - Multi-tenant isolation is achieved through collection-level namespaces in ChromaDB.
- **Sleep Path (Background Path):**
    - Consolidates raw logs into high-value long-term memory using Gemini.
    - Prunes processed logs to maintain high signal-to-noise ratio.

## Files

- `memory.py`: VectorDB wrapper for ChromaDB with multi-tenant support.
- `agent.py`: LangGraph implementation of the diagnostic agent.
- `worker.py`: Background worker for memory consolidation (Sleep Update).
- `main.py`: Demonstration script.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Ensure `.env` contains `GEMINI_API_KEY`.
3. Run the demonstration:
   ```bash
   python main.py
   ```

## Design Principles
- **Decoupling:** Separation of immediate response and long-term knowledge consolidation.
- **Isolation:** Hard isolation between user/section data.
- **Traceability:** All tool calls and interactions are logged as raw events.
