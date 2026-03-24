"""
Top-level orchestrator for aOS.

Runs the main planning loop that polls Redis task queue,
plans via LiteLLM, and dispatches subtasks to appropriate nodes.

Classes:
- ArchitectAgent: Main orchestrator with planning loop
- Task: Task model with metadata
- TaskStatus: Enum for task states

Dependencies:
- Redis Streams: Task queue (pending tasks)
- LiteLLM: Unified LLM gateway for planning
- MQTT: Alerts for stop hooks
- ClusterManager: Node selection

TODO Implementation Order:
1. run_loop() - main polling and planning
2. _detect_retry_storm() - failure detection
3. _trigger_stop_hook() - alert and move to review
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel


class TaskStatus(str, Enum):
    """Status of a task in the system."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEW = "review"  # Moved to human review after retry storm


class Task(BaseModel):
    """
    Represents a task in the orchestrator queue.

    Attributes:
        task_id: Unique task identifier
        description: Natural language task description
        priority: Task priority (higher = more urgent)
        created_at: Timestamp of task creation
        status: Current task status
        retries: Number of retry attempts
        assigned_node: Node currently processing the task
    """

    task_id: str
    description: str
    priority: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    status: TaskStatus = TaskStatus.PENDING
    retries: int = 0
    assigned_node: str | None = None
    subtasks: list[str] = Field(default_factory=list)


class ArchitectAgent:
    """
    Top-level orchestrator that manages the main planning loop.

    Public API:
        run_loop() -> None  # Main async loop
        submit_task(description: str, priority: int) -> str
        get_task_status(task_id: str) -> TaskStatus

    Internal Methods:
        _poll_queue() -> list[Task]
        _plan_subtasks(task: Task) -> list[dict]
        _dispatch_subtask(subtask: dict) -> None
        _detect_retry_storm(task_id: str) -> bool
        _trigger_stop_hook(task_id: str) -> None

    Dependencies:
        - Redis: Task queue (stream: tasks:pending)
        - LiteLLM: Planning via OpenAI-compatible API
        - MQTT: Alert publishing for stop hooks
        - ClusterManager: Node selection for dispatch

    Environment Variables:
        LITELLM_BASE_URL: LiteLLM gateway URL
        LITELLM_MODEL: Model to use for planning (default: gpt-4o)
        MQTT_BROKER: MQTT broker URL
        REDIS_URL: Redis connection string
    """

    def __init__(
        self,
        litellm_base_url: str = "http://localhost:4000",
        litellm_model: str = "gpt-4o",
        redis_url: str = "redis://localhost:6379",
        mqtt_broker: str = "mqtt://localhost:1883",
        poll_interval_ms: int = 500,
    ):
        """
        Initialize the architect agent.

        Args:
            litellm_base_url: LiteLLM gateway URL
            litellm_model: Model identifier for planning
            redis_url: Redis connection URL
            mqtt_broker: MQTT broker URL
            poll_interval_ms: Queue polling interval in milliseconds
        """
        self._litellm_base_url = litellm_base_url
        self._litellm_model = litellm_model
        self._redis_url = redis_url
        self._mqtt_broker = mqtt_broker
        self._poll_interval = poll_interval_ms / 1000.0

        self._redis_client: Any = None
        self._mqtt_client: Any = None
        self._cluster_manager: Any = None
        self._running = False
        self._failure_counts: dict[str, int] = {}

    async def _ensure_clients(self) -> None:
        """Lazily initialize Redis and MQTT clients."""
        # TODO: Import and create redis.asyncio client
        # TODO: Import paho.mqtt.client and connect
        pass

    async def submit_task(self, description: str, priority: int = 0) -> str:
        """
        Submit a new task to the pending queue.

        Args:
            description: Natural language task description
            priority: Task priority (higher = more urgent)

        Returns:
            task_id of the newly created task
        """
        # TODO: Generate UUID for task_id
        # TODO: Serialize Task and push to Redis stream "tasks:pending"
        # TODO: Return task_id
        pass

    async def get_task_status(self, task_id: str) -> TaskStatus | None:
        """
        Get current status of a task.

        Args:
            task_id: Task identifier

        Returns:
            TaskStatus if found, None otherwise
        """
        # TODO: Look up task in Redis and return status
        pass

    async def run_loop(self) -> None:
        """
        Main planning loop - runs continuously until stopped.

        TODO Implementation:
        1. Initialize Redis and MQTT clients
        2. Initialize ClusterManager for node routing
        3. Enter while self._running loop:
           a. Poll tasks:pending stream (XREAD with block)
           b. For each pending task:
              - Call _plan_subtasks() via LiteLLM
              - Dispatch each subtask to appropriate node
           c. Check for retry storms on running tasks
           d. Sleep for poll_interval_ms
        4. On KeyboardInterrupt, set _running = False

        The loop handles:
        - Task polling from Redis Streams
        - LLM-based planning (break down into subtasks)
        - Node selection via ClusterManager
        - Failure detection and stop hooks
        - MQTT alerts for human intervention

        Edge Cases:
        - Redis connection lost: retry with exponential backoff
        - LiteLLM timeout: log error, mark task as failed
        - No nodes available: re-queue task, increment retry
        """
        self._running = True

        # TODO: Initialize clients
        await self._ensure_clients()

        while self._running:
            try:
                # Poll for new tasks
                tasks = await self._poll_queue()

                for task in tasks:
                    # Plan subtasks using LiteLLM
                    subtasks = await self._plan_subtasks(task)

                    # Dispatch each subtask
                    for subtask in subtasks:
                        await self._dispatch_subtask(subtask, task.task_id)

                    # Update task status
                    task.status = TaskStatus.RUNNING

                # Check for retry storms
                await self._check_retry_storms()

                # Wait before next poll
                await asyncio.sleep(self._poll_interval)

            except Exception as e:
                # Log error but continue loop
                print(f"Error in run loop: {e}")
                await asyncio.sleep(1)

    async def _poll_queue(self) -> list[Task]:
        """
        Poll Redis for pending tasks.

        TODO Implementation:
        1. Use XREAD on "tasks:pending" stream with block=500ms
        2. Parse each message into Task object
        3. Return list of pending tasks sorted by priority

        Returns:
            List of pending Task objects
        """
        # TODO: Implement queue polling
        pass

    async def _plan_subtasks(self, task: Task) -> list[dict[str, Any]]:
        """
        Break down a task into subtasks using LiteLLM.

        TODO Implementation:
        1. Build prompt with task description and available tools
        2. Call LiteLLM /v1/chat/completions
        3. Parse LLM response into subtask list
        4. Each subtask: {tool, args, dependencies}

        Args:
            task: Parent task to break down

        Returns:
            List of subtask dictionaries
        """
        # TODO: Build planning prompt
        # TODO: Call LiteLLM API
        # TODO: Parse response into structured subtasks
        pass

    async def _dispatch_subtask(self, subtask: dict[str, Any], parent_id: str) -> None:
        """
        Dispatch a subtask to the appropriate node.

        TODO Implementation:
        1. Use ClusterManager.route_task() to select node
        2. Publish subtask to Redis stream: tasks:{node_id}
        3. Track subtask in parent's subtasks list

        Args:
            subtask: Subtask dictionary with tool and args
            parent_id: Parent task ID for tracking
        """
        # TODO: Route to node and publish to Redis
        pass

    async def _detect_retry_storm(self, task_id: str) -> bool:
        """
        Detect if a task is in a retry storm (consecutive failures).

        TODO Implementation:
        1. Check Redis for consecutive failure count on task_id
        2. Threshold defined in config: retry_storm_threshold (default 5)
        3. If consecutive failures > threshold, return True

        Args:
            task_id: Task to check

        Returns:
            True if retry storm detected, False otherwise
        """
        # TODO: Check failure count in Redis
        # TODO: Compare against threshold
        pass

    async def _trigger_stop_hook(self, task_id: str) -> None:
        """
        Trigger stop hook when retry storm is detected.

        TODO Implementation:
        1. Move task from pending/running to pending_review stream
        2. Log full context (task, retries, subtask outcomes) to Redis
        3. Publish MQTT alert to: alerts/{task_id}
        4. Increment failure count for tracking

        Args:
            task_id: Task that triggered the stop hook
        """
        # TODO: Move to review stream
        # TODO: Log context
        # TODO: Publish MQTT alert
        pass

    async def _check_retry_storms(self) -> None:
        """
        Check all running tasks for retry storms.

        Runs periodically to detect tasks in failure loops.
        """
        # TODO: Iterate running tasks, call _detect_retry_storm
        # TODO: If detected, call _trigger_stop_hook
        pass

    async def stop(self) -> None:
        """Stop the main loop gracefully."""
        self._running = False