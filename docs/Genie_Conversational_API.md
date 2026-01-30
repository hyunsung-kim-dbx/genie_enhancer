# Genie Conversational API Reference

> **Purpose**: API endpoints for asking Genie questions and getting SQL responses
> **Used by**: Self-healing benchmark loop

---

## Overview

The Genie Conversational API allows programmatic interaction with a Genie Space:
- Start conversations
- Send follow-up messages
- Retrieve responses (including generated SQL)

This is essential for the self-healing benchmark loop that tests whether Genie answers questions correctly.

---

## API Endpoints

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Start Conversation | POST | `/api/2.0/genie/spaces/{space_id}/start-conversation` |
| Send Message | POST | `/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages` |
| Get Message | GET | `/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}` |
| Get Conversation | GET | `/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}` |

---

## Start Conversation

Start a new conversation with a question.

### Request

```http
POST /api/2.0/genie/spaces/{space_id}/start-conversation
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "content": "What is the total DAU for PUBG in January 2025?"
}
```

### Response

```json
{
  "space_id": "01ef274d35a310b5bffd01dadcbaf577",
  "conversation_id": "abc123def456",
  "message_id": "msg_789xyz",
  "status": "EXECUTING"
}
```

### Important Notes
- Response is **asynchronous** - Genie processes in background
- Poll the `Get Message` endpoint for results
- Status can be: `EXECUTING`, `COMPLETED`, `FAILED`

---

## Get Message Result

Poll for message completion and get the response.

### Request

```http
GET /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}
Authorization: Bearer <token>
```

### Response (Completed with SQL)

```json
{
  "message_id": "msg_789xyz",
  "conversation_id": "abc123def456",
  "status": "COMPLETED",
  "content": "Here's the DAU for PUBG in January 2025:",
  "attachments": [
    {
      "type": "QUERY",
      "query": {
        "id": "query_123",
        "body": "SELECT MEASURE(dau) as total_dau\nFROM catalog.schema.kpi_metrics\nWHERE game_code = 'bro'\n  AND event_date >= DATE '2025-01-01'\n  AND event_date < DATE '2025-02-01'\nGROUP BY ALL",
        "warehouse_id": "abc123",
        "state": "SUCCEEDED"
      }
    },
    {
      "type": "QUERY_RESULT",
      "data": {
        "columns": ["total_dau"],
        "rows": [
          {"total_dau": 1500000}
        ],
        "row_count": 1
      }
    }
  ],
  "created_at": "2025-01-29T10:30:00Z"
}
```

### Response (Failed)

```json
{
  "message_id": "msg_789xyz",
  "status": "FAILED",
  "error": {
    "code": "SQL_EXECUTION_ERROR",
    "message": "Column 'dau' does not exist"
  }
}
```

---

## Send Follow-up Message

Continue an existing conversation.

### Request

```http
POST /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "content": "Now show me the breakdown by platform"
}
```

### Response

Same as `Start Conversation` - returns message_id to poll.

---

## Python Client Implementation

```python
import requests
import time
from typing import Dict, Optional, Any

class GenieConversationalClient:
    """Client for Genie Conversational API."""

    def __init__(self, host: str, token: str, space_id: str):
        self.base_url = f"https://{host}/api/2.0/genie/spaces/{space_id}"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.space_id = space_id

    def start_conversation(self, question: str) -> Dict:
        """Start a new conversation with Genie."""
        url = f"{self.base_url}/start-conversation"
        payload = {"content": question}

        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def send_message(self, conversation_id: str, message: str) -> Dict:
        """Send a follow-up message."""
        url = f"{self.base_url}/conversations/{conversation_id}/messages"
        payload = {"content": message}

        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def get_message(self, conversation_id: str, message_id: str) -> Dict:
        """Get a message result."""
        url = f"{self.base_url}/conversations/{conversation_id}/messages/{message_id}"

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def wait_for_completion(
        self,
        conversation_id: str,
        message_id: str,
        timeout: int = 120,
        poll_interval: int = 2
    ) -> Dict:
        """
        Poll until message is completed or timeout.

        Args:
            conversation_id: The conversation ID
            message_id: The message ID to poll
            timeout: Max seconds to wait
            poll_interval: Seconds between polls

        Returns:
            The completed message result

        Raises:
            TimeoutError: If message doesn't complete within timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = self.get_message(conversation_id, message_id)
            status = result.get("status")

            if status == "COMPLETED":
                return result
            elif status == "FAILED":
                return result
            elif status in ("EXECUTING", "PENDING"):
                time.sleep(poll_interval)
            else:
                raise ValueError(f"Unknown status: {status}")

        raise TimeoutError(
            f"Message {message_id} did not complete within {timeout}s"
        )

    def ask(self, question: str, timeout: int = 120) -> Dict:
        """
        Complete flow: ask question and wait for answer.

        Args:
            question: Natural language question
            timeout: Max seconds to wait for response

        Returns:
            {
                "question": str,
                "conversation_id": str,
                "message_id": str,
                "status": str,
                "sql": str or None,
                "result": dict or None,
                "error": str or None
            }
        """
        # Start conversation
        start_result = self.start_conversation(question)
        conversation_id = start_result["conversation_id"]
        message_id = start_result["message_id"]

        # Wait for completion
        result = self.wait_for_completion(conversation_id, message_id, timeout)

        # Extract relevant info
        return {
            "question": question,
            "conversation_id": conversation_id,
            "message_id": message_id,
            "status": result.get("status"),
            "sql": self._extract_sql(result),
            "result": self._extract_result(result),
            "error": result.get("error", {}).get("message") if result.get("status") == "FAILED" else None
        }

    def _extract_sql(self, result: Dict) -> Optional[str]:
        """Extract SQL from message attachments."""
        for attachment in result.get("attachments", []):
            if attachment.get("type") == "QUERY":
                return attachment.get("query", {}).get("body")
        return None

    def _extract_result(self, result: Dict) -> Optional[Dict]:
        """Extract query result from message attachments."""
        for attachment in result.get("attachments", []):
            if attachment.get("type") == "QUERY_RESULT":
                return attachment.get("data")
        return None
```

---

## Usage Examples

### Basic Question

```python
client = GenieConversationalClient(
    host="krafton-sandbox.cloud.databricks.com",
    token="your_token",
    space_id="01ef274d35a310b5bffd01dadcbaf577"
)

# Ask a question
response = client.ask("What is the total DAU for PUBG in January 2025?")

print(f"Status: {response['status']}")
print(f"SQL: {response['sql']}")
print(f"Result: {response['result']}")
```

### Benchmark Testing

```python
def test_benchmark(client, benchmark):
    """Test a single benchmark question."""
    question = benchmark["question"]
    expected_sql = benchmark["expected_sql"]

    response = client.ask(question)

    if response["status"] != "COMPLETED":
        return {
            "passed": False,
            "reason": f"Genie failed: {response['error']}"
        }

    # Compare SQL (simple check - could be more sophisticated)
    genie_sql = response["sql"]
    if genie_sql is None:
        return {
            "passed": False,
            "reason": "Genie did not generate SQL"
        }

    # Basic comparison - normalize and compare
    if normalize_sql(genie_sql) == normalize_sql(expected_sql):
        return {"passed": True}
    else:
        return {
            "passed": False,
            "reason": "SQL mismatch",
            "genie_sql": genie_sql,
            "expected_sql": expected_sql
        }

def normalize_sql(sql: str) -> str:
    """Normalize SQL for comparison."""
    import re
    sql = sql.upper()
    sql = re.sub(r'\s+', ' ', sql)
    sql = sql.strip()
    return sql
```

### Follow-up Questions

```python
# Start conversation
result = client.start_conversation("What is DAU for PUBG?")
conv_id = result["conversation_id"]
msg_id = result["message_id"]

# Wait for first answer
first_response = client.wait_for_completion(conv_id, msg_id)
print(f"First answer: {first_response}")

# Ask follow-up
followup = client.send_message(conv_id, "Now break it down by platform")
followup_msg_id = followup["message_id"]

# Wait for follow-up answer
followup_response = client.wait_for_completion(conv_id, followup_msg_id)
print(f"Follow-up answer: {followup_response}")
```

---

## Error Handling

### Common Errors

| Error Code | Description | Solution |
|------------|-------------|----------|
| `SQL_EXECUTION_ERROR` | Generated SQL failed to execute | Check Genie Space metadata |
| `TABLE_NOT_FOUND` | Referenced table doesn't exist | Verify table in Unity Catalog |
| `COLUMN_NOT_FOUND` | Referenced column doesn't exist | Add column or synonym |
| `TIMEOUT` | Query took too long | Increase timeout or optimize query |
| `PERMISSION_DENIED` | No access to table/warehouse | Check permissions |

### Retry Logic

```python
import time
from functools import wraps

def retry_on_timeout(max_retries: int = 3, backoff: float = 2.0):
    """Decorator to retry on timeout errors."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except TimeoutError as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        sleep_time = backoff * (2 ** attempt)
                        print(f"Timeout, retrying in {sleep_time}s...")
                        time.sleep(sleep_time)
            raise last_error
        return wrapper
    return decorator

# Usage
@retry_on_timeout(max_retries=3)
def ask_with_retry(client, question):
    return client.ask(question)
```

---

## Integration with Self-Healing Loop

The Conversational API is used in the self-healing loop to:

1. **Test benchmarks**: Ask Genie each benchmark question
2. **Compare SQL**: Check if Genie's SQL matches expected
3. **Identify failures**: Determine why Genie answered incorrectly
4. **Re-test after fixes**: Verify improvements work

```python
def self_healing_iteration(client, benchmarks, space_updater):
    """One iteration of the self-healing loop."""
    results = []

    for benchmark in benchmarks:
        # Test benchmark
        response = client.ask(benchmark["question"])
        passed = compare_sql(response["sql"], benchmark["expected_sql"])

        if not passed:
            # Analyze failure
            analysis = analyze_failure(response, benchmark)

            # Apply fix
            if analysis["fix_type"] == "synonym_missing":
                space_updater.add_synonym(
                    analysis["table"],
                    analysis["column"],
                    analysis["synonym"]
                )

        results.append({
            "question": benchmark["question"],
            "passed": passed,
            "genie_sql": response["sql"]
        })

    pass_rate = sum(1 for r in results if r["passed"]) / len(results)
    return results, pass_rate
```

---

## Rate Limits & Best Practices

### Rate Limits
- **Requests per minute**: ~60 (varies by workspace)
- **Concurrent conversations**: ~10

### Best Practices
1. **Reuse conversations** for related questions (reduces overhead)
2. **Implement backoff** for rate limit errors
3. **Batch benchmarks** - don't test all at once
4. **Cache results** for unchanged spaces
5. **Set reasonable timeouts** (60-120s for complex queries)

---

## Troubleshooting

### Genie Returns No SQL
- Check if Genie Space has data sources
- Verify user has permissions
- Check if question is within scope

### SQL Doesn't Match Expected
- Add synonyms for misunderstood terms
- Improve column/table descriptions
- Add example queries for patterns

### Timeout Errors
- Increase timeout value
- Simplify benchmark queries
- Check warehouse is running
