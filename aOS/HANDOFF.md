# aOS Hand-off Specification for Downstream Coding Agent

This document provides complete implementation guidance for completing the aOS scaffold.

---

## Implementation Order (Dependency Graph)

```
Phase 1: Infrastructure (No dependencies)
├── config/__init__.py          - Config models (blocking: none)
└── docker-compose.yml          - Services (blocking: none)

Phase 2: Core Modules (Depends on: config)
├── core/cluster_manager.py     - Node discovery/mgmt (blocking: config)
├── core/resource_monitor.py     - Telemetry collection (blocking: config)
├── core/architect_agent.py     - Main orchestrator (blocking: cluster_manager)

Phase 3: Memory & Self-Correction (Depends on: core)
├── memory/mem0_controller.py  - Knowledge graph (blocking: core)
├── memory/context_manager.py   - Context compression (blocking: core)
├── self_correction/masc_engine.py - Failure detection (blocking: memory)

Phase 4: Plugins & Security (Depends on: core)
├── plugins/plugin_manager.py   - Runtime skills (blocking: core)
├── security/sandbox.py         - Tool isolation (blocking: core)

Phase 5: Edge & Consolidation (Depends on: phases 2-4)
├── android/adb_controller.py   - Android control (blocking: security)
├── consolidation/nightly_cycle.py - Self-improvement (blocking: memory)
```

---

## TODO Details by Module

### 1. core/cluster_manager.py

#### TODO: discover_nodes()
- **Inputs**: None
- **Expected Output**: `list[NodeProfile]` - all discovered nodes
- **Logic**:
  1. Parse `tailscale status --json` for peer IPs
  2. GET `/v1/nodes` from Exo API
  3. Merge and deduplicate by node_id
  4. Update `self._nodes` cache
- **Edge Cases**: Tailscale not running → fallback to Exo-only; stale nodes → remove after 5min

#### TODO: get_headroom(node_id: str)
- **Inputs**: `node_id: str`
- **Expected Output**: `dict` with keys: cpu_pct, vram_free_gb, ram_free_gb, thermal_margin_c, battery_pct
- **Logic**:
  1. psutil for CPU/RAM
  2. nvidia-smi for VRAM/thermal
  3. ADB shell for Android
- **Edge Cases**: nvidia-smi fails → CUDA API fallback; ADB fails → return stale cached

#### TODO: route_task(task: dict)
- **Inputs**: `task: dict` with vram_required, priority
- **Expected Output**: `str` - node_id of best node
- **Logic**:
  1. Get headroom for all nodes
  2. Score: `(vram_free*0.4) + (ram_free*0.2) + (thermal_margin*0.2) + (battery_factor*0.2)`
  3. Exclude: thermal_margin<10, battery<20%, insufficient VRAM
- **Edge Cases**: No eligible nodes → return empty string

#### TODO: migrate_task(task_id, from_node, to_node, state)
- **Inputs**: task_id, from_node, to_node, task_state dict
- **Expected Output**: None (side effect: Redis publish)
- **Logic**:
  1. Serialize state to JSON
  2. XADD to `cluster:migrations` stream
- **Edge Cases**: Redis down → raise ConnectionError

---

### 2. core/architect_agent.py

#### TODO: run_loop()
- **Inputs**: None (uses initialized clients)
- **Expected Output**: None (runs forever until stopped)
- **Logic**:
  1. XREAD from `tasks:pending` with block=500ms
  2. For each task: _plan_subtasks() → _dispatch_subtask()
  3. _check_retry_storms()
- **Edge Cases**: Redis disconnect → exponential backoff; LiteLLM timeout → mark failed

#### TODO: _detect_retry_storm(task_id)
- **Inputs**: task_id: str
- **Expected Output**: `bool` - True if retry storm detected
- **Logic**: Get failure count from Redis, compare to `retry_storm_threshold` (default 5)

#### TODO: _trigger_stop_hook(task_id)
- **Inputs**: task_id: str
- **Expected Output**: None
- **Logic**:
  1. XADD to `tasks:review` stream
  2. Log context to Redis
  3. MQTT publish to `alerts/{task_id}`

---

### 3. core/resource_monitor.py

#### TODO: poll_desktop()
- **Inputs**: None
- **Expected Output**: `dict` with cpu_pct, ram_*, vram_*, gpu_util_pct, thermal_c, timestamp

#### TODO: poll_laptop()
- **Inputs**: None
- **Expected Output**: Same as desktop + battery_pct, battery_charging

#### TODO: poll_android()
- **Inputs**: None
- **Expected Output**: battery_pct, battery_temp_c, thermal_status, ram_*, load_avg

#### TODO: publish_telemetry(node_id, metrics)
- **Inputs**: node_id, metrics dict
- **Expected Output**: None
- **Logic**:
  1. SETEX `telemetry:{node_id}` 30 (TTL)
  2. MQTT publish to `telemetry/{node_id}`

---

### 4. memory/mem0_controller.py

#### TODO: store_decision_trace(task_id, action, reasoning, outcome, tags)
- **Inputs**: task_id, action, reasoning, outcome, tags (optional)
- **Expected Output**: trace_id: str
- **Logic**:
  1. Generate UUID
  2. Get embedding from LiteLLM
  3. Mem0.upsert() with metadata

#### TODO: retrieve_context(query, top_k, session_id)
- **Inputs**: query, top_k (default 5), session_id (optional)
- **Expected Output**: `list[dict]` of matching traces

#### TODO: summarize_session(session_id)
- **Inputs**: session_id: str
- **Expected Output**: summary text string
- **Logic**: Retrieve traces → LiteLLM summarize → store back to Mem0

---

### 5. memory/context_manager.py

#### TODO: hibernate(agent_id, message_history)
- **Inputs**: agent_id, message_history list
- **Expected Output**: cache file path string
- **Logic**:
  1. Serialize to JSON
  2. Compress (lz4 or zlib)
  3. Write to `{cache_dir}/{agent_id}_{ts}.ctx`
  4. SET Redis `cache:{agent_id}` with metadata

#### TODO: restore(agent_id)
- **Inputs**: agent_id: str
- **Expected Output**: `list[dict]` message history
- **Logic**: GET cache path from Redis → read → decompress → parse

#### TODO: summarize_and_truncate(history, max_tokens)
- **Inputs**: history list, max_tokens (default 8192)
- **Expected Output**: truncated history with summary
- **Logic**: If over limit → split, summarize older via LiteLLM, merge

---

### 6. self_correction/masc_engine.py

#### TODO: embed_expected(step_description)
- **Inputs**: step_description: str
- **Expected Output**: np.ndarray embedding
- **Logic**: Check Redis cache → LiteLLM embed → cache 1hr TTL

#### TODO: check_step(expected_embedding, actual_output)
- **Inputs**: expected_embedding np.ndarray, actual_output str
- **Expected Output**: (is_valid: bool, distance: float)
- **Logic**: Embed actual → cosine distance → compare to FAILURE_THRESHOLD

#### TODO: auto_correct(task_id, failed_step)
- **Inputs**: task_id, failed_step dict
- **Expected Output**: correction dict with diagnosis/correction/next_step
- **Logic**: Get 3 traces from Mem0 → build LiteLLM prompt → parse response

---

### 7. plugins/plugin_manager.py

#### TODO: acquire_skill(capability_description)
- **Inputs**: capability_description: str
- **Expected Output**: bool - success
- **Logic**: Search PyPI → LiteLLM generate driver → save → syntax check → load → test

#### TODO: load_all()
- **Inputs**: None
- **Expected Output**: `dict[str, Plugin]` - all loaded plugins
- **Logic**: KEYS `plugins:*` → import each → instantiate → return

---

### 8. security/sandbox.py

#### TODO: run_tool(tool_fn, kwargs, risk_level)
- **Inputs**: tool_fn Callable, kwargs dict, risk_level ("low"/"medium"/"high")
- **Expected Output**: ToolResult
- **Logic**:
  - low: direct asyncio execution
  - medium: check Redis allowlist first
  - high: MQTT human confirm → wait → execute

#### TODO: _check_network_allowlist(hostname)
- **Inputs**: hostname: str
- **Expected Output**: bool - allowed
- **Logic**: EXISTS `allowlist:network:{hostname}` → return cached or deny

---

### 9. android/adb_controller.py

#### TODO: connect(ip, port)
- **Inputs**: ip: str, port: int (default 5555)
- **Expected Output**: bool - connected
- **Logic**: 3 retries with exponential backoff (1s,2s,4s) + asyncio.timeout(30)

#### TODO: send_ui_command(command)
- **Inputs**: UICommand
- **Expected Output**: bool - success
- **Logic**: Route to adb shell input command

#### TODO: get_battery_state()
- **Inputs**: None
- **Expected Output**: BatteryState
- **Logic**: adb shell dumpsys battery → parse

#### TODO: send_confirmation_request(task_id, description)
- **Inputs**: task_id, description
- **Expected Output**: bool - confirmed
- **Logic**: Push Android notification → MQTT subscribe confirm/{task_id} → wait 30s

---

### 10. consolidation/nightly_cycle.py

#### TODO: run()
- **Inputs**: None
- **Expected Output**: summary dict
- **Logic**: Run dpo → lora → synthetic in order

#### TODO: dpo_dataset_generation()
- **Inputs**: None
- **Expected Output**: list[DPOExample]
- **Logic**: Query Mem0 24hr traces → filter self-corrected → build pairs → JSONL

#### TODO: lora_consolidation(dpo_dataset)
- **Inputs**: dpo_dataset (optional)
- **Expected Output**: adapter path string
- **Logic**: unsloth load model → configure LoRA → train → save

#### TODO: synthetic_dreaming()
- **Inputs**: None
- **Expected Output**: list[str] queries
- **Logic**: Analyze Mem0 topics → LiteLLM generate → LPUSH Redis

---

## Required Environment Variables

| Module | Variables |
|--------|-----------|
| All | `REDIS_URL`, `LITELLM_BASE_URL` |
| config | `AOS_NODE_*` (node_id, role, ip, etc.) |
| core.cluster_manager | `EXO_API_URL`, `TAILSCALE_SOCKET` |
| core.architect_agent | `LITELLM_MODEL`, `MQTT_BROKER` |
| core.resource_monitor | `MQTT_BROKER` |
| memory.mem0_controller | `MEM0_API_KEY`, `MEM0_ORG_ID` |
| memory.context_manager | `CACHE_DIR` |
| self_correction.masc_engine | `LITELLM_EMBEDDING_MODEL` |
| plugins.plugin_manager | None extra |
| security.sandbox | `MQTT_BROKER`, `HUMAN_CONFIRM_TOPIC` |
| android.adb_controller | `MQTT_BROKER` |
| consolidation.nightly_cycle | `MEM0_API_KEY`, `LORA_OUTPUT_PATH` |

---

## Test Coverage Targets

| Module | Target | Key Test Cases |
|--------|--------|----------------|
| cluster_manager | 80% | node discovery, headroom collection, task routing, migration |
| architect_agent | 80% | task submission, planning, dispatch, retry storm detection |
| resource_monitor | 80% | desktop/laptop/android polling, telemetry publishing |
| mem0_controller | 80% | store/retrieve traces, session summarization |
| context_manager | 80% | hibernate/restore, compression, truncation |
| masc_engine | 80% | embedding, failure detection, auto-correction |
| plugin_manager | 70% | skill acquisition, loading, unloading |
| sandbox | 80% | low/medium/high execution, allowlist, human confirm |
| adb_controller | 70% | connect, UI commands, battery state |
| nightly_cycle | 70% | DPO generation, LoRA training, synthetic dreaming |

---

## Integration Test Plan (3 Dummy Nodes)

### Setup
1. Start Docker services: `docker compose up -d`
2. Mock Tailscale peers via /etc/hosts or fake status JSON
3. Mock Exo API responses
4. Use Redis/MQTT from compose

### Test Scenarios

1. **Node Discovery Test**
   - Verify discover_nodes() returns mock Tailscale + Exo peers
   
2. **Task Routing Test**
   - Submit task → verify routed to highest-scoring node
   - Simulate node overload → verify reroute

3. **Task Migration Test**
   - Start task on node A → migrate to node B → verify state transfer

4. **Retry Storm Test**
   - Simulate 5 consecutive failures → verify stop hook triggered

5. **Memory Test**
   - Store trace → retrieve → verify semantic search works

6. **Context Compression Test**
   - Create long history → hibernate → restore → verify content matches

7. **MASC Detection Test**
   - Inject expected/actual mismatch → verify failure detected

8. **Sandbox Test**
   - low risk: verify direct execution
   - medium risk: verify allowlist rejection
   - high risk: verify MQTT confirmation flow

9. **ADB Connection Test**
   - Mock ADB server → verify connect with retries

10. **Nightly Cycle Test**
    - Mock Mem0 traces → verify DPO generation output
    - (Skip actual LoRA training - too slow for CI)

---

## Cost Note for Downstream Agent

- **Budget**: Strict - use DeepSeek V3 via OpenRouter
- **Strategy**: Prioritize correctness over verbosity
- **Avoid**: Re-reading unchanged files; implement one TODO at a time
- **Focus**: Complete each method fully before moving to next
- **Testing**: Write tests AFTER implementation, not before
