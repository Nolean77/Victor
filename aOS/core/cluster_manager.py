"""
Core cluster management module.

Manages the Exo cluster lifecycle, node health monitoring, and task routing
across the 3-node mesh network (desktop, laptop, android).

Classes:
- NodeProfile: Pydantic model for node metadata
- ClusterManager: Async manager for cluster operations

Dependencies:
- Tailscale: Node discovery via peer list
- Exo: Cluster management via /v1/nodes endpoint
- Redis Streams: Task migration channel

TODO Implementation Order:
1. discover_nodes() - ping Tailscale peers, query Exo
2. get_headroom() - collect resource metrics per node
3. route_task() - score-based task routing
4. migrate_task() - serialize state, publish to Redis
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class NodeRole(str, Enum):
    """Role of a node in the cluster."""

    DESKTOP = "desktop"
    LAPTOP = "laptop"
    ANDROID = "android"


class NodeProfile(BaseModel):
    """
    Profile of a single node in the cluster.

    Attributes:
        node_id: Unique identifier (e.g., "desktop-0", "laptop-0")
        role: Node role (desktop/laptop/android)
        vram_gb: Available GPU VRAM in gigabytes
        ram_gb: Available system RAM in gigabytes
        gpu_name: GPU model string (e.g., "RTX 4090")
        thermal_limit_c: Maximum allowable temperature in Celsius
        battery_pct: Battery percentage (None for desktop)
        ip: Local mesh IP address
        tailscale_ip: Tailscale VPN IP address
        last_seen: Timestamp of last health check
    """

    node_id: str
    role: NodeRole
    vram_gb: float
    ram_gb: float
    gpu_name: str
    thermal_limit_c: float = 85.0
    battery_pct: float | None = None
    ip: str
    tailscale_ip: str | None = None
    last_seen: datetime | None = None


class TaskState(BaseModel):
    """State of a task being migrated between nodes."""

    task_id: str
    from_node: str
    to_node: str
    payload: dict[str, Any]
    created_at: datetime


class ClusterManager:
    """
    Manages the Exo cluster lifecycle and node health.

    Public API:
        discover_nodes() -> list[NodeProfile]
        get_headroom(node_id: str) -> dict
        route_task(task: Task) -> str
        migrate_task(task_id: str, from_node: str, to_node: str) -> None

    Internal Methods:
        _query_tailscale_peers() -> list[str]
        _query_exo_nodes() -> list[dict]
        _calculate_node_score(profile: NodeProfile, headroom: dict) -> float

    Dependencies:
        - Redis: For task migration streams
        - Tailscale CLI: For peer discovery
        - Exo API: For cluster state

    Environment Variables:
        REDIS_URL: Redis connection string
        EXO_API_URL: Exo cluster API endpoint
        TAILSCALE_SOCKET: Path to Tailscale socket (optional)
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        exo_api_url: str = "http://localhost:8080",
    ):
        """
        Initialize the cluster manager.

        Args:
            redis_url: Redis connection URL for task migration
            exo_api_url: Exo cluster API URL
        """
        self._redis_url = redis_url
        self._exo_api_url = exo_api_url
        self._redis_client: Any = None
        self._nodes: dict[str, NodeProfile] = {}
        self._lock = asyncio.Lock()

    async def _ensure_redis(self) -> Any:
        """Lazily initialize Redis client."""
        # TODO: Import redis.asyncio and create connection
        # import redis.asyncio as redis
        # if self._redis_client is None:
        #     self._redis_client = redis.from_url(self._redis_url)
        pass

    async def discover_nodes(self) -> list[NodeProfile]:
        """
        Discover all nodes in the cluster via Tailscale and Exo.

        TODO Implementation:
        1. Query Tailscale peers via `tailscale status --json` or socket
        2. Query Exo /v1/nodes endpoint for registered workers
        3. Merge results, deduplicate by node_id
        4. Update self._nodes cache with fresh profiles

        Returns:
            List of discovered NodeProfile objects

        Edge Cases:
        - Tailscale daemon not running: fallback to Exo-only discovery
        - Node appears in Tailscale but not Exo: mark as "unconfirmed"
        - Stale entries: remove nodes not seen in 5 minutes
        """
        # TODO: Implement actual node discovery logic
        # 1. Parse Tailscale peer list (JSON output)
        # 2. Call Exo API: GET /v1/nodes
        # 3. Build NodeProfile for each discovered node
        # 4. Update self._nodes and return list
        pass

    async def get_headroom(self, node_id: str) -> dict[str, Any]:
        """
        Get available resources on a specific node.

        TODO Implementation:
        1. Check node exists in self._nodes
        2. Run platform-specific metric collection:
           - Desktop/Laptop: psutil + nvidia-smi
           - Android: ADB shell commands (dumpsys)
        3. Return normalized headroom dict

        Args:
            node_id: Target node identifier

        Returns:
            Dict with keys:
            - cpu_pct: CPU usage percentage
            - vram_free_gb: Free GPU memory in GB
            - ram_free_gb: Free system RAM in GB
            - thermal_margin_c: Thermal headroom (limit - current)
            - battery_pct: Battery percentage (if applicable)

        Raises:
            ValueError: If node_id not found in cluster

        Edge Cases:
        - nvidia-smi fails: fallback to CUDA API
        - ADB connection fails: return last cached values with stale flag
        """
        # TODO: Implement headroom collection
        pass

    async def route_task(self, task: dict[str, Any]) -> str:
        """
        Route a task to the best available node.

        TODO Implementation:
        1. Get headroom for all known nodes
        2. Apply scoring formula:
           score = (vram_free * 0.4) + (ram_free * 0.2) +
                   (thermal_margin * 0.2) + (battery_factor * 0.2)
        3. Exclude nodes where:
           - thermal_margin_c < 10 (overheating risk)
           - battery_pct < 20 (laptop/android only)
           - vram_free_gb < task.vram_required
        4. Return node_id of highest-scoring node

        Args:
            task: Task dict containing vram_required, priority, etc.

        Returns:
            node_id of selected node

        Edge Cases:
        - No eligible nodes: return empty string, task stays queued
        - Multiple equal scores: prefer desktop over laptop over android
        """
        # TODO: Implement task routing with scoring
        pass

    async def migrate_task(
        self,
        task_id: str,
        from_node: str,
        to_node: str,
        task_state: dict[str, Any],
    ) -> None:
        """
        Migrate a running task from one node to another.

        TODO Implementation:
        1. Serialize task_state to JSON
        2. Publish to Redis stream: cluster:migrations
        3. Include metadata: task_id, from_node, to_node, timestamp
        4. The target node should subscribe and pick up the task

        Args:
            task_id: Unique task identifier
            from_node: Source node ID
            to_node: Destination node ID
            task_state: Serialized task state (inputs, outputs, checkpoint)

        Raises:
            ConnectionError: If Redis is unavailable

        Edge Cases:
        - Migration stream full: use XTRIM to prune old entries
        - Target node offline: keep in stream, retry on next poll
        """
        # TODO: Implement task migration via Redis Streams
        pass

    async def shutdown(self) -> None:
        """Clean up resources on shutdown."""
        if self._redis_client:
            await self._redis_client.close()
        self._nodes.clear()