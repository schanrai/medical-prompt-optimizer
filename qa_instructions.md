

**Testing using venv from the terminal**
activate:
   source venv/bin/activate
You'll see (venv) appear in your prompt
Run the Call 1 standalone test:
   python -m src.call_1_scope
   python -m src.call_1_scope
Or run the full pipeline with 7 test cases:
   python -m src.pipeline
That's it! You'll see:
Console logging from telemetry.py (timestamped INFO lines)
The test output (3 test cases with results)
Success/failure for each test
Token counts and latency
To see just the test results without the logging noise:

   python -m src.call_1_scope 2>/dev/null

(This redirects stderr/logging to nowhere, shows only the test output)

To verify telemetry file is being written:
   ls -la logs/cat logs/telemetry.jsonl
(Note: telemetry.jsonl won't have entries yet - log_run() isn't called until the full pipeline, which we haven't built. Right now only log_step() is active for console debugging)

When you're done testing:
   deactivate
(Exits the venv)

**To start the server:**
   python -m uvicorn src.app:app --reload --host 0.0.0.0 --port 8000



**Stage 0 testing with API server running**

# Test empty input
curl -X POST http://localhost:8000/api/check \
  -H "Content-Type: application/json" \
  -d '{"question": ""}'

# Test too short
curl -X POST http://localhost:8000/api/check \
  -H "Content-Type: application/json" \
  -d '{"question": "hi"}'

# Test gibberish
curl -X POST http://localhost:8000/api/check \
  -H "Content-Type: application/json" \
  -d '{"question": "asdf jkl qwer"}'

# Test valid question (will hit the LLM)
curl -X POST http://localhost:8000/api/check \
  -H "Content-Type: application/json" \
  -d '{"question": "What causes chest pain?"}'