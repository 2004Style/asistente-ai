# Architecture Reference

`rbot` is a modular, platform-agnostic AI assistant daemon designed for desktop automation.

## Core Design

```
+-------------------------------------------------------------+
|                         FastAPI Daemon                      |
|                 (REST API / WebSocket HUD Server)           |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                         Bootstrap                           |
|       (Initializes Loader, Schema, EventBus, Container)     |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                      Dependency Container                   |
|  - llm_provider        - platform_adapter    - scheduler    |
|  - memory_manager      - tool_registry       - task_queue   |
+-------------------------------------------------------------+
```

## Safety Sandbox

All terminal commands are executed via a `CommandSandbox` that validates actions against a `SecurityPolicy` and cleans environmental variables to prevent traversal exploits.
