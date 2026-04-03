# ⚙️ Execution Engine

## Intelligent Intent Layer for Frappe MCP + OpenClaw

---

## 1. Execution Engine Objective

The Execution Engine is responsible for:

* converting validated intent into executable actions
* orchestrating multi-step workflows
* ensuring safe, ordered, and recoverable execution
* interacting with MCP tools via OpenClaw

It acts as the **operational core** of the system.

---

## 2. Core Responsibilities

The execution engine must:

* generate execution plans
* resolve dependencies between steps
* enforce validation before execution
* handle errors and retries
* maintain execution state

---

## 3. Execution Architecture

---

### 3.1 Execution Flow

```text
Validated Intent
   ↓
Plan Generator
   ↓
Execution Plan
   ↓
Step Executor
   ↓
Validation Layer
   ↓
Tool Invocation (MCP)
   ↓
OpenClaw Execution
   ↓
Result Processing
   ↓
Completion / Recovery
```

---

### 3.2 Execution Loop

```text
for each step:
    execute
    validate
    if failure:
        recover
```

---

## 4. Plan Generation

---

### 4.1 Plan Generator

#### Responsibility

Transforms validated intent into a sequence of steps.

---

### Inputs

* structured intent
* resolved context
* schema information
* reasoning output

---

### Outputs

```json
[
  {"step": 1, "action": "fetch_doc", "target": "Sales Invoice"},
  {"step": 2, "action": "create_doc", "target": "Payment Entry"},
  {"step": 3, "action": "submit_doc", "target": "Payment Entry"}
]
```

---

### 4.2 Plan Characteristics

Plans must be:

* ordered
* deterministic
* minimal
* reversible where possible

---

### 4.3 Plan Types

| Type              | Description                |
| ----------------- | -------------------------- |
| CRUD Plan         | simple create/update       |
| Workflow Plan     | includes state transitions |
| Multi-Entity Plan | involves multiple DocTypes |
| Conditional Plan  | depends on runtime state   |

---

## 5. Step Execution

---

### 5.1 Step Executor

#### Responsibility

Executes individual steps in sequence.

---

### Step Structure

```json
{
  "step_id": "1",
  "action": "create_doc",
  "input": {},
  "status": "pending"
}
```

---

### Execution Phases

1. pre-validation
2. execution
3. post-validation

---

---

### 5.2 Pre-Validation

Checks:

* required inputs
* permissions
* workflow readiness

---

### 5.3 Execution

* mapped to MCP tool
* sent to OpenClaw
* executed against Frappe

---

### 5.4 Post-Validation

Checks:

* result correctness
* expected state change
* data integrity

---

## 6. Dependency Resolution

---

### 6.1 Dependency Graph

Each plan is internally represented as:

```text
Step 1 → Step 2 → Step 3
```

---

### 6.2 Dependency Types

| Type              | Example                      |
| ----------------- | ---------------------------- |
| Data Dependency   | need invoice before payment  |
| State Dependency  | must submit before approve   |
| Entity Dependency | need customer before invoice |

---

### 6.3 Resolver Behavior

* ensures correct ordering
* injects missing steps if required

---

## 7. Tool Invocation Layer

---

### 7.1 Tool Mapping

Each step maps to a tool:

| Action     | Tool       |
| ---------- | ---------- |
| create_doc | MCP create |
| get_doc    | MCP fetch  |
| update_doc | MCP update |
| submit_doc | MCP submit |

---

---

### 7.2 Invocation Format

```json
{
  "tool": "create_doc",
  "params": {}
}
```

---

---

### 7.3 OpenClaw Interaction

* receives tool request
* executes
* returns structured response

---

## 8. State Management

---

### 8.1 Execution State

Tracks:

* current step
* completed steps
* failed steps

---

---

### 8.2 Plan State

| State     | Description   |
| --------- | ------------- |
| pending   | not started   |
| running   | in progress   |
| completed | successful    |
| failed    | unrecoverable |

---

---

### 8.3 Step State

| State   | Description |
| ------- | ----------- |
| pending | waiting     |
| success | completed   |
| failed  | error       |

---

## 9. Error Handling

---

### 9.1 Error Detection

Occurs during:

* validation
* execution
* result verification

---

---

### 9.2 Error Classification

| Type             | Description             |
| ---------------- | ----------------------- |
| Missing Data     | required input missing  |
| Permission Error | access denied           |
| Validation Error | business rule violation |
| System Error     | unexpected failure      |

---

---

### 9.3 Recovery Strategies

| Error        | Strategy          |
| ------------ | ----------------- |
| Missing Data | infer or request  |
| Permission   | escalate          |
| Validation   | correct and retry |
| System       | re-plan           |

---

---

### 9.4 Retry Logic

* limited retries per step
* exponential backoff optional
* fallback to re-planning

---

## 10. Re-Planning Mechanism

---

### 10.1 Trigger Conditions

* repeated failure
* invalid assumptions
* changing context

---

### 10.2 Behavior

* regenerate plan
* reuse successful steps
* skip completed actions

---

## 11. Idempotency and Safety

---

### 11.1 Idempotency Rules

* repeated execution must not corrupt data
* operations must detect existing state

---

---

### 11.2 Safety Constraints

* no unsafe writes
* no bypassing validations
* no direct DB manipulation

---

## 12. Performance Considerations

---

### 12.1 Optimization Strategies

* batch operations where possible
* minimize tool calls
* reuse cached data

---

---

### 12.2 Latency Sources

* planning
* tool execution
* validation

---

---

### 12.3 Mitigation

* parallel fetches
* caching
* lightweight validation paths

---

## 13. Observability

---

### 13.1 Logging

Track:

* step execution
* errors
* retries

---

---

### 13.2 Metrics

* execution time
* success rate
* retry count

---

---

### 13.3 Debugging

* replay execution
* inspect steps
* trace failures

---

## 14. Execution Engine Boundaries

---

### Does

* execute validated plans
* enforce order
* handle errors

---

### Does Not

* interpret raw user input
* decide business rules
* bypass constraint engine

---

## 15. Final Execution Engine Definition

> A deterministic, planner-driven execution system that orchestrates multi-step ERP operations through controlled tool invocation, ensuring correctness, safety, and recoverability at every stage.
