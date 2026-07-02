---
name: lemma-sdk-builder
description: Build products using the Lemma SDK. Use when users ask to create applications with Lemma SDK, work with Lemma platform API, integrate Lemma into their products, build agents/workflows on Lemma, or develop using Python/TypeScript SDK. Triggers on phrases like "build with lemma", "lemma sdk", "lemma platform integration", "create lemma agent", "lemma workflow setup".
---

# Lemma SDK Builder

Build production-ready products using the Lemma SDK for Python and TypeScript.

## Quick Start

### Python SDK Installation

```bash
uv pip install lemma-sdk
# or from local source:
uv pip install /path/to/lemma-python
```

### TypeScript SDK Installation

```bash
npm install lemma-sdk
# For React projects:
npm install react react-dom
```

## Authentication

### Python SDK Auth

**Environment variables:**
```python
import os
os.environ["LEMMA_TOKEN"] = "<access-token>"
os.environ["LEMMA_POD_ID"] = "<pod-id>"
os.environ["LEMMA_ORG_ID"] = "<org-id>"
os.environ["LEMMA_BASE_URL"] = "https://api.lemma.work"  # or local: http://127.0.0.1:8711
```

**Explicit construction:**
```python
from lemma_sdk import Pod, Lemma

pod = Pod(
    pod_id="pod-id",
    org_id="org-id",
    token="token",
    base_url="https://api.lemma.work"
)
```

**Context manager pattern:**
```python
with Pod.from_env() as pod:
    result = pod.functions.run("triage_ticket", {"ticket_id": "rec-1"})
```

### TypeScript SDK Auth

```typescript
import { LemmaClient } from "lemma-sdk";

const client = new LemmaClient({
  podId: "<pod-id>",
});

await client.initialize();
```

**Browser (no-build HTML):**
```html
<script src="https://api.lemma.work/public/sdk/lemma-client.js"></script>
<script>
  const client = new window.LemmaClient.LemmaClient();
  // Reads window.__LEMMA_CONFIG__ injected by host
</script>
```

## Core Operations

### Tables & Records (Python)

```python
# Get table reference
tickets = pod.table("tickets")

# CRUD operations
row = tickets.create({"title": "Bug report", "status": "new"})
ticket_id = row["id"]

record = tickets.get(ticket_id)
tickets.update(ticket_id, {"status": "resolved"})
tickets.delete(ticket_id)

# List with filters
rows = pod.records.list(
    "tickets",
    limit=50,
    filter=[
        {"field": "status", "op": "eq", "value": "new"},
        {"field": "priority", "op": "ne", "value": "low"},
    ],
    sort=[{"field": "created_at", "direction": "desc"}]
)

# Raw SQL query
results = pod.query(
    "SELECT status, COUNT(*) as total FROM tickets GROUP BY status"
)
```

### Tables & Records (TypeScript)

```typescript
const tables = await client.tables.list();
const records = await client.records.list("tickets", { limit: 50 });

// Create record
const newRecord = await client.records.create("tickets", {
  title: "Bug report",
  status: "new"
});

// Update record
await client.records.update("tickets", recordId, { status: "resolved" });

// Delete record
await client.records.delete("tickets", recordId);
```

### Live Updates (TypeScript WebSocket)

```typescript
const handle = client.datastore.watchChanges({
  table: "tickets",
  onChange: (frame) => {
    // frame.operation: "insert" | "update" | "delete"
    console.log(frame.operation, frame.table_name, frame.record_id);
  },
  onStatus: (s) => console.log(s), // "connecting" | "open" | "reconnecting" | "closed"
  onReady: ({ since }) => console.log("Live, cursor:", since),
});

// Later: stop watching
handle.close();
```

## Files & Documents

### Python Files

```python
# Create folder
pod.files.create_folder("/reports", description="Generated reports")

# Upload file
pod.files.upload("/tmp/summary.md", directory_path="/reports")

# Search with RAG
hits = pod.files.search(
    "refund policy",
    scope_path="/knowledge",
    scope_mode="SUBTREE",  # SUBTREE or DIRECT
    search_method="HYBRID"  # TEXT, VECTOR, or HYBRID
)

# Download content
md = pod.files.download_markdown("/knowledge/policy.pdf")
raw = pod.files.download("/knowledge/policy.pdf")
```

### TypeScript Files

```typescript
import { useFiles, useFileSearch } from "lemma-sdk/react";

// List files in directory
const files = await client.files.list({ directoryPath: "/reports" });

// Upload file
await client.files.upload(file, { directoryPath: "/reports" });

// Search files
const searchResults = await client.files.search({
  query: "refund policy",
  scopePath: "/knowledge",
});
```

## Functions

### Python Functions

```python
from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod

class TriageInput(BaseModel):
    ticket_id: str

class TriageResult(BaseModel):
    status: str

async def triage_ticket(ctx: FunctionContext, data: TriageInput) -> TriageResult:
    pod = Pod.from_env()  # Auto-authenticated
    pod.table("tickets").update(data.ticket_id, {"status": "triaged"})
    return TriageResult(status="triaged")
```

**Run a function:**
```python
run = pod.functions.run("triage_ticket", {"ticket_id": "rec-1"}).to_dict()
# Access: run["status"], run["output_data"], run["logs"]
```

### TypeScript Functions

```typescript
const run = await client.functions.run("triage_ticket", {
  ticket_id: "rec-1"
});

// Poll for completion
const status = await client.functions.getRun(run.id);
```

## Agents & Conversations

### Python Agents

```python
# Get agent
agent = pod.agents.get("triage").to_dict()

# Create conversation and chat
conv = pod.conversations.create_for_agent("triage", title="Triage Session")
pod.conversations.send(str(conv.to_dict()["id"]), "Classify ticket rec-1")
```

### TypeScript Agents

```typescript
import { useConversations, useConversationMessages } from "lemma-sdk/react";

// Create conversation
const conversation = await client.conversations.create({
  agentName: "triage_agent",
  title: "Triage ticket ticket_123",
});

await client.conversations.messages.send(conversation.id, JSON.stringify({
  ticket_id: "ticket_123",
  prompt: "Triage this ticket."
}));

// Stream responses
const stream = client.conversations.messages.stream(conversation.id);
for await (const event of stream) {
  console.log(event);
}
```

## Workflows

### Python Workflows

```python
# Start workflow
wf_run = pod.workflows.create_run("nightly_review").to_dict()

# Handle human approval steps
pod.workflows.submit_form(
    wf_run["id"],
    node_id="<form_node>",
    inputs={"limit": 10}
)
```

### TypeScript Workflows

```typescript
import { useWorkflowRun } from "lemma-sdk/react";

// Start workflow
const workflow = useWorkflowRun({
  client,
  workflowName: "approve_ticket",
});

// Start with inputs
workflow.start({ ticket_id: "ticket_123" });

// Handle approvals
workflow.resume({ formNodeId: "approval_1", inputs: { approved: true } });

// Cancel or retry
workflow.cancel();
workflow.retry();
```

## React Integration (TypeScript)

```typescript
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  AuthGuard,
  useRecords,
  useRecordForm,
  useWorkflowRun,
} from "lemma-sdk/react";

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthGuard>
        <TicketList />
      </AuthGuard>
    </QueryClientProvider>
  );
}

function TicketList() {
  const records = useRecords({
    client,
    tableName: "tickets",
    limit: 25,
    sortBy: "created_at",
    order: "desc",
  });

  if (records.error) return <p>{records.error.message}</p>;

  return (
    <ul>
      {records.records.map((ticket) => (
        <li key={String(ticket.id)}>{String(ticket.title)}</li>
      ))}
    </ul>
  );
}
```

### React Registry Blocks (shadcn)

```bash
# Initialize shadcn registry
npx lemma-sdk init-shadcn

# Add UI blocks
npx shadcn@latest add @lemma/lemma-records-view
npx shadcn@latest add @lemma/lemma-record-form
npx shadcn@latest add @lemma/lemma-global-search
```

```typescript
import { LemmaRecordsView } from "@/components/lemma/lemma-records-view";
import { LemmaGlobalSearch } from "@/components/lemma/lemma-global-search";

// Basic records view
<LemmaRecordsView client={client} podId={podId} tableName="tickets" />;

// With custom configuration
<LemmaRecordsView
  client={client}
  podId={podId}
  tableName="deals"
  defaultView="list"
  chrome={{ search: true, filters: true, create: true }}
  hiddenFields={["id", "created_at"]}
  onCreateOptions={{ submitVia: "function", submitFunctionName: "create-deal" }}
/>;

// Global search with agent
<LemmaGlobalSearch
  client={client}
  podId={podId}
  tables={[{ tableName: "deals", label: "Deals", searchFields: ["name", "status"] }]}
  files={{ enabled: true }}
  agent={{ agentName: "sales-copilot", label: "Ask CRM" }}
/>;
```

## Connectors

### External API Integration

```python
# Discover operations
matches = pod.connectors.operations.search("workspace-gmail", "send email")
schema = pod.connectors.operations.get("workspace-gmail", "GMAIL_SEND_EMAIL")

# Execute connector action
result = pod.connectors.execute(
    "workspace-gmail",
    "GMAIL_SEND_EMAIL",
    {"recipient_email": "user@example.com", "subject": "Hi", "body": "..."}
).to_dict()["result"]
```

## Error Handling

### Python Errors

```python
from lemma_sdk import LemmaAPIError, LemmaConfigError

try:
    pod.records.get("tickets", "missing")
except LemmaAPIError as e:
    print(f"API Error: {e.status_code} - {e.code} - {e.message}")
except LemmaConfigError:
    print("Configuration error: missing token or pod ID")
```

### TypeScript Errors

```typescript
try {
  const record = await client.records.get("tickets", "missing");
} catch (error) {
  if (error instanceof LemmaAPIError) {
    console.error(`API Error: ${error.statusCode} - ${error.code}`);
  }
}
```

## Response Shapes

| Operation | Response |
|-----------|----------|
| `records.create/get/update` | Bare record object |
| `records.list`, `table.list` | `{items: [], total: N, limit: N, next_page_token: ...}` |
| `bulk_create/update/delete` | `{count: N}` |
| `query(sql)` | `{items: [], total: N}` |
| `connectors.execute` | `{result: ...}` |
| `functions.run` | `{status, output_data, logs}` |

## Best Practices

1. **Use context managers in Python** for automatic cleanup:
   ```python
   with Pod.from_env() as pod:
       # operations
   ```

2. **Handle pagination** for large datasets:
   ```python
   while True:
       page = pod.records.list("tickets", limit=100, page_token=token)
       process(page["items"])
       if not page.get("next_page_token"):
           break
   ```

3. **Use typed models** for better IDE support:
   ```python
   from lemma_sdk.models import Record, FunctionRun
   record: Record = pod.records.create("tickets", {"title": "Typed"})
   ```

4. **Implement WebSocket reconnection** for live updates:
   - Built-in retry with exponential backoff (500ms to 30s)
   - Pass `since` cursor to resume from last position

5. **Use functions for deterministic operations** - not agents
6. **Prefer React hooks** for reactive data in TypeScript
7. **Use registry blocks** for standard UI components