# 🧩 Components

## Intelligent Intent Layer for Frappe MCP + OpenClaw

---

## 1. Component Overview

The system is composed of **modular, loosely coupled components**, each responsible for a distinct stage of cognition or execution.

These components are grouped into six subsystems:

1. Interpretation Subsystem
2. Context Subsystem
3. Semantic Subsystem
4. Deterministic Reasoning Subsystem
5. Validation Subsystem
6. Execution Subsystem

Each component:

* has a clearly defined input/output contract
* is independently testable
* does not bypass other layers

---

## 2. Component Interaction Model

All components interact in a **linear but feedback-capable pipeline**:

```
Intent → Context → Semantic → Reasoning → Constraint → Planner → Execution
                                      ↑
                                  Feedback Loop
```

Feedback is triggered when:

* validation fails
* execution errors occur
* ambiguity remains unresolved

---

## 3. Interpretation Subsystem

---

### 3.1 Intent Engine

#### Responsibility

Transforms raw user input into structured intent.

---

#### Inputs

* user message (natural language)

---

#### Outputs

```json
{
  "intent": "action_type",
  "target_candidates": ["DocType1", "DocType2"],
  "entities": {},
  "confidence": 0.0,
  "ambiguity": true/false,
  "missing_fields": []
}
```

---

#### Internal Behavior

* uses LLM for parsing
* applies prompt templates
* extracts entities and action

---

#### Edge Cases

| Scenario             | Handling                   |
| -------------------- | -------------------------- |
| vague input          | mark ambiguity             |
| missing fields       | populate missing_fields    |
| conflicting entities | return multiple candidates |

---

---

### 3.2 Intent Normalizer

#### Responsibility

Standardizes intent output into a consistent schema.

---

#### Functions

* map synonyms to canonical actions
* normalize entity names
* validate structure

---

## 4. Context Subsystem

---

### 4.1 Context Engine

#### Responsibility

Enhances intent using runtime context.

---

#### Inputs

* structured intent
* user identity
* session history
* recent system activity

---

#### Outputs

```json
{
  "resolved_target": "Sales Invoice",
  "resolved_doc": "INV-0001",
  "context_confidence": 0.85
}
```

---

#### Internal Sources

* recent documents
* last actions
* workflow state
* user role

---

---

### 4.2 Session Memory Store

#### Responsibility

Maintains short-term conversational memory.

---

#### Stores

* last referenced documents
* recent operations
* unresolved intents

---

---

## 5. Semantic Subsystem

---

### 5.1 System Scanner

#### Responsibility

Extracts system structure from Frappe.

---

#### Outputs

* DocType list
* field definitions
* relationships
* workflows
* permissions

---

---

### 5.2 Schema Registry

#### Responsibility

Stores structured representation of system schema.

---

#### Data Structure

```json
{
  "doctype": {
    "fields": [],
    "required": [],
    "links": []
  }
}
```

---

---

### 5.3 Relationship Graph

#### Responsibility

Represents entity relationships.

---

#### Structure

* nodes = DocTypes
* edges = relationships

---

#### Usage

* dependency resolution
* traversal logic

---

---

### 5.4 Embedding Engine

#### Responsibility

Generates vector representations.

---

#### Embeds

* DocTypes
* fields
* sample values

---

---

### 5.5 Alias Resolver

#### Responsibility

Maps user language to system entities.

---

#### Input

"user says: bill"

---

#### Output

"Sales Invoice"

---

---

## 6. Deterministic Reasoning Subsystem (Vectorless Core)

---

### 6.1 Reasoning Engine

#### Responsibility

Enforces logical correctness.

---

#### Functions

* eliminate invalid candidates
* resolve entity dependencies
* traverse graph

---

---

### 6.2 Dependency Resolver

#### Responsibility

Determines execution order and requirements.

---

#### Example

Payment requires:

* invoice
* amount

---

---

### 6.3 Candidate Filter

#### Responsibility

Filters semantic candidates using rules.

---

#### Example

Reject:

* DocTypes without required fields
* invalid workflow states

---

---

## 7. Validation Subsystem

---

### 7.1 Constraint Engine

#### Responsibility

Ensures safe execution.

---

#### Validations

* permissions
* workflow transitions
* required fields

---

---

### 7.2 Permission Validator

#### Responsibility

Checks user access.

---

#### Implementation

```python
frappe.has_permission()
```

---

---

### 7.3 Workflow Validator

#### Responsibility

Validates state transitions.

---

---

### 7.4 Field Validator

#### Responsibility

Ensures required fields exist.

---

---

## 8. Execution Subsystem

---

### 8.1 Execution Planner

#### Responsibility

Creates execution plans.

---

#### Output

```json
[
  {"step": 1, "action": "fetch"},
  {"step": 2, "action": "create"},
  {"step": 3, "action": "submit"}
]
```

---

---

### 8.2 Plan Executor

#### Responsibility

Executes steps sequentially.

---

#### Loop

```
execute → validate → retry
```

---

---

### 8.3 Tool Adapter (MCP Layer)

#### Responsibility

Maps plan steps to MCP tools.

---

---

### 8.4 OpenClaw Adapter

#### Responsibility

Handles execution via OpenClaw.

---

---

## 9. Recovery Subsystem

---

### 9.1 Error Classifier

#### Responsibility

Categorizes errors.

---

#### Types

* missing data
* permission
* validation
* unknown

---

---

### 9.2 Recovery Engine

#### Responsibility

Applies recovery strategies.

---

#### Actions

* infer
* ask
* retry
* re-plan

---

---

## 10. Learning Subsystem (Optional Advanced Layer)

---

### 10.1 Mapping Store

Stores:

* alias mappings
* frequent workflows

---

---

### 10.2 Behavior Learner

Learns from:

* successful executions
* user corrections

---

---

## 11. Component Communication Contracts

---

### Input/Output Rules

* all components accept structured input
* no raw text passed beyond intent layer
* outputs must be JSON-like objects

---

### Validation Boundaries

* each component validates its own output
* downstream components assume structured input

---

## 12. Component Summary

The system is composed of:

* interpretation components (intent)
* context components (memory + resolution)
* semantic components (schema + embeddings)
* reasoning components (graph + rules)
* validation components (constraints)
* execution components (planner + tools)
* recovery components (error handling)

---

## 13. Final Component Definition

> A modular, layered component system where probabilistic interpretation feeds into deterministic reasoning and controlled execution, enabling safe and adaptive interaction with complex ERP systems.
