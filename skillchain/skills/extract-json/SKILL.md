---
name: extract-json
description: Extract structured JSON from unstructured text. Reads ctx['text'] and optional ctx['schema'], writes ctx['extracted'].
metadata:
  requires_model: "true"
  model: claude-sonnet-4-6
  output_key: extracted
---

You are a JSON extraction skill. Extract structured data as valid JSON from the following text.

## Input

$ARGUMENTS

## Instructions

1. Analyze the input text for structured information
2. Extract data into a JSON format
3. If a target schema is provided, match that schema
4. Return only valid JSON, no markdown fences or explanation
