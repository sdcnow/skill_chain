---
name: write-file
description: Write content to a file. Uses ctx['output_path'] and ctx['content'], writes ctx['write_status'].
metadata:
  requires_model: "false"
  output_key: write_status
---

Write the provided content to the specified output path. Creates parent directories if needed.

$ARGUMENTS
