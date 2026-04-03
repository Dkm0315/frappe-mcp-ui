# 🗄️ Data Models

## Intelligent Intent Layer for Frappe MCP + OpenClaw

---

## 1. Data Model Objective

The data model supports:

* dynamic understanding of ERP schema
* hybrid reasoning (vector + vectorless)
* execution planning and tracking
* learning and adaptation over time

It must be:

* schema-agnostic
* extensible
* efficient for lookup and validation
* compatible with Frappe (MariaDB-backed)

---

## 2. Data Model Layers

The system maintains four categories of data:

1. System Metadata Models (ERP structure)
2. Semantic Models (embeddings + aliasing)
3. Execution Models (intent, plan, logs)
4. Learning Models (adaptive mappings)

---

## 3. System Metadata Models (Vectorless Foundation)

---

### 3.1 DocType Registry

Represents all available DocTypes in the ERP.

#### Fields

| Field       | Type    | Description          |
| ----------- | ------- | -------------------- |
| name        | string  | DocType name         |
| module      | string  | Module name          |
| is_custom   | boolean | Custom or standard   |
| description | text    | Optional description |

---

### 3.2 Field Registry

Represents fields for each DocType.

#### Fields

| Field     | Type    | Description           |
| --------- | ------- | --------------------- |
| doctype   | string  | Parent DocType        |
| fieldname | string  | Field identifier      |
| label     | string  | Display label         |
| fieldtype | string  | Data type             |
| required  | boolean | Mandatory field       |
| options   | string  | Link target / options |

---

### 3.3 Relationship Registry

Represents relationships between DocTypes.

#### Fields

| Field          | Type   | Description        |
| -------------- | ------ | ------------------ |
| source_doctype | string | Parent entity      |
| target_doctype | string | Linked entity      |
| relation_type  | string | link / child table |

---

### 3.4 Workflow Registry

Represents workflow definitions.

#### Fields

| Field       | Type   | Description         |
| ----------- | ------ | ------------------- |
| doctype     | string | Target DocType      |
| states      | json   | List of states      |
| transitions | json   | Allowed transitions |

---

### 3.5 Permission Registry

Represents role-based access.

#### Fields

| Field       | Type   | Description     |
| ----------- | ------ | --------------- |
| doctype     | string | Target DocType  |
| role        | string | Role name       |
| permissions | json   | Allowed actions |

---

## 4. Semantic Models (Hybrid Layer)

---

### 4.1 Embedding Store (Vector)

Stores embeddings for semantic similarity.

#### Fields

| Field       | Type   | Description           |
| ----------- | ------ | --------------------- |
| entity_type | string | doctype / field       |
| entity_name | string | Name                  |
| embedding   | vector | Vector representation |

---

### 4.2 Alias Mapping

Maps user language to system entities.

#### Fields

| Field          | Type   | Description        |
| -------------- | ------ | ------------------ |
| alias          | string | User term          |
| mapped_doctype | string | Target DocType     |
| confidence     | float  | Mapping confidence |

---

### 4.3 Sample Data Store

Stores representative data for semantic context.

#### Fields

| Field       | Type   | Description    |
| ----------- | ------ | -------------- |
| doctype     | string | DocType        |
| sample_json | json   | Sample records |

---

## 5. Execution Models

---

### 5.1 Intent Model

Represents parsed user intent.

#### Fields

| Field      | Type    | Description      |
| ---------- | ------- | ---------------- |
| intent_id  | string  | Unique ID        |
| raw_input  | text    | User input       |
| action     | string  | Action type      |
| target     | string  | DocType          |
| entities   | json    | Extracted fields |
| confidence | float   | Confidence score |
| ambiguity  | boolean | Ambiguity flag   |

---

### 5.2 Context Model

Stores contextual resolution.

#### Fields

| Field             | Type   | Description        |
| ----------------- | ------ | ------------------ |
| context_id        | string | Unique ID          |
| user              | string | User ID            |
| recent_docs       | json   | Recent references  |
| resolved_entities | json   | Contextual mapping |

---

### 5.3 Execution Plan Model

Represents multi-step plan.

#### Fields

| Field     | Type   | Description              |
| --------- | ------ | ------------------------ |
| plan_id   | string | Unique ID                |
| intent_id | string | Linked intent            |
| steps     | json   | Ordered steps            |
| status    | string | pending / running / done |

---

### 5.4 Execution Step Model

Represents individual steps.

#### Fields

| Field   | Type   | Description      |
| ------- | ------ | ---------------- |
| step_id | string | Unique ID        |
| plan_id | string | Parent plan      |
| action  | string | Tool action      |
| input   | json   | Step input       |
| output  | json   | Step result      |
| status  | string | success / failed |

---

### 5.5 Execution Log

Tracks all actions.

#### Fields

| Field     | Type     | Description    |
| --------- | -------- | -------------- |
| log_id    | string   | Unique ID      |
| plan_id   | string   | Linked plan    |
| timestamp | datetime | Execution time |
| message   | text     | Log details    |
| status    | string   | info / error   |

---

## 6. Learning Models

---

### 6.1 Alias Learning Store

Stores learned mappings over time.

#### Fields

| Field          | Type   | Description |
| -------------- | ------ | ----------- |
| phrase         | string | User phrase |
| mapped_doctype | string | Target      |
| frequency      | int    | Usage count |

---

### 6.2 Workflow Pattern Store

Stores common execution flows.

#### Fields

| Field      | Type   | Description     |
| ---------- | ------ | --------------- |
| pattern_id | string | Unique ID       |
| sequence   | json   | Step sequence   |
| frequency  | int    | Usage frequency |

---

### 6.3 Error Pattern Store

Stores recurring failures.

#### Fields

| Field      | Type   | Description      |
| ---------- | ------ | ---------------- |
| error_type | string | Type             |
| resolution | text   | Suggested fix    |
| frequency  | int    | Occurrence count |

---

## 7. Graph Representation (Vectorless Core)

---

### Structure

* Nodes: DocTypes
* Edges: Relationships

---

### Storage Options

* in-memory graph
* adjacency list in DB

---

### Usage

* dependency resolution
* traversal
* validation

---

## 8. Data Flow Relationships

---

```text
Intent → Context → Semantic → Plan → Execution → Logs → Learning
```

---

## 9. Data Consistency Rules

---

* schema models updated on migration
* embeddings refreshed periodically
* learning models updated incrementally
* execution logs immutable

---

## 10. Performance Considerations

---

* cache schema registry
* limit embedding size
* store only sample data
* index frequently accessed fields

---

## 11. Extensibility

---

The data model supports:

* new ERP systems
* additional entity types
* advanced learning modules

---

## 12. Final Data Model Definition

> A layered data architecture combining structured ERP metadata, semantic embeddings, execution tracking, and adaptive learning to support hybrid reasoning and safe intent-driven execution.
