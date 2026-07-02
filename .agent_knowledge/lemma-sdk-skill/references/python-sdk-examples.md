# Python SDK Reference Examples

## Complete Authentication Patterns

### 1. Environment-Based Auth (Recommended)

```python
import os
from lemma_sdk import Pod, Lemma

# Set environment variables
os.environ["LEMMA_TOKEN"] = "your-access-token"
os.environ["LEMMA_POD_ID"] = "your-pod-id"
os.environ["LEMMA_ORG_ID"] = "your-org-id"
os.environ["LEMMA_BASE_URL"] = "https://api.lemma.work"

# Create authenticated pod
pod = Pod.from_env()

# Or for org-level operations
lemma = Lemma.from_env(org_id="your-org-id")
```

### 2. Explicit Auth (API Keys, Service Accounts)

```python
from lemma_sdk import Pod, Lemma

pod = Pod(
    pod_id="pod-123",
    org_id="org-456",
    token="your-token",
    base_url="https://api.lemma.work",
    auth_url="https://lemma.work/auth",
    timeout=30,
    ssl_no_verify=False
)

# For local development
local_pod = Pod(
    pod_id="dev-pod",
    org_id="dev-org",
    token="dev-token",
    base_url="http://127.0.0.1:8711"
)
```

### 3. Config File Auth

```python
from lemma_sdk import Pod

# Reads from ~/.lemma/config.json or custom path
os.environ["LEMMA_CONFIG_FILE"] = "/path/to/config.json"
pod = Pod.from_env()
```

## Table Operations

### Schema Definition

Tables are defined in Lemma platform. The SDK provides typed access:

```python
# Get table metadata
table_info = pod.tables.get("tickets")
print(f"Table fields: {table_info['fields']}")

# List all tables
tables = pod.tables.list()
for table in tables["items"]:
    print(f"{table['name']}: {table.get('description', 'No description')}")
```

### Record CRUD

```python
# CREATE
new_ticket = pod.records.create("tickets", {
    "title": "User cannot login",
    "description": "Getting 500 error on /auth/login",
    "priority": "high",
    "status": "new",
    "assignee_email": "support@example.com"
})
ticket_id = new_ticket["id"]

# READ
ticket = pod.records.get("tickets", ticket_id)
print(f"Title: {ticket['title']}, Status: {ticket['status']}")

# UPDATE (partial update - only specified fields change)
pod.records.update("tickets", ticket_id, {
    "status": "in_progress",
    "assignee_email": "dev@example.com"
})

# DELETE
pod.records.delete("tickets", ticket_id)

# LIST with filtering
open_tickets = pod.records.list(
    "tickets",
    filter=[
        {"field": "status", "op": "eq", "value": "open"},
        {"field": "priority", "op": "in", "value": ["high", "urgent"]},
    ],
    sort=[{"field": "created_at", "direction": "desc"}],
    limit=50
)
```

### Filter Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` | Equals | `{"field": "status", "op": "eq", "value": "open"}` |
| `ne` | Not equals | `{"field": "status", "op": "ne", "value": "closed"}` |
| `gt` | Greater than | `{"field": "amount", "op": "gt", "value": 100}` |
| `gte` | Greater or equal | `{"field": "amount", "op": "gte", "value": 100}` |
| `lt` | Less than | `{"field": "priority", "op": "lt", "value": 5}` |
| `lte` | Less or equal | `{"field": "priority", "op": "lte", "value": 5}` |
| `in` | In list | `{"field": "status", "op": "in", "value": ["new", "open"]}` |
| `nin` | Not in list | `{"field": "type", "op": "nin", "value": ["test", "demo"]}` |
| `contains` | String contains | `{"field": "title", "op": "contains", "value": "bug"}` |
| `startswith` | String starts with | `{"field": "email", "op": "startswith", "value": "admin"}` |
| `endswith` | String ends with | `{"field": "email", "op": "endswith", "value": ".edu"}` |

### Bulk Operations

```python
# BULK CREATE
created = pod.records.bulk_create("ticket_events", [
    {"ticket_id": ticket_id, "kind": "created", "timestamp": "2024-01-01T00:00:00Z"},
    {"ticket_id": ticket_id, "kind": "assigned", "assigned_to": "dev@example.com"},
    {"ticket_id": ticket_id, "kind": "status_change", "from": "new", "to": "open"},
])
print(f"Created {created['count']} events")

# BULK UPDATE (requires id field)
updated = pod.records.bulk_update("tickets", [
    {"id": ticket_id_1, "status": "resolved"},
    {"id": ticket_id_2, "status": "closed", "resolved_at": "2024-01-01T00:00:00Z"},
])
print(f"Updated {updated['count']} tickets")

# BULK DELETE (just ids)
deleted = pod.records.bulk_delete("tickets", [ticket_id_1, ticket_id_2])
print(f"Deleted {deleted['count']} tickets")
```

### Raw SQL Queries

```python
# Aggregate queries
stats = pod.query("""
    SELECT
        status,
        COUNT(*) as count,
        AVG(priority) as avg_priority
    FROM tickets
    GROUP BY status
    ORDER BY count DESC
""")

# Join queries (non-RLS tables only)
leads_companies = pod.query("""
    SELECT l.id, l.name, l.email, c.name as company_name
    FROM leads l
    JOIN companies c ON l.company_id = c.id
    WHERE l.created_at > '2024-01-01'
""")

# Complex filtering
filtered = pod.query("""
    SELECT * FROM tickets
    WHERE status IN ('new', 'open')
    AND (priority = 'high' OR assignee_email IS NULL)
    ORDER BY created_at DESC
    LIMIT 100
""")
```

## File Operations

### Directory Management

```python
# Create folder structure
pod.files.create_folder("/knowledge", description="Knowledge base")
pod.files.create_folder("/knowledge/products", description="Product documentation")
pod.files.create_folder("/reports", description="Generated reports")
pod.files.create_folder("/templates", description="Email and document templates")

# List folder contents
contents = pod.files.list_children("/knowledge")
for item in contents:
    print(f"{item['type']}: {item['path']}")

# Move/rename files
pod.files.move("/reports/summary.md", "/archive/summary-2024.md")

# Delete files/folders
pod.files.delete("/archive/old-report.md")
pod.files.delete_folder("/archive")  # Recursive delete
```

### File Upload

```python
# Upload text content
pod.files.upload_content(
    "/reports/weekly-summary.md",
    content="# Weekly Summary\n\nGenerated on 2024-01-01",
    directory_path="/reports"
)

# Upload file from disk
pod.files.upload("/path/to/document.pdf", directory_path="/knowledge/docs")

# Upload with metadata
pod.files.upload(
    "/path/to/image.png",
    directory_path="/assets",
    description="Company logo",
    tags=["logo", "brand"]
)
```

### File Search

```python
# Simple text search
results = pod.files.search("refund policy").to_dict()

# Scoped search with RAG
results = pod.files.search(
    query="data retention policy",
    scope_path="/legal",
    scope_mode="SUBTREE",  # Search in folder and subfolders
    search_method="HYBRID",  # Combine text and vector search
    limit=10
)

# Download file content
markdown_content = pod.files.download_markdown("/knowledge/guide.md")
raw_content = pod.files.download("/knowledge/data.csv")
```

## Functions

### Function Definition

```python
from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod
from typing import Optional
from datetime import datetime

class CalculateDiscountInput(BaseModel):
    customer_id: str
    order_total: float
    discount_code: Optional[str] = None

class CalculateDiscountOutput(BaseModel):
    original_total: float
    discount_amount: float
    final_total: float
    discount_applied: bool
    message: str

async def calculate_discount(
    ctx: FunctionContext,
    data: CalculateDiscountInput
) -> CalculateDiscountOutput:
    """
    Calculate discount for an order.
    Runs within Lemma's secure function runtime.
    """
    pod = Pod.from_env()  # Auto-authenticated as function principal

    # Get customer info
    customer = pod.records.get("customers", data.customer_id)

    # Calculate discount
    discount_amount = 0.0
    discount_applied = False
    message = "No discount applied"

    # Check discount code
    if data.discount_code:
        codes = pod.records.list(
            "discount_codes",
            filter=[{"field": "code", "op": "eq", "value": data.discount_code}]
        )
        if codes["items"]:
            code = codes["items"][0]
            discount_amount = data.order_total * (code["percentage"] / 100)
            discount_applied = True
            message = f"Applied {code['percentage']}% discount"

    # Check customer tier discount
    if not discount_applied and customer.get("tier") == "premium":
        discount_amount = data.order_total * 0.10
        discount_applied = True
        message = "Applied 10% premium customer discount"

    return CalculateDiscountOutput(
        original_total=data.order_total,
        discount_amount=round(discount_amount, 2),
        final_total=round(data.order_total - discount_amount, 2),
        discount_applied=discount_applied,
        message=message
    )
```

### Running Functions

```python
# Sync run
result = pod.functions.run("calculate_discount", {
    "customer_id": "cust_123",
    "order_total": 150.00,
    "discount_code": "SAVE20"
}).to_dict()

print(f"Final total: ${result['output_data']['final_total']}")

# Async run with polling
run = pod.functions.run("send_notifications", {
    "template": "welcome",
    "recipient_ids": ["user_1", "user_2", "user_3"]
})

# Poll for completion
import time
while run.to_dict()["status"] in ["pending", "running"]:
    time.sleep(2)
    run = pod.functions.get_run(run.to_dict()["id"])

print(f"Result: {run.to_dict()}")
```

## Agents

### Agent Management

```python
# List available agents
agents = pod.agents.list()
for agent in agents["items"]:
    print(f"{agent['name']}: {agent.get('description', 'No description')}")

# Get agent details
agent = pod.agents.get("sales_assistant")
print(f"Input schema: {agent.get('input_schema')}")
print(f"Tools: {agent.get('tool_grants', [])}")
```

### Agent Conversations

```python
# Create a conversation with an agent
conversation = pod.conversations.create_for_agent(
    agent_name="sales_assistant",
    title="Product inquiry - Enterprise Plan"
)

conv_id = conversation.to_dict()["id"]

# Send a message
pod.conversations.send(conv_id, """
Please help me understand the Enterprise Plan features.
I'm interested in:
1. User limits
2. API rate limits
3. Custom integrations
4. SLA guarantees
""")

# Get conversation history
messages = pod.conversations.messages.list(conv_id)
for msg in messages["items"]:
    print(f"[{msg['role']}] {msg.get('text', '')[:100]}...")

# Stream responses (async)
async def chat_with_agent():
    async for event in pod.conversations.stream(conv_id, "What are the pricing tiers?"):
        if event.get("type") == "text":
            print(event["content"], end="", flush=True)
        elif event.get("type") == "tool_call":
            print(f"\n[Calling tool: {event['tool']}]")
```

## Workflows

### Workflow Management

```python
# List workflows
workflows = pod.workflows.list()
for wf in workflows["items"]:
    print(f"{wf['name']}: {wf.get('description', '')}")

# Get workflow details
wf = pod.workflows.get("onboarding_flow")
print(f"Steps: {wf.get('steps')}")
```

### Running Workflows

```python
# Start workflow
run = pod.workflows.create_run(
    "onboarding_flow",
    inputs={"user_id": "user_123", "plan": "enterprise"}
).to_dict()

run_id = run["id"]
print(f"Started workflow run: {run_id}")

# Check status
status = pod.workflows.get_run(run_id).to_dict()
print(f"Status: {status['status']}")

# Handle human approval steps
if status["status"] == "waiting":
    for wait in status.get("waiting_nodes", []):
        if wait["type"] == "form":
            print(f"Waiting at: {wait['node_id']} - {wait.get('form_title')}")
            # Submit form
            pod.workflows.submit_form(
                run_id,
                node_id=wait["node_id"],
                inputs={"approved": True, "notes": "Looks good!"}
            )

# Cancel workflow
pod.workflows.cancel_run(run_id)

# Retry failed workflow
pod.workflows.retry_run(run_id)
```

## Schedules

### Schedule Management

```python
# Create schedule
schedule = pod.schedules.create({
    "name": "daily_report",
    "workflow_name": "generate_report",
    "schedule_type": "cron",
    "cron_expression": "0 8 * * *",  # Daily at 8 AM
    "inputs": {"report_type": "daily"},
    "timezone": "America/New_York"
})

# List schedules
schedules = pod.schedules.list()

# Pause/resume schedule
pod.schedules.update(schedule["id"], {"enabled": False})
pod.schedules.update(schedule["id"], {"enabled": True})

# Delete schedule
pod.schedules.delete(schedule["id"])
```

## Error Handling

### Comprehensive Error Handling

```python
from lemma_sdk import LemmaAPIError, LemmaConfigError, LemmaAuthError

def robust_api_call():
    try:
        # Try to get a record
        record = pod.records.get("tickets", "rec_nonexistent")
        return record

    except LemmaAPIError as e:
        if e.status_code == 404:
            print(f"Record not found: {e.message}")
            return None
        elif e.status_code == 403:
            print(f"Permission denied: {e.message}")
            raise PermissionError(f"Cannot access record: {e.message}")
        elif e.status_code == 429:
            print("Rate limited, backing off...")
            time.sleep(60)  # Wait and retry
            return robust_api_call()
        else:
            print(f"API error {e.status_code}: {e.code} - {e.message}")
            raise

    except LemmaConfigError as e:
        print(f"Configuration error: {e}")
        print("Please check environment variables and configuration")
        raise

    except LemmaAuthError as e:
        print(f"Authentication error: {e}")
        # Refresh token logic here
        raise

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

# Retry decorator for transient failures
from functools import wraps
import time

def retry_on_rate_limit(max_retries=3, backoff=60):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except LemmaAPIError as e:
                    if e.status_code == 429 and attempt < max_retries - 1:
                        print(f"Rate limited, attempt {attempt + 1}/{max_retries}")
                        time.sleep(backoff * (attempt + 1))
                    else:
                        raise
            return None
        return wrapper
    return decorator

@retry_on_rate_limit(max_retries=3)
def get_ticket(ticket_id):
    return pod.records.get("tickets", ticket_id)
```

## Advanced Patterns

### Async Operations

```python
import asyncio
from lemma_sdk import Pod

async def process_tickets():
    async with Pod.from_env() as pod:
        # Get all open tickets
        tickets = pod.records.list("tickets", filter=[
            {"field": "status", "op": "eq", "value": "open"}
        ])

        # Process each ticket concurrently
        tasks = []
        for ticket in tickets["items"]:
            task = process_single_ticket(pod, ticket)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

async def process_single_ticket(pod, ticket):
    try:
        # Run triage function
        result = await pod.functions.run_async("triage_ticket", {
            "ticket_id": ticket["id"]
        })
        return {"ticket_id": ticket["id"], "result": result}
    except Exception as e:
        return {"ticket_id": ticket["id"], "error": str(e)}

# Run
asyncio.run(process_tickets())
```

### Pagination Helper

```python
def get_all_records(table_name, batch_size=100):
    """Fetch all records from a table with automatic pagination."""
    all_records = []
    page_token = None

    while True:
        response = pod.records.list(
            table_name,
            limit=batch_size,
            page_token=page_token
        )

        all_records.extend(response["items"])

        page_token = response.get("next_page_token")
        if not page_token:
            break

    return all_records

# Usage
all_tickets = get_all_records("tickets")
print(f"Total tickets: {len(all_tickets)}")
```

### Observer Pattern for Live Updates

```python
# For real-time updates, use webhooks or polling
# The SDK doesn't have built-in WebSocket support like TypeScript,
# but you can implement polling:

import threading
import time

class TicketObserver:
    def __init__(self, pod, callback):
        self.pod = pod
        self.callback = callback
        self.running = False
        self.thread = None
        self.last_check = None

    def start(self, poll_interval=5):
        self.running = True
        self.last_check = time.time()
        self.thread = threading.Thread(target=self._poll, args=(poll_interval,))
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _poll(self, interval):
        while self.running:
            try:
                # Get updated records since last check
                records = pod.records.list(
                    "tickets",
                    filter=[{"field": "updated_at", "op": "gt", "value": self.last_check}]
                )

                for record in records["items"]:
                    self.callback("update", record)

                self.last_check = time.time()
            except Exception as e:
                print(f"Poll error: {e}")

            time.sleep(interval)

# Usage
def on_ticket_update(operation, ticket):
    print(f"{operation}: {ticket['id']} - {ticket.get('title')}")

observer = TicketObserver(pod, on_ticket_update)
observer.start(poll_interval=5)

# Later
observer.stop()
```