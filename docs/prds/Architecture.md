# 🏗️ Architecture

## Intelligent Intent Layer for Frappe MCP + OpenClaw

---

## 1. Architectural Objective

The architecture is designed to enable:

* **intent-driven interaction** over ERP systems
* **runtime adaptability** to any Frappe schema
* **safe, constraint-aware execution**
* **separation between probabilistic understanding and deterministic execution**

The system must remain:

* modular
* observable
* debuggable
* extensible

---

## 2. Architectural Principles

---

### 2.1 Layered Cognition Model

The system is divided into layers that represent distinct stages of reasoning:

1. Interpretation (Intent + Context)
2. Understanding (Semantic Modeling)
3. Deterministic Reasoning (Vectorless Core)
4. Validation (Constraints)
5. Execution (Planner + Tools)

Each layer:

* consumes structured input
* produces structured output
* does not bypass adjacent layers

---

### 2.2 Hybrid Reasoning Architecture

The system separates:

#### Vector Layer (Probabilistic)

* semantic similarity
* alias detection
* fuzzy intent resolution

#### Vectorless Layer (Deterministic)

* schema traversal
* workflow validation
* execution correctness

These layers operate sequentially:

```
Vector → Candidate Generation
Vectorless → Validation & Execution
```

---

### 2.3 Planner-Centric Execution

The architecture ensures:

* tools are atomic and deterministic
* planner orchestrates all execution
* no direct LLM-to-tool execution

---

### 2.4 Source of Truth Separation

| Component    | Role                   |
| ------------ | ---------------------- |
| MariaDB      | system truth           |
| Vector Store | semantic understanding |
| Planner      | execution logic        |

---

## 3. High-Level Architecture

```
                ┌──────────────────────────┐
                │        User Input        │
                └────────────┬─────────────┘
                             ↓
                ┌──────────────────────────┐
                │     Intent Engine        │
                │   (Vector Processing)    │
                └────────────┬─────────────┘
                             ↓
                ┌──────────────────────────┐
                │     Context Engine       │
                │   (Session + System)     │
                └────────────┬─────────────┘
                             ↓
                ┌──────────────────────────┐
                │     Semantic Engine      │
                │ (Schema + Embeddings)    │
                └────────────┬─────────────┘
                             ↓
                ┌──────────────────────────┐
                │ Deterministic Reasoning  │
                │     (Vectorless Core)    │
                └────────────┬─────────────┘
                             ↓
                ┌──────────────────────────┐
                │    Constraint Engine     │
                │ (Permissions + Workflow) │
                └────────────┬─────────────┘
                             ↓
                ┌──────────────────────────┐
                │    Execution Planner     │
                │   (Step Orchestration)   │
                └────────────┬─────────────┘
                             ↓
                ┌──────────────────────────┐
                │     MCP Tool Layer       │
                │  (Deterministic APIs)    │
                └────────────┬─────────────┘
                             ↓
                ┌──────────────────────────┐
                │     OpenClaw Executor    │
                └────────────┬─────────────┘
                             ↓
                ┌──────────────────────────┐
                │     Frappe Backend       │
                │   (MariaDB + Logic)      │
                └──────────────────────────┘
```

---

## 4. Component Interaction Flow

---

### 4.1 Request Lifecycle

1. User submits input
2. Intent Engine parses intent
3. Context Engine enriches input
4. Semantic Engine identifies candidates
5. Deterministic Reasoning filters valid paths
6. Constraint Engine validates feasibility
7. Planner generates execution steps
8. MCP tools are invoked via OpenClaw
9. Results are validated
10. Errors trigger recovery loop

---

### 4.2 Data Flow Model

```
Raw Input
   ↓
Structured Intent (JSON)
   ↓
Context-Enriched Intent
   ↓
Semantic Candidates
   ↓
Validated Entities (Graph)
   ↓
Execution Plan
   ↓
Tool Calls
   ↓
Execution Results
```

---

## 5. Internal Subsystems

---

### 5.1 Interpretation Subsystem

Includes:

* Intent Engine
* Context Engine

Purpose:

* convert natural language into structured representation

---

### 5.2 Semantic Subsystem

Includes:

* System Scanner
* Schema Map
* Relationship Graph
* Embedding Index

Purpose:

* understand ERP structure dynamically

---

### 5.3 Deterministic Reasoning Subsystem

Includes:

* graph traversal engine
* dependency resolver
* candidate eliminator

Purpose:

* ensure logical correctness

---

### 5.4 Validation Subsystem

Includes:

* permission validator
* workflow validator
* field validator

Purpose:

* ensure safe execution

---

### 5.5 Execution Subsystem

Includes:

* planner
* MCP tools
* OpenClaw

Purpose:

* execute validated plans

---

### 5.6 Recovery Subsystem

Includes:

* error classifier
* retry logic
* re-planning engine

Purpose:

* ensure resilience

---

## 6. Storage Architecture

---

### 6.1 Primary Storage (MariaDB)

Stores:

* DocType metadata
* workflows
* permissions
* application data
* learned mappings

Acts as:

> deterministic source of truth

---

### 6.2 Vector Storage

Stores:

* embeddings of DocTypes
* field representations
* sample values

Used for:

* semantic similarity
* alias resolution

---

### 6.3 Graph Representation

Stored as:

* adjacency lists or in-memory graph
* derived from schema relationships

Used for:

* traversal
* dependency resolution

---

## 7. Execution Architecture

---

### 7.1 Planner-Driven Execution

All execution flows through:

* plan generation
* step validation
* controlled execution

---

### 7.2 Execution Loop

```
for step in plan:
    execute step
    validate result
    if failure:
        recover
```

---

### 7.3 Idempotency

All operations must be:

* repeatable
* safe to retry
* state-aware

---

## 8. Integration Architecture

---

### 8.1 MCP Integration

* exposes ERP operations as tools
* acts as interface between planner and execution

---

### 8.2 OpenClaw Integration

* executes MCP tool calls
* handles orchestration
* returns structured responses

---

## 9. Scalability Considerations

---

### 9.1 Horizontal Scaling

* multiple ERP instances
* independent semantic models per instance

---

### 9.2 Caching

* schema cache
* embedding cache
* context cache

---

### 9.3 Load Handling

* concurrent requests
* async execution for long workflows

---

## 10. Observability

---

### 10.1 Logging

* intent interpretation
* planning decisions
* tool executions
* errors and recovery

---

### 10.2 Debugging Capability

System must allow:

* tracing execution path
* inspecting intermediate states
* replaying execution

---

## 11. Failure Boundaries

---

### 11.1 Hard Fail Conditions

* permission violation
* critical system errors

---

### 11.2 Soft Fail Conditions

* missing data
* ambiguous input
* recoverable validation errors

---

## 12. Architectural Summary

The system is a **layered, hybrid reasoning architecture** where:

* vector components interpret user intent
* vectorless components enforce correctness
* planner orchestrates execution
* tools perform deterministic operations

The architecture ensures:

* adaptability across ERP systems
* safety in execution
* resilience to failure
* clarity in reasoning and debugging

---

## 13. Final Architectural Definition

> A modular, hybrid cognition architecture combining probabilistic interpretation and deterministic reasoning to enable safe, adaptive, and scalable intent-driven execution over dynamic ERP systems.
