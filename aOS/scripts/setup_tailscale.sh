#!/bin/bash
# Setup Tailscale for aOS mesh network
# Run this on each node (desktop, laptop, android)

set -e

echo "=== aOS Tailscale Setup ==="

# Check if Tailscale is installed
if ! command -v tailscale &> /dev/null; then
    echo "Error: Tailscale is not installed"
    echo "Install from: https://tailscale.com/download"
    exit 1
fi

# Check if already logged in
if ! tailscale status --json 2>/dev/null | grep -q '"BackendState":"Running"'; then
    echo "Tailscale not logged in. Please run:"
    echo "  tailscale up --accept-routes --accept-dns"
    exit 1
fi

echo "Tailscale is running"

# Enable subnet router if not already (for node-to-node communication)
echo "Enabling subnet router..."
tailscale set --accept-routes

# Get Tailscale IP
TS_IP=$(tailscale ip -4 2>/dev/null || echo "not-assigned")
echo "Tailscale IP: $TS_IP"

# Print peer information
echo ""
echo "=== Connected Peers ==="
tailscale status --json | python3 -c "
import json
import sys
data = json.load(sys.stdin)
for peer, info in data.get('Peer', {}).items():
    print(f\"{info.get('HostName', 'unknown')}: {info.get('TailscaleIP', 'N/A')}\")
"

echo ""
echo "=== Setup Complete ==="
echo "Desktop node should be reachable at: $TS_IP"
echo ""
echo "To allow other nodes to connect:"
echo "  tailscale up --accept-routes --operator=\$USER"
