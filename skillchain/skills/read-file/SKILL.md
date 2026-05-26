---
name: read-file
description: Read a file's contents into context. Reads ctx['file_path'], writes ctx['content'].
metadata:
  requires_model: "false"
  output_key: content
---

Read the contents of the file at the specified path and store in ctx['content'].

$ARGUMENTS
