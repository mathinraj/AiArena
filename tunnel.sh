#!/bin/bash
# Creates a tunnel so you can access the app from your phone
echo "Creating tunnel to localhost:8000..."
echo "Look for the URL like: https://xxxxx.trycloudflare.com"
echo ""
cloudflared tunnel --url http://localhost:8000
