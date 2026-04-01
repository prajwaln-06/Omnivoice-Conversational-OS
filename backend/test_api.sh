#!/bin/bash
# Run: bash test_api.sh
# Make sure uvicorn is running first:
# uvicorn main:app --reload --port 8000

BASE="http://localhost:8000"
SESSION_ID=""

pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1"; }

json_field() {
  python - <<'PY' "$1" "$2"
import json,sys
raw=sys.argv[1]
field=sys.argv[2]
try:
    obj=json.loads(raw)
    print(obj.get(field,""))
except Exception:
    print("")
PY
}

echo "Testing OmniVoice API..."

# Test 1: Health check
HEALTH=$(curl -s "$BASE/health")
if echo "$HEALTH" | grep -q '"status"'; then
  pass "Health check"
else
  fail "Health check"
fi

# Test 2: Upload healthcare schema
SCHEMA_PAYLOAD='{"domain":"healthcare","schema":{"fields":["patient_name","symptoms","diagnosis","prescription","follow_up"],"system_prompt":"Extract healthcare fields as JSON"}}'
SCHEMA_RESP=$(curl -s -X POST "$BASE/api/upload-schema" -H "Content-Type: application/json" -d "$SCHEMA_PAYLOAD")
if echo "$SCHEMA_RESP" | grep -q '"domain":"healthcare"'; then
  pass "Upload healthcare schema"
else
  fail "Upload healthcare schema"
fi

# Test 3: Full postcall pipeline with a real audio file
AUDIO_FILE="test_audio.wav"
if [ -f "$AUDIO_FILE" ]; then
  POSTCALL_RESP=$(curl -s -X POST "$BASE/api/postcall/analyze" -F "audio=@$AUDIO_FILE" -F "domain=healthcare")
  SESSION_ID=$(json_field "$POSTCALL_RESP" "session_id")
  if [ -n "$SESSION_ID" ]; then
    pass "Postcall analyze"
  else
    fail "Postcall analyze"
  fi
else
  echo "SKIP: Postcall analyze (no $AUDIO_FILE present)"
fi

# Test 4: Get session by ID
if [ -n "$SESSION_ID" ]; then
  SESSION_RESP=$(curl -s "$BASE/api/session/$SESSION_ID")
  if echo "$SESSION_RESP" | grep -q '"session_id"'; then
    pass "Get session"
  else
    fail "Get session"
  fi
else
  echo "SKIP: Get session (no session id from postcall)"
fi

# Test 5: Approve endpoint
if [ -n "$SESSION_ID" ]; then
  APPROVE_PAYLOAD="{\"session_id\":\"$SESSION_ID\",\"extracted_data\":{\"patient_name\":\"Test\",\"symptoms\":[\"fever\"],\"diagnosis\":\"viral fever\",\"prescription\":\"Paracetamol\",\"follow_up\":\"5 days\"}}"
  APPROVE_RESP=$(curl -s -X POST "$BASE/api/approve" -H "Content-Type: application/json" -d "$APPROVE_PAYLOAD")
  if echo "$APPROVE_RESP" | grep -q '"whatsapp_sent":true'; then
    pass "Approve endpoint"
  else
    fail "Approve endpoint"
  fi
else
  echo "SKIP: Approve endpoint (no session id from postcall)"
fi
