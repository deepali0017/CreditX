#!/bin/bash
echo ""
echo "================================================"
echo "   🌿 CreditX — Carbon Intelligence Platform"
echo "================================================"
echo ""

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR" || exit 1

if [ -f "$PROJECT_DIR/firebase.local.env" ]; then
  echo "🔐 Loading Firebase config from firebase.local.env"
  set -a
  source "$PROJECT_DIR/firebase.local.env"
  set +a
  echo "✅ Firebase config loaded"
  echo ""
fi

# ── Kill anything already on port 8080 ──
echo "🔍 Checking port 8080..."
PORT_PID=$(lsof -ti:8080 2>/dev/null)
if [ -n "$PORT_PID" ]; then
  echo "⚠️  Port 8080 in use (PID $PORT_PID) — stopping it..."
  kill -9 $PORT_PID 2>/dev/null
  sleep 1
fi
echo "✅ Port 8080 is free"
echo ""

# ── Install dependencies ──
echo "📦 Installing dependencies..."
python3 -m venv .venv 2>/dev/null
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "✅ Dependencies ready"
echo ""

echo "  🌐 Backend running at: http://localhost:8080"
echo "  📖 Opening browser in 2 seconds..."
echo "  🛑 Press Ctrl+C to stop."
echo ""

# ── Open browser (Mac = open, Linux = xdg-open) ──
(sleep 2 && (open "http://localhost:8080" 2>/dev/null || xdg-open "http://localhost:8080" 2>/dev/null)) &

# ── Run Flask ──
python3 app.py
