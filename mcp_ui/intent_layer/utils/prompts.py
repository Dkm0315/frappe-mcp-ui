"""Prompt templates aligned with the PRDs."""

INTENT_EXTRACTION_PROMPT = """You are an intent parser for a Frappe ERP system.

Extract only this JSON object from the user message:
{
  "action": "",
  "target_candidates": [],
  "entities": {},
  "confidence": 0.0,
  "ambiguity": false,
  "missing_fields": []
}

Allowed actions: create, read, update, delete, submit, cancel, approve, reject, pay, search, list, workflow, unknown.
Do not include any prose. Do not invent fields that are not present in the user message.

User message:
{message}
"""
