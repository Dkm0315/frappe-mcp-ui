# 🧠 Intelligent Intent Layer for Frappe MCP + OpenClaw

## Complete System Overview (Updated with Vectorless Architecture)

---

## 1. System Definition

The Intelligent Intent Layer is a **runtime-adaptive cognitive system** that transforms a Frappe-based ERP from a **UI-driven system** into an **intent-driven system**.

It enables users to interact with ERP using natural language while ensuring:

* strict workflow compliance
* permission enforcement
* adherence to business constraints
* resilience to schema inconsistencies

The system is **self-discovering** and **schema-agnostic**, meaning it dynamically understands any Frappe instance it is installed on without prior configuration.

---

## 2. Core Objective

The system eliminates the need for:

* user training
* UI navigation
* schema awareness

and replaces it with:

> intent → understanding → validated execution

It must function correctly even when:

* schema is poorly structured
* naming is inconsistent
* workflows are complex
* user input is ambiguous

---

## 3. System Philosophy

---

### 3.1 Discover, Don’t Configure

All understanding is derived dynamically from:

* schema introspection
* metadata extraction
* real data sampling

No manual mappings are required.

---

### 3.2 Hybrid Intelligence (Vector + Vectorless)

The system is built on two complementary reasoning models:

#### Vector-based reasoning

Used for:

* semantic similarity
* fuzzy matching
* alias detection
* intent interpretation

#### Vectorless reasoning (Deterministic Core)

Used for:

* schema truth
* workflow enforcement
* permission validation
* execution planning

> Vector finds possibilities
> Vectorless decides reality

---

### 3.3 Separation of Concerns

The system strictly separates:

* interpretation (intent + context)
* reasoning (semantic + vectorless logic)
* validation (constraints)
* execution (tools)

---

### 3.4 Constraint-First Execution

No action is executed unless:

* permissions are verified
* workflows are valid
* required fields are satisfied

---

## 4. High-Level Flow

```
User Input
   ↓
Intent Layer (Vector)
   ↓
Context Layer (Hybrid)
   ↓
Semantic Engine (Hybrid)
   ↓
Deterministic Reasoning Layer (Vectorless)
   ↓
Constraint Engine (Vectorless)
   ↓
Execution Planner (Hybrid)
   ↓
MCP Tool Layer (Vectorless)
   ↓
OpenClaw Execution
   ↓
Frappe Backend
```

---

## 5. Layered System Breakdown

---

### 5.1 Intent Layer (Vector-heavy)

Converts natural language into structured intent.

Extracts:

* action type
* target entity
* entities and values
* confidence score
* ambiguity

Handles:

* informal input
* incomplete commands
* ambiguous phrasing

Output is probabilistic, not final.

---

### 5.2 Context Layer (Hybrid)

Resolves ambiguity using runtime context.

Uses:

* user role
* session history
* recent documents
* system state

Transforms vague input into actionable meaning.

---

### 5.3 Semantic Engine (Hybrid)

Builds dynamic understanding of the ERP system.

---

#### System Scanner (Vectorless Extraction)

Extracts:

* DocTypes
* fields and types
* relationships
* workflows
* permissions
* installed apps
* sample data

---

#### Semantic Modeling

Builds:

**Schema Map (Vectorless)**
Exact structural representation of ERP.

**Relationship Graph (Vectorless)**
Defines how entities connect.

**Alias Map (Vector-assisted)**
Maps user language to system entities.

**Embeddings (Vector)**
Enable semantic similarity.

---

### 5.4 Deterministic Reasoning Layer (Vectorless Core)

This is the central reasoning engine.

---

#### Responsibilities:

* traverse relationship graph
* resolve entity dependencies
* determine valid execution paths
* eliminate invalid candidates
* enforce logical correctness

---

#### Example:

User intent:
"make payment"

Vector suggests:

* Sales Invoice
* Purchase Invoice

Vectorless reasoning:

* checks user role
* checks recent context
* selects correct entity

---

#### Nature:

* rule-based
* graph-driven
* deterministic

No embeddings are used here.

---

### 5.5 Constraint Engine (Vectorless)

Validates execution feasibility.

Checks:

* permissions
* workflow states
* required fields
* business rules

---

#### Behavior:

If validation fails:

* suggests correction
* requests input
* modifies plan

Never allows invalid execution.

---

### 5.6 Execution Planner (Hybrid)

Transforms intent into executable steps.

---

#### Responsibilities:

* step generation
* dependency resolution
* ordering operations
* adapting to schema

---

#### Example Plan:

1. fetch latest invoice
2. extract outstanding amount
3. create payment entry
4. submit

---

#### Execution Loop:

```
execute → validate → adapt → retry
```

Planner uses:

* vector (initial mapping)
* vectorless (execution logic)

---

### 5.7 Error Recovery Engine (Vectorless)

Ensures resilience.

---

#### Error Types:

* missing data
* permission issues
* validation errors
* unknown failures

---

#### Strategies:

* infer missing values
* request clarification
* retry with correction
* re-plan execution

---

### 5.8 MCP Tool Layer (Vectorless)

Provides deterministic execution functions.

Examples:

* create document
* update document
* fetch records
* validate documents

---

Tools are:

* simple
* predictable
* side-effect controlled

---

### 5.9 OpenClaw Execution

Acts as execution orchestrator.

Handles:

* tool invocation
* execution sequencing
* result returning

Ensures:

* idempotency
* retry safety

---

## 6. Data Architecture

---

### 6.1 MariaDB (Vectorless Foundation)

Stores:

* schema metadata
* workflows
* permissions
* learned mappings
* logs

Acts as:

> source of truth

---

### 6.2 Vector Store

Stores:

* embeddings
* semantic representations

Used for:

* similarity search
* alias resolution

---

### 6.3 Hybrid Data Flow

```
Vector Layer → candidate generation
Vectorless Layer → validation and execution
```

---

## 7. Installation Lifecycle

On installation:

1. scan entire system
2. extract schema and workflows
3. build relationship graph
4. generate embeddings
5. create alias mappings
6. initialize reasoning engine

System becomes ready without manual setup.

---

## 8. Execution Lifecycle

For each request:

1. parse intent
2. resolve context
3. identify entities (vector)
4. validate via graph (vectorless)
5. generate execution plan
6. enforce constraints
7. execute via MCP/OpenClaw
8. validate results
9. recover if needed

---

## 9. Safety and Compliance

System enforces:

* backend permission checks
* workflow correctness
* audit logging

No action bypasses ERP rules.

---

## 10. Performance Expectations

* intent parsing: sub-second
* planning: < 2 seconds
* execution reliability: > 99%

Optimized via:

* selective embedding
* caching
* minimal context loading

---

## 11. Failure Handling Philosophy

The system:

* does not fail immediately
* attempts recovery
* avoids unsafe execution

Failure is treated as:

> a state for reasoning, not termination

---

## 12. System Capability Summary

The system can:

* interpret ambiguous human language
* understand unknown ERP schemas
* map user language to system entities
* enforce workflows and permissions
* execute multi-step operations
* recover from errors dynamically

---

## 13. Final Definition

The Intelligent Intent Layer is:

> a hybrid cognitive system combining vector-based semantic understanding and vectorless deterministic reasoning to safely execute user intent in any ERP system without requiring prior schema knowledge or training.
