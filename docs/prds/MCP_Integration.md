# 🔧 MCP Integration

## Intelligent Intent Layer for Frappe MCP + OpenClaw

---

## 1. Objective

The MCP Integration layer connects the Intelligent Intent System with Frappe by exposing ERP capabilities as **structured, callable tools**.

It enables:

* controlled execution of ERP operations
* standardized interface between planner and backend
* safe abstraction over Frappe APIs and logic

This layer ensures that:

> all execution is performed through well-defined, deterministic tools

---

## 2. Role of MCP in Architecture

---

### 2.1 Position in System

```text
Execution Planner
      ↓
MCP Tool Layer
      ↓
OpenClaw
      ↓
Frappe Backend
```

---

### 2.2 Responsibility

* expose ERP operations as tools
* validate inputs before execution
* standardize tool invocation
* isolate backend complexity

---

## 3. MCP Design Principles

---

### 3.1 Tool Atomicity

Each tool performs:

* a single operation
* no implicit side effects
* clear input/output

---

### 3.2 Deterministic Behavior

* same input → same output
* no hidden logic

---

### 3.3 Schema Awareness

* tools validate against DocType schema
* reject invalid inputs

---

### 3.4 Security Enforcement

* permission checks inside tools
* no direct DB access

---

## 4. Tool Categories

---

## 4.1 CRUD Tools

---

### create_doc

Creates a new document.

```json
{
  "doctype": "",
  "data": {}
}
```

---

### get_doc

Fetches document by ID.

```json
{
  "doctype": "",
  "name": ""
}
```

---

### update_doc

Updates document fields.

```json
{
  "doctype": "",
  "name": "",
  "data": {}
}
```

---

### delete_doc

Deletes document.

```json
{
  "doctype": "",
  "name": ""
}
```

---

---

## 4.2 Workflow Tools

---

### submit_doc

Submits a document.

```json
{
  "doctype": "",
  "name": ""
}
```

---

### apply_workflow

Applies workflow transition.

```json
{
  "doctype": "",
  "name": "",
  "action": ""
}
```

---

---

## 4.3 Query Tools

---

### search_docs

Search documents.

```json
{
  "doctype": "",
  "filters": {}
}
```

---

### list_docs

List documents with pagination.

```json
{
  "doctype": "",
  "limit": 10
}
```

---

---

## 4.4 Metadata Tools

---

### get_schema

Fetch DocType schema.

```json
{
  "doctype": ""
}
```

---

### list_doctypes

Returns all DocTypes.

```json
{}
```

---

---

## 4.5 Validation Tools

---

### validate_doc

Validates document before creation/update.

```json
{
  "doctype": "",
  "data": {}
}
```

---

---

## 4.6 Utility Tools

---

### get_recent_docs

Returns recent documents for context.

```json
{
  "doctype": "",
  "limit": 5
}
```

---

---

## 5. Tool Interface Contract

---

### Input Format

```json
{
  "tool": "",
  "params": {}
}
```

---

---

### Output Format

```json
{
  "status": "success",
  "data": {},
  "error": null
}
```

---

---

## 6. Tool Execution Flow

---

```text
Planner Step
   ↓
Tool Selection
   ↓
Parameter Validation
   ↓
OpenClaw Execution
   ↓
Frappe API Call
   ↓
Response Returned
```

---

## 7. Input Validation

---

### Checks

* required fields
* field types
* schema validity

---

---

### Failure Handling

* reject invalid input
* return structured error
* no partial execution

---

## 8. Permission Enforcement

---

### Inside Tools

Each tool must:

* verify user permissions
* enforce role-based access

---

---

### Example

```python
frappe.has_permission(doctype, user=user)
```

---

---

## 9. Tool Selection Logic

---

### Planner Responsibility

Planner decides:

* which tool to use
* when to use it
* in what sequence

---

---

### Decision Rules

```text
IF operation = create
   → use create_doc
IF workflow required
   → use submit_doc
IF complex logic exists
   → prefer API method
```

---

---

## 10. Error Handling in Tools

---

### Types

* validation errors
* permission errors
* execution errors

---

---

### Response Format

```json
{
  "status": "error",
  "error": {
    "type": "",
    "message": ""
  }
}
```

---

---

## 11. Idempotency

---

### Requirements

* repeated calls must not corrupt data
* detect duplicate operations
* maintain consistent state

---

---

## 12. Tool Registration

---

### Registration Process

* tools defined in MCP server
* registered with metadata
* exposed to planner

---

---

### Metadata Includes

* tool name
* input schema
* output schema
* permissions required

---

---

## 13. Extensibility

---

### Supports

* custom tools
* app-specific operations
* external integrations

---

---

### Example

Custom tool:

```json
{
  "tool": "create_invoice_with_discount",
  "params": {}
}
```

---

---

## 14. Performance Considerations

---

* minimize number of tool calls
* batch operations where possible
* cache metadata

---

---

## 15. Observability

---

### Track

* tool usage
* success rate
* failure rate
* latency

---

---

## 16. MCP Layer Boundaries

---

### Does

* expose operations
* validate inputs
* enforce permissions

---

### Does Not

* interpret intent
* generate plans
* bypass constraints

---

---

## 17. Final Definition

> A deterministic tool abstraction layer that exposes ERP capabilities as structured operations, enabling safe, controlled, and standardized execution of intent-driven workflows through MCP and OpenClaw.

