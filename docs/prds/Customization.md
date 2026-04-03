# 🧩 Customization Intelligence Layer

## Intelligent Intent Layer for Frappe MCP + OpenClaw

---

## 1. Objective

The Customization Intelligence Layer enables the system to understand and reason over **all dynamic and custom logic** within a Frappe instance.

It ensures that the system is not limited to:

* standard DocTypes
* static schema

but fully understands:

* custom DocTypes
* custom fields
* controllers
* hooks
* server scripts
* client scripts
* APIs
* UI pages and SPA flows

---

## 2. Problem Definition

Frappe systems are not defined by schema alone.

Critical business logic exists in:

* Python controllers (`doctype.py`)
* hooks (`hooks.py`)
* custom scripts
* whitelisted APIs
* UI flows (desk pages, SPA)

Without understanding these:

* execution becomes incorrect
* workflows are bypassed
* system behavior is misinterpreted

---

## 3. Layer Position in Architecture

```text
Semantic Engine
   ↓
Customization Intelligence Layer
   ↓
Deterministic Reasoning Layer
```

---

## 4. Core Responsibilities

The layer must:

* discover all customizations
* extract behavioral logic
* map execution pathways
* expose structured representations to planner

---

## 5. Component Breakdown

---

## 5.1 Custom DocType Scanner

---

### Responsibility

Detect and register all custom DocTypes.

---

### Extracts

* DocType name
* module
* fields
* relationships

---

### Output

```json
{
  "doctype": "Custom Order",
  "is_custom": true,
  "fields": []
}
```

---

---

## 5.2 Custom Field Analyzer

---

### Responsibility

Understand dynamic and custom fields.

---

### Extracts

* field definitions
* conditional visibility (`depends_on`)
* required constraints

---

### Importance

Custom fields often contain:

* critical business data
* non-standard naming

---

---

## 5.3 Controller Analyzer (Python Layer)

---

### Responsibility

Parse DocType controllers (`*.py`).

---

### Extracts

* overridden methods
* validations
* hooks (`validate`, `on_submit`, etc.)

---

### Example Extraction

```json
{
  "event": "validate",
  "condition": "amount > 50000",
  "action": "require approval"
}
```

---

---

## 5.4 Hooks Analyzer

---

### Responsibility

Parse `hooks.py`.

---

### Extracts

* doc_events
* scheduler events
* overridden methods

---

### Example

```json
{
  "doctype": "Sales Invoice",
  "event": "on_submit",
  "handler": "custom_app.api.handle_invoice"
}
```

---

---

## 5.5 Server Script Analyzer

---

### Responsibility

Parse server scripts stored in DB.

---

### Extracts

* triggers
* validations
* side effects

---

---

## 5.6 Client Script Analyzer

---

### Responsibility

Parse client-side logic.

---

### Extracts

* UI validations
* field dependencies
* dynamic behaviors

---

---

## 5.7 API Surface Mapper

---

### Responsibility

Identify callable backend methods.

---

### Extracts

* whitelisted methods
* endpoints
* input/output patterns

---

### Output

```json
{
  "method": "create_invoice_with_discount",
  "inputs": {},
  "outputs": {}
}
```

---

---

## 5.8 UI / SPA Analyzer

---

### Responsibility

Understand UI-only workflows.

---

### Extracts

* pages
* routes
* multi-step flows

---

### Importance

Some workflows exist only in UI:

* wizards
* dashboards
* composite actions

---

---

## 5.9 Business Rule Extractor

---

### Responsibility

Convert raw code into structured rules.

---

### Output

```json
{
  "rule": "approval_required",
  "condition": "amount > 50000",
  "action": "require_manager"
}
```

---

---

## 6. Data Output of Layer

---

The layer produces:

---

### 6.1 Behavior Graph

```text
Action → Validation → Workflow → API → Result
```

---

---

### 6.2 API Map

* available actions
* preferred execution methods

---

---

### 6.3 Rule Set

* extracted business rules
* validation logic

---

---

## 7. Planner Integration

---

### Decision Priority

```text
IF API exists
   → use API
ELSE IF workflow exists
   → follow workflow
ELSE
   → fallback to CRUD
```

---

---

## 8. Execution Impact

---

### Without Layer

* incorrect execution
* broken workflows
* missed validations

---

---

### With Layer

* correct API usage
* proper workflow handling
* accurate behavior

---

---

## 9. Performance Considerations

---

* scan only on install or change
* cache extracted logic
* incremental updates

---

---

## 10. Limitations

---

* cannot fully understand arbitrary code
* requires heuristic extraction
* may miss edge-case logic

---

---

## 11. Final Definition

> A system layer that extracts, models, and exposes all custom behavioral logic within a Frappe instance, enabling accurate and safe execution beyond static schema understanding.

---

---

# 🔗 Connection Layer (Bot ↔ Intent System ↔ OpenClaw)

## Coding Assistant Implementation PRD

---

## 1. Objective

Define the **integration layer** that connects:

* Bot (Telegram / BotFather)
* Intent Layer API
* OpenClaw execution system

This layer acts as the **communication and orchestration bridge**.

---

## 2. Architecture

```text
User (Telegram)
   ↓
Bot Service
   ↓
Connection Layer API
   ↓
Intent Layer (/run)
   ↓
Planner
   ↓
MCP
   ↓
OpenClaw
   ↓
Frappe
```

---

## 3. Core Responsibilities

The connection layer must:

* receive user messages
* call intent system
* handle responses
* format output for user
* manage session mapping

---

## 4. Components

---

## 4.1 Bot Adapter

---

### Responsibility

Interface with Telegram.

---

### Functions

* receive messages
* send responses

---

---

## 4.2 Request Router

---

### Responsibility

Forward requests to intent system.

---

### Example

```python
response = requests.post("/run", payload)
```

---

---

## 4.3 Response Formatter

---

### Responsibility

Convert system output into user-friendly text.

---

---

## 4.4 Session Manager

---

### Responsibility

Maintain user context.

---

### Stores

* user_id
* session history
* last actions

---

---

## 4.5 Execution Proxy

---

### Responsibility

Handle communication with OpenClaw (if needed directly).

---

---

## 5. API Contract

---

### Request to Intent Layer

```json
{
  "user_id": "",
  "message": ""
}
```

---

---

### Response

```json
{
  "status": "",
  "message": "",
  "data": {}
}
```

---

---

## 6. Flow

---

```text
User Message
   ↓
Bot receives
   ↓
Connection Layer
   ↓
Intent Layer (/run)
   ↓
Execution
   ↓
Response returned
   ↓
Bot replies
```

---

---

## 7. Error Handling

---

* retry failed requests
* return user-friendly errors
* fallback responses

---

---

## 8. Security

---

* authenticate requests
* validate inputs
* prevent injection

---

---

## 9. Performance

---

* async handling
* minimal latency
* batching if needed

---

---

## 10. Extensibility

---

* support multiple platforms (Slack, Web)
* support multiple agents

---

---

## 11. Final Definition

> A lightweight orchestration layer that connects user-facing interfaces with the intelligent intent system and execution engine, ensuring seamless, secure, and efficient communication across all components.
