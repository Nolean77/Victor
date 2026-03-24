"""
aOS - Agentic Operating System
3-Node Local AI Fabric

Project Structure:
- core/          : Cluster management, orchestration, resource monitoring
- memory/        : Mem0 knowledge graph, context management
- self_correction: MASC unsupervised failure detection
- plugins/       : Runtime skill acquisition
- security/      : Sandbox execution isolation
- consolidation/ : Nightly LoRA/DPO self-improvement
- android/       : Edge node ADB control
- config/        : Pydantic configuration models
- scripts/       : Setup and cron automation

Tech Stack:
- Inference: Exo (tensor-parallel cluster) + Ollama (fallback)
- LLM Gateway: LiteLLM (unified OpenAI-compatible endpoint)
- Mesh Network: Tailscale (node discovery + secure tunnel)
- Message Bus: Redis Streams + Redis Pub/Sub
- Edge Telemetry: MQTT via Mosquitto
- Memory: Mem0 (graph-based, cross-session decision traces)
- Packaging: uv (Python env management)
- Linting: Ruff
- Testing: pytest + pytest-asyncio
- Containers: Docker Compose v2
- Fine-tuning: LoRA via unsloth
- ADB bridge: pure-python-adb
"""

__version__ = "0.1.0"