#!/bin/bash
# Nightly cron script for aOS self-improvement cycle
# Runs DPO generation, LoRA consolidation, and synthetic dreaming

set -e

# Configuration
LOG_DIR="${AOS_LOGS_DIR:-./logs}"
NIGHTLY_LOG="$LOG_DIR/nightly_$(date +%Y-%m-%d).log"
PYTHON_BIN="${AOS_PYTHON:-python3}"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "=== aOS Nightly Cycle ===" | tee -a "$NIGHTLY_LOG"
echo "Started at: $(date)" | tee -a "$NIGHTLY_LOG"

# Check if Docker services are running
echo "Checking Docker services..." | tee -a "$NIGHTLY_LOG"
if ! docker ps | grep -q aos-redis; then
    echo "Error: Docker services not running" | tee -a "$NIGHTLY_LOG"
    echo "Start with: docker compose up -d" | tee -a "$NIGHTLY_LOG"
    exit 1
fi

# Activate Python virtual environment if present
if [ -d ".venv" ]; then
    echo "Activating virtual environment..." | tee -a "$NIGHTLY_LOG"
    source .venv/bin/activate
fi

# Run the nightly cycle
echo "Starting nightly cycle..." | tee -a "$NIGHTLY_LOG"

cd /workspace/project/Victor/aOS

if $PYTHON_BIN -c "from aos.consolidation import NightlyCycle; import asyncio; asyncio.run(NightlyCycle().run())" 2>&1 | tee -a "$NIGHTLY_LOG"; then
    echo "Nightly cycle completed successfully" | tee -a "$NIGHTLY_LOG"
else
    echo "Nightly cycle completed with errors" | tee -a "$NIGHTLY_LOG"
    # Don't fail the cron job, just log
fi

echo "Finished at: $(date)" | tee -a "$NIGHTLY_LOG"
echo "=== End of Nightly Cycle ===" | tee -a "$NIGHTLY_LOG"

# Clean up old logs (keep last 30 days)
find "$LOG_DIR" -name "nightly_*.log" -mtime +30 -delete

exit 0
