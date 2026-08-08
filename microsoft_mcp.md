# Microsoft Copilot Studio MCP Integration

## Epicenter AI-Assisted Pre-Registration and Eligibility Verification

- **Status:** Recommended integration guide
- **Project sources:** [PRD.md](./PRD.md), [design.md](./design.md), and [techStack.md](./techStack.md)
- **Platform:** Microsoft Copilot Studio
- **Last reviewed:** 8 August 2026

## 1. What “Copilot as an MCP” Means

Microsoft Copilot Studio is the **MCP client** in this architecture. Epicenter hosts the **MCP server** that exposes a small set of approved project capabilities as tools.

```text
Copilot Studio agent
        │
        │ authenticated MCP tool calls over HTTPS
        ▼
Epicenter MCP server: /mcp
        │
        ▼
Shared Python service layer
  ├── document extraction jobs
  ├── deterministic eligibility rules
  ├── queue and appointment lookups
  ├── Supabase Postgres + RLS
  └── append-only audit events
```

The MCP server is an additional transport into the same backend. It must not contain a second implementation of extraction, eligibility, queueing, authorization, or audit logic.

Copilot Studio currently supports **Streamable HTTP** for MCP. Do not build this integration using the older SSE transport, which Copilot Studio no longer supports. The deployed MCP URL should therefore be an HTTPS endpoint such as:

```text
https://api.epicenter.example/mcp
```

## 2. How This Project Uses MCP

MCP gives a Copilot Studio agent controlled access to Epicenter workflows. It demonstrates that the hackathon solution can be integrated into Microsoft's agent platform without rebuilding the core application in Copilot Studio.

### 2.1 Appropriate Copilot workflows

The agent may:

- look up the status of a document-extraction job;
- start extraction for an already-authorized document record;
- preview the deterministic eligibility result for a document and appointment;
- retrieve a masked patient or appointment summary for staff;
- retrieve queue, counter, and processing-stage information;
- list review cases using narrow filters and pagination;
- explain why a case is in FAST or REVIEW using stored rule results.

### 2.2 Actions that remain outside MCP for P0

Copilot must not:

- perform or infer identity or e-card verification;
- record the staff attestation for a manually completed identity/e-card check;
- confirm or correct extracted coverage facts;
- approve an eligibility or billing result;
- reveal a full NRIC;
- move a patient into FAST by overriding the prerequisite rule;
- submit a real payment or live TPA claim;
- fetch an arbitrary patient by an unscoped NRIC or email search;
- return source document binaries, signed storage URLs, or raw extracted document text.

These actions require the dedicated staff or patient UI, the applicable re-authentication step, and an auditable human confirmation. MCP never changes the P0 rule that actual identity/e-card checking is manual and the product stores confirmation only.

## 3. Recommended Initial Tools

Use project-prefixed, action-oriented tool names so the agent can distinguish them from tools supplied by other systems.

| Tool | Purpose | Mutation | Required app permission |
| --- | --- | --- | --- |
| `epicenter_get_extraction_status` | Return `queued`, `processing`, `ready`, or `failed` for one job | No | `epicenter:read` |
| `epicenter_start_document_extraction` | Create or return the active idempotent extraction job for an authorized document | Yes, idempotent | `epicenter:extract` |
| `epicenter_preview_eligibility` | Run/read the current deterministic appointment-scoped match without confirming it | No final state change | `epicenter:read` |
| `epicenter_get_queue_entry` | Return masked queue, counter, lifecycle, and last-updated information | No | `epicenter:read` |
| `epicenter_get_appointment_summary` | Return the prerequisite states and stored routing reason for one appointment | No | `epicenter:read` |
| `epicenter_list_review_cases` | Return a bounded, paginated list of staff review cases | No | `epicenter:read` |

Do not add a generic SQL tool, arbitrary patient search tool, file download tool, or catch-all `update_record` tool. Each MCP tool should represent one safe business workflow.

### 3.1 Tool response rules

Every tool should return a small typed result containing only what the agent needs. For example:

```json
{
  "queue_entry_id": "qe_01J...",
  "appointment_reference": "PS-REG-0417",
  "lifecycle": "incoming",
  "queue": "review",
  "queue_number": "R-006",
  "counter_number": 4,
  "reason_code": "missing_document",
  "updated_at": "2026-08-08T09:02:11+08:00"
}
```

Rules for all responses:

- return opaque IDs and masked identifiers, never a full NRIC;
- use enumerated status/reason codes rather than free-form model judgments;
- distinguish `not_found` from `not_authorized` without leaking whether another patient's record exists;
- cap list results and include a cursor when more rows are available;
- return the stored rule outcome and source version, not a Copilot-generated coverage decision;
- return an explicit `requires_staff_confirmation` flag where relevant;
- do not return raw document text unless a future, separately approved tool has a justified need.

### 3.2 MCP tool annotations

Declare tool behavior accurately:

- lookup/list tools: `readOnlyHint=true`, `destructiveHint=false`;
- start extraction: `readOnlyHint=false`, `destructiveHint=false`, `idempotentHint=true`;
- all initial tools: `openWorldHint=false`, because they operate only on Epicenter's backend.

Annotations help an agent plan, but they are not security controls. The server must enforce authorization for every call.

## 4. Server Implementation

### 4.1 Repository boundary

Use the backend layout proposed in `techStack.md`:

```text
backend/
├── api/                  # FastAPI routes for the web application
├── mcp/
│   ├── server.py         # MCP server and transport configuration
│   ├── tools/
│   │   ├── documents.py
│   │   ├── appointments.py
│   │   └── queue.py
│   └── auth.py           # Clerk token validation and app-permission mapping
├── worker/               # asynchronous document worker
└── core/                 # shared extraction, rules, queue, and audit services
```

Both FastAPI routes and MCP tools call `backend/core`. A tool declaration should validate input, establish the authorized actor, call one core service, and serialize the result.

### 4.2 Python MCP server skeleton

Use the official Python MCP SDK and pin the tested SDK version in the lockfile when implementation begins.

```python
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

from backend.core.queue import get_queue_entry_for_actor
from backend.mcp.auth import require_permission

mcp = FastMCP(
    "Epicenter",
    json_response=True,
)


class QueueEntryInput(BaseModel):
    queue_entry_id: str = Field(min_length=1, max_length=128)


@mcp.tool(
    name="epicenter_get_queue_entry",
    description=(
        "Get the masked queue and counter status for one authorized Epicenter "
        "queue entry. Use this for operational status, not clinical advice."
    ),
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def get_queue_entry(input: QueueEntryInput, context) -> dict:
    actor = await require_permission(context, "epicenter:read")
    result = await get_queue_entry_for_actor(
        actor=actor,
        queue_entry_id=input.queue_entry_id,
    )
    return result.model_dump(mode="json")


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
        streamable_http_path="/mcp",
    )
```

Treat this as an implementation shape, not a copy-paste dependency contract: confirm decorator/context signatures against the pinned SDK version. The official SDK defaults the Streamable HTTP path to `/mcp` and is designed to be mounted into an existing ASGI application if Epicenter later runs REST and MCP in one process.

### 4.3 Input and error handling

- Define Pydantic models with descriptions, bounds, enums, and formats.
- Reject unknown identifiers, oversized payloads, and unsupported filters before calling services.
- Require idempotency for job-starting tools so retries do not create duplicate extraction jobs.
- Use actionable but non-leaking errors such as `not_authorized_or_not_found`, `job_already_complete`, and `document_not_ready`.
- Apply timeouts around database and provider calls.
- Keep MCP payloads small; document files continue to move through private upload/storage flows, not through the agent context.

## 5. Authentication and Authorization

### 5.1 Recommended production setup with Clerk

Use Clerk as Epicenter's identity and OAuth authorization service. Copilot Studio's onboarding wizard supports OAuth 2.0 through dynamic discovery, dynamic registration, or manual configuration, and Clerk publishes OAuth authorization-server metadata and supports dynamic client registration.

For this project, prefer a **manually registered Clerk OAuth application** for Copilot Studio. Enter the callback URL supplied by Copilot Studio in the Clerk OAuth application and configure Copilot Studio with Clerk's client ID, client secret, authorization URL, token URL, refresh URL, and scopes.

Recommended Clerk OAuth scopes:

```text
openid profile email
```

Clerk does not currently offer general custom OAuth scopes. Therefore, `epicenter:read` and `epicenter:extract` in §3 are **Epicenter application permissions**, not OAuth scope strings. After validating Clerk's token, the MCP server maps its subject to a local staff/service actor and checks these permissions in Epicenter before every tool call.

The MCP server must validate the Clerk access token's issuer, audience, expiry, and signature. The web application also uses Clerk sessions. Supabase is configured to accept Clerk as a native third-party authentication provider, and RLS reads the Clerk subject from `auth.jwt()->>'sub'`; Supabase does not own Epicenter user credentials.

Clerk dynamic client registration can work with MCP clients and Copilot Studio's dynamic-discovery option, but enabling it creates a public client-registration endpoint. Keep it disabled unless the team has reviewed that risk, enabled consent, restricted default scopes, and established client-registration monitoring and cleanup.

### 5.2 Hackathon option

For synthetic demo data only, Copilot Studio also supports an API key sent in a named header. If used:

- keep the key in the Copilot connection, never in prompts, source control, or browser code;
- use a dedicated read/extract-only service identity;
- rotate the key after the demonstration;
- rate-limit it and audit every call;
- never expose the endpoint with `None` authentication.

Use OAuth rather than a shared API key for any real patient or healthcare data.

### 5.3 Authorization remains server-side

Copilot instructions and MCP annotations are guidance, not access control. Each tool call must enforce:

1. valid MCP connection identity;
2. required Epicenter application permission;
3. staff role or service-role permission;
4. appointment/patient/queue-record access;
5. RLS-compatible database access;
6. audit recording for tool calls and mutations.

The MCP server should use core services with an explicit actor context. It should not use a global Supabase service-role client that bypasses authorization checks.

## 6. Deployment

Deploy the MCP server with the FastAPI service on Railway as proposed in `techStack.md`. The REST API, `/mcp`, and `/healthz` may share one Railway web service because they use the same authorization and core service layer; the document worker is a second private Railway service.

Minimum deployment requirements:

- public HTTPS URL reachable by Copilot Studio;
- Streamable HTTP endpoint at `/mcp`;
- separate unauthenticated liveness endpoint such as `/healthz` that returns no patient data;
- authentication on every MCP request;
- secrets stored as Railway service variables, not in the image or repository;
- structured logs with correlation IDs and no raw NRIC, access tokens, document contents, or signed URLs;
- bounded request size, concurrency, timeout, and rate limits;
- a Railway health check against `/healthz`;
- an always-running service during the judged demo if sleep/cold-start behavior would be disruptive.

`localhost` is suitable for MCP Inspector testing but cannot be the final Copilot Studio server URL. Do not expose a temporary tunnel to real patient data.

## 7. Connect the Server to Copilot Studio

Microsoft's recommended route is the MCP onboarding wizard:

1. Deploy the API/MCP service to Railway, generate a public domain, and verify `https://<railway-domain>/mcp`.
2. Open the Copilot Studio agent.
3. Go to **Tools**.
4. Select **Add a tool**.
5. Select **New tool**.
6. Select **Model Context Protocol**.
7. Enter:
   - **Server name:** `Epicenter Pre-Registration`
   - **Server description:** `Retrieves authorized Epicenter appointment, document-processing, eligibility-preview, and queue information; can start idempotent document extraction jobs.`
   - **Server URL:** `https://<railway-domain>/mcp`
8. Choose the configured authentication type:
   - **OAuth 2.0** backed by Clerk for the intended implementation; or
   - **API key** for a synthetic-data hackathon demo only.
9. Create or select the connection.
10. Select **Add to agent**.
11. Confirm that Copilot Studio discovers only the approved tools in §3.
12. Add the agent instructions in §8 and run the acceptance tests in §10.

Copilot Studio also supports importing a Power Apps custom connector. Use that path only if the onboarding wizard cannot represent a required connection setting.

### 7.1 Custom connector fallback

The minimum connector shape documented by Microsoft is:

```yaml
swagger: '2.0'
info:
  title: Epicenter MCP
  description: Streamable MCP connection for Epicenter
  version: 1.0.0
host: api.epicenter.example
basePath: /
schemes:
  - https
paths:
  /mcp:
    post:
      summary: Epicenter Pre-Registration MCP Server
      x-ms-agentic-protocol: mcp-streamable-1.0
      operationId: InvokeMCP
      responses:
        '200':
          description: Success
```

Configure authentication in the connector rather than committing secrets to this schema. Access to the MCP server is also subject to the environment's Power Platform connector data policies.

## 8. Suggested Copilot Agent Instructions

Add instructions similar to the following to the Copilot Studio agent:

```text
Use Epicenter tools only for authorized operational pre-registration questions.
Never claim that identity, e-card, coverage, eligibility, or billing has been
approved unless the tool result explicitly reports a stored staff confirmation.

Treat eligibility previews as deterministic system results awaiting staff review.
Do not infer missing coverage details or convert low confidence into a pass.
Do not ask for or display a full NRIC, raw document text, or another patient's data.

FAST applies only when the appointment is booked, pre-registration was completed
before arrival, all required documents are present, valid, and high-confidence,
and every eligibility/package match is clean. Every other case, including every
walk-in, is REVIEW. Explain the stored reason code without criticizing the patient.

If a tool returns not_authorized_or_not_found, do not speculate whether the record
exists. Direct the staff member to the Epicenter staff interface.
```

These instructions improve orchestration and wording. Backend rules remain the source of truth.

## 9. Example Agent Flows

### 9.1 “Why is this patient in the review queue?”

1. Copilot calls `epicenter_get_appointment_summary` with the appointment reference.
2. The tool returns prerequisite booleans, `queue=review`, and `reason_code=missing_document`.
3. Copilot explains the stored reason and links/directs staff to the document-upload screen.
4. Copilot does not move the patient into FAST.

### 9.2 “Process the document that was just uploaded”

1. Copilot calls `epicenter_start_document_extraction` with the authorized document ID.
2. The service returns the existing or new job ID.
3. Copilot calls `epicenter_get_extraction_status` later rather than holding one long request open.
4. When ready, Copilot reports that the extraction is available for staff review; it does not call it approved.

### 9.3 “Where should the incoming patient go?”

1. Copilot calls `epicenter_get_queue_entry`.
2. The tool returns the expected queue/counter for Incoming or actual queue/counter for Ongoing.
3. Copilot states that an expected counter is a planning assignment and may change at check-in or during rebalancing.

### 9.4 “Is the reused Meridian document still valid?”

1. The patient has already selected **Yes, same coverage** in the scoped patient flow.
2. Copilot calls `epicenter_preview_eligibility` for the prior document and current appointment.
3. The core service re-runs current validity and eligibility rules.
4. Copilot reports the preview and `requires_staff_confirmation=true`; it never carries forward the old visit's approval.

## 10. Testing and Acceptance Checklist

### 10.1 Local server testing

```bash
uv add "mcp[cli]"
uv run mcp dev backend/mcp/server.py
```

Use MCP Inspector to verify tool discovery, schemas, responses, and errors. For a separately running Streamable HTTP server, connect the Inspector to:

```text
http://127.0.0.1:8000/mcp
```

### 10.2 Required acceptance tests

- [ ] `tools/list` exposes only the approved Epicenter tools.
- [ ] The deployed endpoint uses Streamable HTTP at `/mcp`, not SSE.
- [ ] Missing, expired, wrong-audience, and invalid Clerk credentials are rejected.
- [ ] A valid Clerk identity without the required Epicenter app permission is rejected.
- [ ] A staff/service actor cannot retrieve a record outside its authorized scope.
- [ ] Tool responses mask NRIC and omit raw extracted document text, document URLs, and tokens.
- [ ] Starting extraction twice returns the same active/completed job rather than duplicating work.
- [ ] Eligibility preview uses the versioned rules service and always indicates whether staff confirmation is pending.
- [ ] Queue responses preserve the strict FAST/REVIEW rule and place all walk-ins in REVIEW.
- [ ] Copilot cannot call manual-check confirmation, correction, billing approval, or NRIC-reveal actions.
- [ ] Every tool call has a correlation ID; mutations produce an audit event.
- [ ] Bounded list tools paginate and reject excessive limits.
- [ ] Copilot Studio discovers the server and calls each tool through the configured connection.
- [ ] Power Platform data policies permit the intended connector in the chosen environment.

## 11. Recommended Rollout

### Phase 1 — Hackathon integration

- Implement the six narrow tools in §3 against synthetic demo data.
- Prefer read-only tools; allow only idempotent extraction-job creation.
- Deploy the Streamable HTTP server with the FastAPI service on Railway.
- Connect it with OAuth if ready, otherwise a restricted demo API key.
- Demonstrate one appointment review, one extraction job, and one queue lookup from Copilot Studio.

### Phase 2 — Production hardening

- Complete Clerk OAuth identity mapping, consent, token validation, and least-privilege Epicenter permissions.
- Validate Power Platform data-loss-prevention policies with the clinic tenant.
- Add formal threat modelling, penetration testing, retention controls, and operational alerting.
- Evaluate narrowly scoped write tools only when they can provide the same re-authentication, confirmation, and audit guarantees as the staff UI.

## 12. Official References

- [Connect an existing MCP server to a Copilot Studio agent](https://learn.microsoft.com/en-us/microsoft-copilot-studio/mcp-add-existing-server-to-agent)
- [Official Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Running a Python MCP server](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/run/index.md)
- [MCP authorization specification](https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization)
- [Clerk OAuth implementation and dynamic client registration](https://clerk.com/docs/guides/configure/auth-strategies/oauth/how-clerk-implements-oauth)
- [Clerk MCP client connection guidance](https://clerk.com/docs/guides/ai/mcp/connect-mcp-client)
- [Clerk and Supabase integration](https://clerk.com/docs/guides/development/integrations/databases/supabase)
- [Clerk sensitive-action reverification](https://clerk.com/docs/guides/secure/reverification)
- [Deploy FastAPI on Railway](https://docs.railway.com/guides/fastapi)

Copilot Studio and MCP support evolve quickly. Recheck the Microsoft transport, authentication, connector, licensing, and tenant-policy documentation before deployment rather than treating this guide as a permanent platform contract.
