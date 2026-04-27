# PawPal+ AI System Diagram

```mermaid
flowchart TD
    subgraph INPUT["Input"]
        U["User - natural language"]
    end

    subgraph UI["Streamlit UI"]
        CHAT["AI Assistant Tab - chat interface"]
        TABS["Existing Tabs - Owner, Tasks, Schedule"]
    end

    subgraph AI["AI Layer"]
        GUARD["Input Validator and Guardrails"]
        AGENT["Claude Agent - Orchestrator"]
        RETRIEVER["RAG Retriever - cosine similarity search"]
        KB[("Pet Care Knowledge Base - docs")]
    end

    subgraph TOOLS["Agent Tools"]
        T1["add_pet"]
        T2["add_task"]
        T3["generate_schedule"]
        T4["list_tasks"]
        T5["search_knowledge"]
    end

    subgraph CORE["PawPal+ Core System"]
        SCHED["Scheduler - greedy priority algorithm"]
        EVAL["Plan Evaluator - quality score"]
        DB[("SQLite Database")]
    end

    subgraph OBS["Logging and Safety"]
        LOG["AI Action Logger"]
    end

    subgraph VERIFY["Human and Testing Verification"]
        HUMAN["Human Review - approve or edit"]
        TEST["Pytest Suite - unit and mocked AI tests"]
    end

    U -->|"types request"| CHAT
    CHAT --> GUARD
    GUARD -->|"sanitized input"| AGENT

    AGENT -->|"tool: search_knowledge"| T5
    T5 --> RETRIEVER
    RETRIEVER -->|"query"| KB
    KB -->|"ranked docs"| RETRIEVER
    RETRIEVER -->|"relevant pet care context"| AGENT

    AGENT -->|"tool calls"| T1
    AGENT -->|"tool calls"| T2
    AGENT -->|"tool calls"| T3
    AGENT -->|"tool calls"| T4
    T1 --> DB
    T2 --> DB
    T4 --> DB
    DB -->|"data"| T4
    T3 --> SCHED
    SCHED --> DB
    DB -->|"tasks"| SCHED
    SCHED --> EVAL
    EVAL -->|"plan quality score"| AGENT

    AGENT -->|"logs every step"| LOG
    AGENT -->|"final response and schedule"| CHAT
    CHAT -->|"displays output"| U

    U -->|"reads result"| HUMAN
    HUMAN -->|"manual edits"| TABS
    TABS --> DB

    TEST -.->|"validates"| AGENT
    TEST -.->|"validates"| RETRIEVER
    TEST -.->|"validates"| SCHED
```

---

## Component Summary

| Component | Role |
|---|---|
| **User** | Provides natural language input (e.g. "Set up a weekly routine for my puppy") |
| **Input Validator / Guardrails** | Sanitizes and rejects unsafe or malformed input before it reaches the agent |
| **Claude Agent** | Orchestrates the entire response — decides which tools to call and in what order |
| **RAG Retriever** | Searches the pet care knowledge base using vector/cosine similarity and returns relevant context |
| **Pet Care Knowledge Base** | Curated documents: feeding guides, vaccination schedules, breed-specific needs |
| **Agent Tools** | Discrete actions the agent can take: add pets, add tasks, generate a schedule, list tasks, search knowledge |
| **Scheduler** | Existing greedy priority algorithm — unchanged, called via the `generate_schedule` tool |
| **Plan Evaluator** | Scores the generated plan (compliant tasks / total tasks × 100%) and feeds the score back to the agent |
| **SQLite Database** | Persistent storage for all users, pets, and tasks |
| **AI Action Logger** | Records every tool call, retrieval query, and agent decision for auditing and debugging |
| **Human Review** | User reads the AI output and can approve, edit, or override via the existing Streamlit tabs |
| **Pytest Suite** | Automated tests covering tools, retriever accuracy, and scheduler correctness (mocked Claude calls) |

## Data Flow Summary

```
User Input
  → Guardrails (validate)
    → Claude Agent (plan)
      → RAG Retriever (retrieve context from knowledge base)
      → Agent Tools (act: add tasks, generate schedule)
        → Scheduler + Evaluator (run algorithm, score plan)
          → Logger (record)
            → Streamlit UI (display)
              → Human Review (verify / edit)
                → Pytest Suite (automated regression checks)
```
