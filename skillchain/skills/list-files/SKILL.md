---
name: list-files
description: List files in a directory with optional glob pattern. Reads ctx['directory'] and optional ctx['pattern'], writes ctx['files'].
metadata:
  requires_model: "false"
  output_key: files
---

List all files in the specified directory. If a pattern is provided, filter by glob pattern. Returns a sorted list of filenames.

$ARGUMENTS
