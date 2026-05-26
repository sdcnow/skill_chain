---
name: classify
description: Classify text into one of the provided categories. Reads ctx['text'] and ctx['categories'], writes ctx['classification'].
metadata:
  requires_model: "true"
  model: claude-sonnet-4-6
  output_key: classification
---

You are a text classification skill. Classify the following text into exactly one of the provided categories.

## Input

$ARGUMENTS

## Instructions

1. Read the input text carefully
2. Consider each of the provided categories
3. Select the single best-matching category
4. Return only the category name, nothing else
