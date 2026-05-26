---
name: summarize
description: Summarize text concisely using an LLM. Reads ctx['text'], writes ctx['summary'].
metadata:
  requires_model: "true"
  model: claude-sonnet-4-6
  output_key: summary
---

You are a summarization skill. Summarize the following text concisely.

## Input

$ARGUMENTS

## Instructions

1. Identify the main points and key information
2. Produce a concise summary
3. Return only the summary, no preamble or explanation
