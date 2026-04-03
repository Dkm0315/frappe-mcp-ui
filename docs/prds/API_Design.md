# 🔌 API Design

## Intelligent Intent Layer for Frappe MCP + OpenClaw

---

## 1. Objective

The API layer exposes the Intelligent Intent System as a **structured, stateless service interface** that:

* receives user intent
* orchestrates internal processing
* returns execution outcomes
* enables integration with UI, agents, and external systems

The API must be:

* predictable
* versioned
* secure
* observable

---

## 2. API Design Principles

---

### 2.1 Statelessness

* each request contains all required data
* no dependency on server-side session state

---

### 2.2 Layer Exposure

APIs correspond to system stages:

* intent parsing
* planning
* execution

---

### 2.3 Structured Contracts

* all inputs/outputs must follow strict JSON schema
* no free-form responses

---

### 2.4 Deterministic Responses

* same input → same output (given same context)

---

## 3. API Architecture

---

### 3.1 Flow

```text id="ehxy2n"
Client
 ↓
API Gateway
 ↓
Intent Layer
 ↓
Context + Semantic
 ↓
Planner
 ↓
Execution Engine
 ↓
Response
```

---

## 4. Core APIs

---

## 4.1 Intent API

---

### Endpoint

```
POST /intent
```

---

### Purpose

Convert raw input into structured intent.

---

### Request

```json
{
  "user_id": "",
  "message": ""
}
```

---

### Response

```json
{
  "intent": {
    "action": "",
    "target_candidates": [],
    "entities": {},
    "confidence": 0.0,
    "ambiguity": false,
    "missing_fields": []
  }
}
```

---

---

## 4.2 Context API

---

### Endpoint

```
POST /context
```

---

### Purpose

Resolve intent using context.

---

### Request

```json
{
  "intent": {},
  "user_id": ""
}
```

---

### Response

```json
{
  "resolved_target": "",
  "resolved_entities": {},
  "confidence": 0.0
}
```

---

---

## 4.3 Plan API

---

### Endpoint

```
POST /plan
```

---

### Purpose

Generate execution plan.

---

### Request

```json
{
  "intent": {},
  "context": {}
}
```

---

### Response

```json
{
  "plan": [
    {"step": 1, "action": "", "target": "", "input": {}}
  ]
}
```

---

---

## 4.4 Execute API

---

### Endpoint

```
POST /execute
```

---

### Purpose

Execute generated plan.

---

### Request

```json
{
  "plan": []
}
```

---

### Response

```json
{
  "status": "success",
  "results": [],
  "errors": []
}
```

---

---

## 4.5 Full Pipeline API

---

### Endpoint

```
POST /run
```

---

### Purpose

End-to-end execution.

---

### Request

```json
{
  "user_id": "",
  "message": ""
}
```

---

### Response

```json
{
  "intent": {},
  "plan": [],
  "execution": {},
  "status": ""
}
```

---

---

## 4.6 Schema API

---

### Endpoint

```
GET /schema
```

---

### Purpose

Expose system metadata.

---

### Response

```json
{
  "doctypes": [],
  "fields": [],
  "relationships": []
}
```

---

---

## 4.7 Health API

---

### Endpoint

```
GET /health
```

---

### Purpose

System status check.

---

### Response

```json
{
  "status": "ok"
}
```

---

## 5. API Contracts

---

### 5.1 Input Validation

* validate JSON schema
* reject malformed requests
* enforce required fields

---

---

### 5.2 Output Guarantees

* always structured JSON
* consistent field names
* no null ambiguity

---

---

## 6. Error Handling

---

### 6.1 Error Response Format

```json
{
  "error": {
    "type": "",
    "message": "",
    "code": ""
  }
}
```

---

---

### 6.2 HTTP Status Codes

| Code | Meaning           |
| ---- | ----------------- |
| 200  | success           |
| 400  | invalid request   |
| 403  | permission denied |
| 500  | server error      |

---

---

## 7. Authentication & Authorization

---

### 7.1 Authentication

* token-based (API key / session)
* integrated with Frappe auth

---

---

### 7.2 Authorization

* validated via constraint engine
* enforced per request

---

---

## 8. Rate Limiting

---

### Purpose

* prevent abuse
* control system load

---

---

### Strategy

* per-user rate limits
* per-endpoint limits

---

---

## 9. Versioning

---

### Strategy

* version in URL

```
/v1/intent
```

---

---

### Purpose

* backward compatibility
* safe updates

---

---

## 10. Observability

---

### 10.1 Logging

* request payload
* response output
* errors

---

---

### 10.2 Metrics

* latency
* success rate
* error rate

---

---

## 11. Extensibility

---

APIs must support:

* additional endpoints
* new execution types
* integration with external systems

---

---

## 12. API Boundaries

---

### Does

* expose system capabilities
* orchestrate processing
* return structured results

---

### Does Not

* bypass internal layers
* execute unsafe actions
* expose internal logic directly

---

## 13. Final Definition

> A structured, stateless API layer that exposes intent-driven ERP capabilities through well-defined endpoints, enabling safe, scalable, and extensible integration with external clients and systems.
