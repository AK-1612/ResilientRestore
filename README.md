# ResilientRestore

> **Enterprise-Grade Transactional State Checkpoint and Automated Rollback Sidecar for AI Agent Tool Execution.**

---

## Overview

As autonomous AI agents execute complex, multi-step workflows involving file modifications, database operations, and system tool calls, unexpected errors, flawed logic, or runtime failures can lead to system corruption and data loss. Mitigating these failures and ensuring robust remediation is a core pillar of enterprise AI resilience.

**ResilientRestore** acts as an inline transactional wrapper and checkpoint manager for AI agent tool executions. It automatically captures state snapshots (such as file diffs and database records) *before* a tool runs, providing instant transactional isolation, automated rollbacks, and self-healing error recovery loops if an execution fails.

---

## Key Features

* **Pre-Execution Snapshot Engine**: Automatically computes diffs and captures compressed snapshots of target resources (files, tables) prior to tool invocation.
* **Transactional Isolation (ACID for Agents)**: Wraps multi-step agent plans in transaction blocks, enabling automated or 1-click state reversion if downstream steps fail.
* **Self-Healing Error Feedback Loop**: Captures execution stack traces and error telemetry, feeding them back to the orchestration layer to allow safe, sandboxed self-correction.
* **Immutable Audit & Rollback Log**: Maintains a detailed timeline of state modifications for security and compliance auditing.
* **Strict Schema Validation**: Powered by Pydantic v2 with strict mode validation to prevent malformed transaction payloads.

---

## Architecture & Flow

```
                      +-----------------------------+
                      |   Agent Orchestrator Plan   |
                      +--------------+--------------+
                                     |
                                     v
                 +---------------------------------------+
                 |       ResilientRestore Sidecar        |
                 |                                       |
                 |  [1] Pre-Execution State Snapshot     |
                 |      (Capture file/db diffs)          |
                 |                                       |
                 |  [2] Transactional Tool Execution     |
                 |      (Execute tool in sandbox block)  |
                 +-------------------+-------------------+
                                     |
                    +----------------+----------------+
                    |                                 |
              [Execution OK]                   [Execution Error]
                    |                                 |
                    v                                 v
          +-------------------+             +-------------------+
          |  Commit Changes   |             | Automatic Rollback|
          |  State Finalized  |             | Restore Snapshot  |
          +-------------------+             +-------------------+

```

---

## Installation & Setup

### 1. Prerequisites

* Python 3.10+
* Git

### 2. Clone Repository

```bash
git clone https://github.com/AK-1612/ResilientRestore.git
cd ResilientRestore

```

### 3. Create & Activate Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate

```

### 4. Install Dependencies

```bash
pip install -r requirements.txt

```

---

## Core Components

* `checkpoint.py`: Manages state snapshots, file diff computations, and rollback states.
* `middleware.py`: Intercepts tool execution requests to wrap them in transactional boundaries.
* `schemas.py`: Pydantic v2 models defining transaction requests, states, and rollbacks.
* `server.py`: FastAPI application exposing transactional tool execution endpoints.
* `test_restore.py`: Pytest suite validating snapshot creation, failure handling, and state rollbacks.

---

## License

This project is licensed under the [MIT License](https://www.google.com/search?q=LICENSE).