# TypeScript SDK Reference Examples

## Authentication Patterns

### 1. Browser (React/Next.js)

```typescript
import { LemmaClient } from "lemma-sdk";
import { AuthGuard } from "lemma-sdk/react";

// Create client
const client = new LemmaClient({
  podId: process.env.NEXT_PUBLIC_LEMMA_POD_ID,
  baseUrl: process.env.NEXT_PUBLIC_LEMMA_API_URL,
});

// Initialize on app load
await client.initialize();

// AuthGuard for protected routes
function App() {
  return (
    <AuthGuard
      loading={<LoadingSpinner />}
      unauthorized={<LoginPrompt />}
    >
      <Dashboard />
    </AuthGuard>
  );
}
```

### 2. Server-Side (Node.js)

```typescript
import { LemmaClient } from "lemma-sdk";

const client = new LemmaClient({
  podId: process.env.LEMMA_POD_ID,
  token: process.env.LEMMA_TOKEN, // Server-side token
  baseUrl: process.env.LEMMA_API_URL,
});

await client.initialize();
```

### 3. No-Build HTML (Browser Bundle)

```html
<!DOCTYPE html>
<html>
<head>
  <title>Lemma App</title>
</head>
<body>
  <h1>My Lemma App</h1>
  <div id="tickets"></div>

  <script src="https://api.lemma.work/public/sdk/lemma-client.js"></script>
  <script src="https://api.lemma.work/public/sdk/lemma-ui.js"></script>
  <script>
    // Client reads window.__LEMMA_CONFIG__ from host
    const client = new window.LemmaClient.LemmaClient();

    async function init() {
      const state = await client.initialize();

      if (state.status !== 'authenticated') {
        client.auth.redirectToAuth();
        return;
      }

      // Load tickets
      const tickets = await client.records.list('tickets', { limit: 50 });
      renderTickets(tickets.items);
    }

    function renderTickets(tickets) {
      const container = document.getElementById('tickets');
      container.innerHTML = tickets.map(t =>
        `<li>${t.title} - ${t.status}</li>`
      ).join('');
    }

    init();
  </script>
</body>
</html>
```

## React Integration

### Setup with TanStack Query

```typescript
// app/providers.tsx
"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode, useState } from "react";
import { LemmaClient } from "lemma-sdk";

export function LemmaProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

// Create client instance
export const lemmaClient = new LemmaClient({
  podId: process.env.NEXT_PUBLIC_LEMMA_POD_ID,
});

// Hook to access client
export function useLemmaClient() {
  return lemmaClient;
}
```

### Records with React Hooks

```typescript
import { useRecords, useRecordCreate, useRecordUpdate } from "lemma-sdk/react";
import { useLemmaClient } from "@/app/providers";
import { useState } from "react";

export function TicketList() {
  const client = useLemmaClient();
  const [filter, setFilter] = useState<"all" | "open" | "closed">("all");

  const records = useRecords({
    client,
    tableName: "tickets",
    limit: 25,
    sortBy: "created_at",
    order: "desc",
    filter: filter === "all"
      ? undefined
      : [{ field: "status", op: "eq", value: filter }],
  });

  if (records.isLoading) return <Spinner />;
  if (records.error) return <ErrorMessage error={records.error} />;

  return (
    <div>
      <FilterTabs filter={filter} onChange={setFilter} />
      <ul>
        {records.records.map((ticket) => (
          <TicketItem key={ticket.id} ticket={ticket} />
        ))}
      </ul>
      {records.hasNextPage && (
        <button onClick={() => records.loadMore()}>Load more</button>
      )}
    </div>
  );
}

function TicketItem({ ticket }: { ticket: Record<string, any> }) {
  const client = useLemmaClient();
  const updateRecord = useRecordUpdate(client);

  const handleStatusChange = async (newStatus: string) => {
    await updateRecord.mutateAsync({
      tableName: "tickets",
      id: ticket.id,
      payload: { status: newStatus },
    });
  };

  return (
    <li>
      <span>{ticket.title}</span>
      <select
        value={ticket.status}
        onChange={(e) => handleStatusChange(e.target.value)}
      >
        <option value="new">New</option>
        <option value="open">Open</option>
        <option value="resolved">Resolved</option>
      </select>
    </li>
  );
}
```

### Record Form

```typescript
import { useRecordForm, useRecordCreate } from "lemma-sdk/react";
import { useLemmaClient } from "@/app/providers";
import { useState } from "react";

export function CreateTicketForm() {
  const client = useLemmaClient();
  const createRecord = useRecordCreate(client);
  const [isOpen, setIsOpen] = useState(false);

  const form = useRecordForm({
    client,
    tableName: "tickets",
    mode: "create",
  });

  const handleSubmit = async (data: Record<string, any>) => {
    try {
      await createRecord.mutateAsync({
        tableName: "tickets",
        payload: data,
      });
      setIsOpen(false);
    } catch (error) {
      console.error("Failed to create ticket:", error);
    }
  };

  if (!isOpen) {
    return <button onClick={() => setIsOpen(true)}>Create Ticket</button>;
  }

  return (
    <form onSubmit={form.handleSubmit(handleSubmit)}>
      {form.schemaFields.map((field) => (
        <FormField key={field.name} field={field} form={form} />
      ))}
      <div className="form-actions">
        <button type="submit" disabled={createRecord.isPending}>
          {createRecord.isPending ? "Creating..." : "Create"}
        </button>
        <button type="button" onClick={() => setIsOpen(false)}>
          Cancel
        </button>
      </div>
    </form>
  );
}

function FormField({ field, form }: { field: any; form: any }) {
  const { register, formState: { errors } } = form;

  if (field.type === "enum") {
    return (
      <div>
        <label>{field.label}</label>
        <select {...register(field.name)}>
          <option value="">Select...</option>
          {field.options.map((opt: string) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
        {errors[field.name] && <span>{errors[field.name].message}</span>}
      </div>
    );
  }

  return (
    <div>
      <label>{field.label}</label>
      <input
        {...register(field.name)}
        type={field.type === "number" ? "number" : "text"}
      />
      {errors[field.name] && <span>{errors[field.name].message}</span>}
    </div>
  );
}
```

## Live Updates (WebSocket)

```typescript
import { useEffect } from "react";
import { useLemmaClient } from "@/app/providers";
import { useQueryClient } from "@tanstack/react-query";

// Hook for live record updates
export function useLiveRecords(tableName: string) {
  const client = useLemmaClient();
  const queryClient = useQueryClient();

  useEffect(() => {
    const handle = client.datastore.watchChanges({
      table: tableName,
      onChange: (frame) => {
        // Invalidate query to trigger refetch
        queryClient.invalidateQueries({
          queryKey: ["records", tableName],
        });

        console.log(`${frame.operation} on ${frame.table_name}:`, frame.record_id);
      },
      onStatus: (status) => {
        console.log("WebSocket status:", status);
      },
      onError: (error) => {
        console.error("WebSocket error:", error);
      },
    });

    return () => handle.close();
  }, [client, tableName, queryClient]);

  return client;
}

// Component example
export function LiveTicketFeed() {
  const client = useLiveRecords("tickets");
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    const handle = client.datastore.watchChanges({
      table: "tickets",
      onChange: (frame) => {
        setEvents((prev) => [
          { ...frame, timestamp: new Date() },
          ...prev.slice(0, 99), // Keep last 100
        ]);
      },
    });

    return () => handle.close();
  }, [client]);

  return (
    <div className="feed">
      {events.map((event, i) => (
        <div key={i} className="event">
          <span className="operation">{event.operation}</span>
          <span className="record">{event.record_id}</span>
          <span className="time">{event.timestamp.toLocaleTimeString()}</span>
        </div>
      ))}
    </div>
  );
}
```

## Agents & Conversations

### Conversation UI

```typescript
import {
  useConversations,
  useConversationMessages,
  useAssistantController,
} from "lemma-sdk/react";
import { useLemmaClient } from "@/app/providers";
import { useState, useRef, useEffect } from "react";

export function AgentChat() {
  const client = useLemmaClient();
  const [input, setInput] = useState("");

  const conversations = useConversations({
    client,
    agentName: "support_agent",
  });

  const messages = useConversationMessages({
    client,
    conversationId: conversations.effectiveSelectedConversationId,
    autoResume: true,
  });

  const handleSend = async () => {
    if (!input.trim()) return;

    const conversationId = conversations.effectiveSelectedConversationId
      || (await conversations.createConversation({
          title: `Chat ${new Date().toLocaleString()}`,
        })).id;

    await messages.sendMessage(input, { conversationId });
    setInput("");
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.items.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}
        {messages.isStreaming && <StreamingIndicator />}
      </div>

      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask the support agent..."
        />
        <button onClick={handleSend} disabled={messages.isStreaming}>
          Send
        </button>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: any }) {
  const isUser = message.role === "user";

  return (
    <div className={`message ${isUser ? "user" : "assistant"}`}>
      {message.kind === "thinking" ? (
        <span className="thinking">{message.text}</span>
      ) : message.kind === "tool_call" ? (
        <span className="tool-call">
          Using tool: {message.tool_name}
        </span>
      ) : (
        <span className="text">{message.text}</span>
      )}
    </div>
  );
}
```

### Streaming with Assistant Controller

```typescript
import { useAssistantController } from "lemma-sdk/react";
import { useLemmaClient } from "@/app/providers";

export function StreamingAgent() {
  const client = useLemmaClient();

  const controller = useAssistantController({
    client,
    agentName: "code_assistant",
    onText: (text) => {
      // Append streaming text
      console.log("Streaming:", text);
    },
    onToolCall: (tool, args) => {
      console.log("Tool call:", tool, args);
    },
    onToolReturn: (tool, result) => {
      console.log("Tool result:", tool, result);
    },
    onComplete: (output) => {
      console.log("Complete:", output);
    },
  });

  const handleSubmit = async (prompt: string) => {
    const conversation = await client.conversations.create({
      agentName: "code_assistant",
      title: "Code Review",
    });

    controller.start(conversation.id, prompt);
  };

  return (
    <div>
      <button onClick={() => handleSubmit("Review my code")}>
        Start Code Review
      </button>
      <button onClick={() => controller.cancel()}>Cancel</button>
    </div>
  );
}
```

## Workflows

### Workflow Runner Component

```typescript
import { useWorkflowRun, useWorkflowRuns } from "lemma-sdk/react";
import { useLemmaClient } from "@/app/providers";

export function WorkflowRunner() {
  const client = useLemmaClient();

  const workflow = useWorkflowRun({
    client,
    workflowName: "approve_ticket",
  });

  const handleStart = () => {
    workflow.start({
      ticket_id: "ticket_123",
      approver_email: "manager@example.com",
    });
  };

  return (
    <div className="workflow-runner">
      <h3>Ticket Approval Workflow</h3>

      <div className="status">
        Status: {workflow.status || "idle"}
      </div>

      {workflow.isPolling && (
        <div className="progress">
          <Spinner /> Processing...
        </div>
      )}

      {workflow.status === "waiting" && workflow.waitInfo && (
        <div className="approval-needed">
          <p>Waiting for approval from {workflow.waitInfo.assignee}</p>
          {workflow.waitInfo.formFields?.map((field) => (
            <ApprovalField key={field.name} field={field} workflow={workflow} />
          ))}
        </div>
      )}

      {workflow.output && (
        <div className="output">
          <h4>Result</h4>
          <pre>{JSON.stringify(workflow.output, null, 2)}</pre>
        </div>
      )}

      <div className="actions">
        {workflow.status === "idle" && (
          <button onClick={handleStart}>Start Approval</button>
        )}
        {workflow.status === "waiting" && workflow.waitInfo && (
          <button onClick={() => workflow.resume({ approved: true })}>
            Approve
          </button>
        )}
        {workflow.isRunning && (
          <button onClick={() => workflow.cancel()}>Cancel</button>
        )}
        {(workflow.status === "failed" || workflow.status === "cancelled") && (
          <button onClick={() => workflow.retry()}>Retry</button>
        )}
      </div>
    </div>
  );
}

function ApprovalField({ field, workflow }: { field: any; workflow: any }) {
  const [value, setValue] = useState("");

  return (
    <div>
      <label>{field.label}</label>
      {field.type === "boolean" ? (
        <input
          type="checkbox"
          checked={value}
          onChange={(e) => setValue(e.target.checked)}
        />
      ) : (
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
        />
      )}
    </div>
  );
}
```

### Workflow History

```typescript
import { useWorkflowRuns } from "lemma-sdk/react";
import { useLemmaClient } from "@/app/providers";

export function WorkflowHistory() {
  const client = useLemmaClient();

  const runs = useWorkflowRuns({
    client,
    workflowName: "onboarding_flow",
    limit: 20,
  });

  if (runs.isLoading) return <Spinner />;

  return (
    <div className="workflow-history">
      <h3>Recent Workflow Runs</h3>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Started</th>
            <th>Status</th>
            <th>Duration</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {runs.runs.map((run) => (
            <tr key={run.id}>
              <td>{run.id.slice(0, 8)}...</td>
              <td>{new Date(run.created_at).toLocaleString()}</td>
              <td>
                <span className={`status ${run.status}`}>
                  {run.status}
                </span>
              </td>
              <td>
                {run.completed_at
                  ? `${(new Date(run.completed_at).getTime() - new Date(run.created_at).getTime()) / 1000}s`
                  : "-"}
              </td>
              <td>
                <button onClick={() => runs.refresh()}>Refresh</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

## Files

### File Browser

```typescript
import { useFiles, useFileUpload, useFileSearch } from "lemma-sdk/react";
import { useLemmaClient } from "@/app/providers";
import { useState } from "react";

export function FileBrowser() {
  const client = useLemmaClient();
  const [currentPath, setCurrentPath] = useState("/");
  const [searchQuery, setSearchQuery] = useState("");

  const files = useFiles({
    client,
    directoryPath: currentPath,
  });

  const search = useFileSearch({
    client,
    query: searchQuery,
    scopePath: currentPath,
    enabled: searchQuery.length > 2,
  });

  const upload = useFileUpload(client);

  const handleFileUpload = async (file: File) => {
    await upload.mutateAsync({
      file,
      directoryPath: currentPath,
    });
    files.refresh();
  };

  const displayItems = searchQuery.length > 2 ? search.files : files.files;

  return (
    <div className="file-browser">
      <div className="toolbar">
        <input
          type="text"
          placeholder="Search files..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <input
          type="file"
          onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
        />
      </div>

      <div className="breadcrumb">
        {currentPath.split("/").filter(Boolean).map((part, i, arr) => (
          <span key={i}>
            <button onClick={() => setCurrentPath("/" + arr.slice(0, i + 1).join("/"))}>
              {part}
            </button>
            {i < arr.length - 1 && " / "}
          </span>
        ))}
      </div>

      <div className="file-list">
        {displayItems.map((item) => (
          <div
            key={item.path}
            className={`file-item ${item.type === "directory" ? "folder" : "file"}`}
            onClick={() => item.type === "directory" && setCurrentPath(item.path)}
          >
            <span className="icon">{item.type === "directory" ? "📁" : "📄"}</span>
            <span className="name">{item.name}</span>
            <span className="size">{item.size}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Registry Blocks (shadcn)

### Records View with Customization

```typescript
import { LemmaRecordsView } from "@/components/lemma/lemma-records-view";
import { LemmaGlobalSearch } from "@/components/lemma/lemma-global-search";
import { LemmaDetailPanel } from "@/components/lemma/lemma-detail-panel";
import { useState } from "react";

export function CRMView() {
  const [selectedRecord, setSelectedRecord] = useState<string | null>(null);
  const [view, setView] = useState<"list" | "grid">("list");

  return (
    <div className="crm-layout">
      <aside className="sidebar">
        <LemmaGlobalSearch
          client={client}
          podId={podId}
          tables={[
            {
              tableName: "contacts",
              label: "Contacts",
              searchFields: ["name", "email", "company"],
              displayField: "name",
              subtitleField: "company",
              href: (record) => `/contacts?id=${record.id}`,
            },
            {
              tableName: "deals",
              label: "Deals",
              searchFields: ["title", "status", "value"],
              displayField: "title",
              subtitleField: "status",
              href: (record) => `/deals?id=${record.id}`,
            },
          ]}
          files={{ enabled: true }}
          agent={{ agentName: "crm_assistant", label: "Ask CRM" }}
        />
      </aside>

      <main className="content">
        <LemmaRecordsView
          client={client}
          podId={podId}
          tableName="deals"
          defaultView={view}
          availableViews={["list", "grid", "kanban"]}
          chrome={{
            search: true,
            filters: true,
            create: true,
            viewSwitcher: true,
            selection: true,
            export: true,
          }}
          hiddenFields={["id", "created_at", "updated_at", "owner_id"]}
          foreignKeyLabels={{
            company_id: "name",
            contact_id: "name",
          }}
          onRecordClick={(record) => setSelectedRecord(record.id)}
          onCreateOptions={{
            submitVia: "function",
            submitFunctionName: "create-deal",
          }}
        />
      </main>

      {selectedRecord && (
        <LemmaDetailPanel
          client={client}
          podId={podId}
          tableName="deals"
          recordId={selectedRecord}
          onClose={() => setSelectedRecord(null)}
          tabs={["details", "activity", "files"]}
        />
      )}
    </div>
  );
}
```

### Assistant Experience

```typescript
import { LemmaAssistantExperience } from "@/components/lemma/assistant/assistant-experience";

export function AssistantPage() {
  return (
    <div className="assistant-page">
      <LemmaAssistantExperience
        client={client}
        agentName="support_copilot"
        title="Support Assistant"
        description="Ask questions about tickets, customers, and workflows"
        quickActions={[
          {
            label: "Show open tickets",
            action: "Show me all open support tickets sorted by priority",
          },
          {
            label: "Escalate ticket",
            action: "Help me escalate a ticket to the engineering team",
          },
          {
            label: "Generate report",
            action: "Create a weekly support summary report",
          },
        ]}
        suggestions={{
          enabled: true,
          maxSuggestions: 5,
        }}
      />
    </div>
  );
}
```

## Error Handling

```typescript
import { LemmaClient, LemmaAPIError } from "lemma-sdk";

async function robustOperation() {
  try {
    const record = await client.records.get("tickets", "rec_123");
    return record;
  } catch (error) {
    if (error instanceof LemmaAPIError) {
      switch (error.statusCode) {
        case 400:
          console.error("Bad request:", error.message);
          break;
        case 401:
          // Redirect to login
          client.auth.redirectToAuth();
          break;
        case 403:
          console.error("Forbidden:", error.message);
          break;
        case 404:
          console.error("Not found:", error.message);
          return null;
        case 429:
          console.error("Rate limited, retry after:", error.retryAfter);
          // Wait and retry
          await new Promise(r => setTimeout(r, error.retryAfter * 1000));
          return robustOperation();
        default:
          console.error("API error:", error.statusCode, error.code, error.message);
      }
    }
    throw error;
  }
}

// Custom error class
class LemmaError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public code?: string,
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = "LemmaError";
  }
}

// Wrapper function
async function withLemmaError<T>(
  operation: () => Promise<T>,
  fallback: T
): Promise<T> {
  try {
    return await operation();
  } catch (error) {
    if (error instanceof LemmaAPIError) {
      console.error(`Lemma API Error: ${error.statusCode} - ${error.code}`);
      return fallback;
    }
    throw error;
  }
}

// Usage
const record = await withLemmaError(
  () => client.records.get("tickets", "rec_123"),
  null
);
```

## Advanced Patterns

### Custom Hook for Optimistic Updates

```typescript
import { useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useRecordUpdate } from "lemma-sdk/react";
import { useLemmaClient } from "@/providers";

export function useOptimisticUpdate(tableName: string) {
  const client = useLemmaClient();
  const queryClient = useQueryClient();
  const updateRecord = useRecordUpdate(client);

  const optimisticUpdate = useCallback(
    async (recordId: string, updates: Record<string, any>) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({
        queryKey: ["records", tableName],
      });

      // Snapshot previous value
      const previousData = queryClient.getQueryData(["records", tableName]);

      // Optimistically update
      queryClient.setQueryData(["records", tableName], (old: any) => ({
        ...old,
        items: old.items.map((item: any) =>
          item.id === recordId ? { ...item, ...updates } : item
        ),
      }));

      try {
        // Perform actual update
        await updateRecord.mutateAsync({
          tableName,
          id: recordId,
          payload: updates,
        });
      } catch (error) {
        // Rollback on error
        queryClient.setQueryData(["records", tableName], previousData);
        throw error;
      }
    },
    [client, queryClient, updateRecord, tableName]
  );

  return optimisticUpdate;
}

// Usage
function TicketStatusToggle({ ticket }) {
  const updateStatus = useOptimisticUpdate("tickets");

  const toggleStatus = async () => {
    const newStatus = ticket.status === "open" ? "closed" : "open";
    await updateStatus(ticket.id, { status: newStatus });
  };

  return (
    <button onClick={toggleStatus}>
      {ticket.status === "open" ? "Close" : "Reopen"}
    </button>
  );
}
```

### Infinite Scroll for Records

```typescript
import { useInfiniteQuery } from "@tanstack/react-query";
import { useLemmaClient } from "@/providers";

export function useInfiniteRecords(tableName: string, options?: any) {
  const client = useLemmaClient();

  return useInfiniteQuery({
    queryKey: ["records", tableName, options],
    queryFn: async ({ pageParam }) => {
      const response = await client.records.list(tableName, {
        limit: 25,
        pageToken: pageParam,
        ...options,
      });
      return response;
    },
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => lastPage.next_page_token,
  });
}

// Component
function InfiniteTicketList() {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
  } = useInfiniteRecords("tickets");

  if (isLoading) return <Spinner />;

  const tickets = data?.pages.flatMap((page) => page.items) ?? [];

  return (
    <div>
      {tickets.map((ticket) => (
        <TicketItem key={ticket.id} ticket={ticket} />
      ))}

      <button
        onClick={() => fetchNextPage()}
        disabled={!hasNextPage || isFetchingNextPage}
      >
        {isFetchingNextPage
          ? "Loading more..."
          : hasNextPage
          ? "Load more"
          : "Nothing more to load"}
      </button>
    </div>
  );
}
```