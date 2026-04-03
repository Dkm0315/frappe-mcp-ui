# 🧠 Prompting Strategy

## Intelligent Intent Layer for Frappe MCP + OpenClaw

---

## 1. Prompting Objective

The prompting system is responsible for:

* converting user input into structured intent
* guiding reasoning across layers
* minimizing hallucination
* ensuring consistent, structured outputs

It must:

* reduce ambiguity
* control LLM behavior
* produce machine-consumable outputs
* remain efficient in token usage

---

## 2. Prompting Architecture

The system uses **multi-stage prompting**, where each stage has a specific role.

---

### 2.1 Prompt Stages

1. Intent Extraction Prompt
2. Context Resolution Prompt
3. Semantic Mapping Prompt
4. Plan Generation Prompt
5. Error Recovery Prompt

Each stage:

* receives structured input
* produces structured output
* does not depend on raw text beyond the first stage

---

## 3. Core Prompting Principles

---

### 3.1 Structured Output Enforcement

All prompts must return:

* strict JSON format
* no free text
* predictable schema

---

### 3.2 Minimal Context Injection

Only pass:

* relevant DocTypes
* top candidate entities
* required fields

Avoid:

* full schema dumps
* unnecessary history

---

### 3.3 Deterministic Framing

Prompts must:

* restrict output space
* define clear instructions
* reduce creativity

---

### 3.4 Single Responsibility Prompts

Each prompt handles one task only:

* no multi-purpose prompts
* no mixing interpretation with execution

---

## 4. Prompt Types and Templates

---

## 4.1 Intent Extraction Prompt

---

### Purpose

Convert raw input into structured intent.

---

### Input

* user message

---

### Template

```
You are an intent parser for an ERP system.

Extract:
- action
- target entity
- relevant fields
- ambiguity level

Return strictly in JSON format:
{
  "action": "",
  "target_candidates": [],
  "entities": {},
  "confidence": 0.0,
  "ambiguity": false,
  "missing_fields": []
}
```

---

### Output Example

```json
{
  "action": "create",
  "target_candidates": ["Sales Invoice"],
  "entities": {"customer": "Tata"},
  "confidence": 0.85,
  "ambiguity": false,
  "missing_fields": ["items"]
}
```

---

## 4.2 Context Resolution Prompt

---

### Purpose

Resolve references using context.

---

### Input

* intent output
* recent documents
* session memory

---

### Template

```
Resolve missing or ambiguous references using context.

Input:
- intent
- recent documents

Return:
{
  "resolved_target": "",
  "resolved_doc": "",
  "confidence": 0.0
}
```

---

---

## 4.3 Semantic Mapping Prompt

---

### Purpose

Map user terms to actual DocTypes and fields.

---

### Input

* candidate DocTypes
* schema snippets
* alias mappings

---

### Template

```
Map user intent to correct DocType and fields.

Given:
- candidates
- schema

Return:
{
  "selected_doctype": "",
  "field_mapping": {},
  "confidence": 0.0
}
```

---

---

## 4.4 Plan Generation Prompt

---

### Purpose

Generate execution plan.

---

### Input

* validated intent
* resolved context
* schema

---

### Template

```
Generate a step-by-step execution plan.

Constraints:
- only valid operations
- minimal steps

Return:
[
  {"step": 1, "action": "", "target": "", "input": {}}
]
```

---

---

## 4.5 Error Recovery Prompt

---

### Purpose

Suggest recovery actions.

---

### Input

* error type
* failed step
* context

---

### Template

```
Given an execution error, suggest a correction.

Return:
{
  "strategy": "",
  "corrected_input": {},
  "retry": true/false
}
```

---

## 5. Prompt Input Construction

---

### 5.1 Context Packing

Include only:

* relevant schema
* top 3–5 candidate DocTypes
* key fields

---

---

### 5.2 Token Optimization

* avoid full database context
* use summarized schema
* reuse cached prompts

---

---

## 6. Prompt Chaining

---

### Flow

```text
Intent → Context → Semantic → Plan → Execution
```

Each step feeds into the next.

---

---

## 7. Guardrails

---

### 7.1 Output Validation

* enforce JSON schema
* reject malformed outputs
* retry prompt if invalid

---

---

### 7.2 Hallucination Control

* limit allowed actions
* validate against schema
* reject unknown entities

---

---

### 7.3 Restricted Actions

LLM cannot:

* directly execute tools
* bypass constraints
* invent fields

---

## 8. Model Usage Strategy

---

### 8.1 Model Allocation

| Task               | Model Type       |
| ------------------ | ---------------- |
| Intent parsing     | high-quality LLM |
| Context resolution | medium           |
| Planning           | high-quality     |
| Validation         | deterministic    |

---

---

### 8.2 Call Optimization

* minimize number of LLM calls
* combine steps where possible
* cache results

---

## 9. Failure Handling in Prompting

---

### 9.1 Retry Strategy

* re-run with stricter instructions
* reduce context
* fallback to safe defaults

---

---

### 9.2 Fallback Mode

* ask user for clarification
* return partial result
* defer execution

---

## 10. Prompt Versioning

---

### Purpose

* track improvements
* enable rollback
* experiment safely

---

---

### Fields

| Field               | Description    |
| ------------------- | -------------- |
| version_id          | unique version |
| prompt_text         | template       |
| performance_metrics | success rate   |

---

---

## 11. Observability

---

### Track:

* prompt success rate
* invalid outputs
* retries
* latency

---

---

## 12. Prompting Boundaries

---

### Does

* interpret
* suggest
* structure

---

### Does Not

* enforce constraints
* execute actions
* guarantee correctness

---

## 13. Final Prompting Strategy Definition

> A controlled, multi-stage prompting system that converts natural language into structured, validated instructions while minimizing ambiguity, hallucination, and unnecessary model usage.
