# RETRACE Repository Analysis Isolation & Untrusted Code Execution Policy

## 1. Zero-Execution Invariant

Source code repositories under analysis must be treated as **untrusted data input**. RETRACE must **never execute arbitrary code or build scripts** (such as `npm install`, `setup.py`, `Makefile`, etc.) from the analyzed repository.

## 2. Static Analysis & Git Sandboxing

1. **AST Parsing Only**: Analysis is performed strictly via static AST parsers (`ast.parse` in Python, structural tokenizers in JS/TS/HTML) without loading, executing, or importing target source files into the Python interpreter runtime.
2. **Subprocess Sanitization**: All Git commands (`git diff`, `git log`, `git blame`) are executed via array-tokenized arguments without shell interpolation (`shell=False`).
3. **Environment Scrubbing**: Git subprocesses execute with sanitized environments that do not inherit AWS credentials or master application secrets.
4. **Command Execution Timeouts**: All Git and AST inspection operations enforce strict timeouts (10s per command) to prevent hanging on corrupted or cyclic repository structures.
