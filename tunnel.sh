#!/bin/bash
# Creates a tunnel and displays a QR code for mobile access
echo "Creating tunnel to localhost:8000..."
echo ""

# Start cloudflared and capture output
cloudflared tunnel --url http://localhost:8000 2>&1 | while read -r line; do
    # Look for the tunnel URL
    url=$(echo "$line" | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com')
    if [ -n "$url" ]; then
        echo "════════════════════════════════════════"
        echo "  Scan this QR code on your phone:"
        echo "════════════════════════════════════════"
        echo ""
        qrencode -t ANSIUTF8 "$url"
        echo ""
        echo "  URL: $url"
        echo "════════════════════════════════════════"
        echo ""
        echo "Tunnel is running. Press Ctrl+C to stop."
    fi
done
