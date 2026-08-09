# Microsoft MCP Integration Plan

## Epicenter Pre-Registration, Clinic Operations, and Simulation

- **Status:** Recommended integration guide
- **Project sources:** [PRD.md](./PRD.md), [design.md](./design.md), [techStack.md](./techStack.md), and [simulator.md](./simulator.md)
- **Primary host:** Microsoft Copilot Studio
- **Last reviewed:** 9 August 2026

## 1. Integration Principle

Use a first-party Microsoft MCP server when it already owns the required Microsoft capability. Use the custom Epicenter MCP server only for Epicenter-specific business operations that Microsoft services cannot safely infer or implement.

```text
Copilot Studio agent
   ├── Epicenter MCP
   │     Queue/readiness, document jobs, deterministic eligibility,
   │     operational summaries, allocation advice, and simulation
   │
   ├── Microsoft Learn MCP
   │     Current public Microsoft product documentation
   │
   ├── Power BI / Fabric MCP (optional P1, preview)
   │     Aggregate operational analytics and semantic-model queries
   │
   └── Dataverse MCP (optional deployment profile, preview)
         Dataverse records only if Dataverse becomes authoritative
```

MCP is not a reason to duplicate data or bypass the product's service layer. Epicenter's custom MCP endpoint is another transport into the same core services used by FastAPI and the web interface.

```text
Copilot Studio → HTTPS /mcp → Epicenter authorization
                              → shared core services
                                 ├── document jobs
                                 ├── readiness state machine
                                 ├── deterministic eligibility rules
                                 ├── operational-event aggregates
                                 ├── allocation advisor
                                 └── synthetic simulator
```

Copilot Studio supports MCP tools and resources through Streamable HTTP. It no longer supports the deprecated SSE transport. Generative orchestration must be enabled for the agent to select MCP tools dynamically.

## 2. Microsoft MCP Selection Matrix

| MCP server | Epicenter use | Phase | Decision |
| --- | --- | --- | --- |
| **Epicenter custom MCP** | Safe access to project-specific queue, readiness, eligibility, operational, allocation, and simulation services | P0 | Required; no first-party MCP implements this domain logic |
| **Microsoft Learn MCP** | Retrieve current Microsoft documentation while developing/configuring Copilot Studio, Power Platform, Fabric, Power BI, or Azure | P0 development | Use in the maker/developer agent, not the staff operations agent |
| **Microsoft Dataverse MCP Server** | Natural-language access to Dataverse tables if a Microsoft-native deployment selects Dataverse as an authoritative store | P1 option; preview | Do not add merely to mirror Supabase data |
| **Power BI remote MCP Server** | Query a de-identified aggregate Epicenter semantic model for operational insights | P1 option; preview | Strong fit for the Intelligence Loop after tenant/licensing/security validation |
| **Fabric Core MCP Server** | Manage or inspect Fabric workspaces/items that host the aggregate analytics pipeline | P1 development/admin; preview | Keep out of the patient/staff operations agent |
| **Azure MCP Server** | Developer/operations access to Azure resources, logs, storage, or App Service if an Azure deployment is adopted | Deployment-dependent | Internal development/operations only; current Railway/Supabase baseline gains little from it |

### 2.1 Why not connect everything to one agent?

Each connected MCP server expands the agent's tool surface and data boundary. Copilot Studio enables all tools from a newly added MCP server by default. For every server:

1. turn off **Allow all**;
2. enable only the required tools;
3. keep newly discovered tools disabled by default;
4. separate staff operations, analytics, and developer/admin agents; and
5. apply Power Platform data policies before testing with anything beyond synthetic data.

The staff operations agent should normally connect only to the Epicenter MCP. Microsoft Learn, Fabric Core, Azure, and model-authoring tools belong in maker/developer or administrator contexts.

## 3. Epicenter MCP Responsibilities

The custom server owns only Epicenter workflows. It must never expose generic database, filesystem, or cloud-administration access.

### 3.1 Allowed operational workflows

The staff agent may:

- retrieve a masked appointment and readiness summary;
- retrieve the one persistent `Q-*` ticket and current lifecycle state;
- list unresolved assisted-review cases with bounded filters;
- start an idempotent extraction job for an already-authorized document record;
- retrieve extraction-job status;
- preview the deterministic appointment-scoped eligibility result;
- retrieve aggregate operational measures for an authorized clinic/date range;
- retrieve a stored allocation recommendation, its evidence, constraints, status, and expiry; and
- explain stored states and reason codes without inventing coverage or clinical conclusions.

### 3.2 Allowed synthetic simulator workflows

The demo agent may:

- list versioned simulator scenarios;
- run a deterministic synthetic scenario with a permitted seed/configuration;
- retrieve a run's event-derived summary;
- compare baseline and Epicenter runs that share arrivals and sampled service times; and
- explain a simulated allocation recommendation and its simulated outcome.

Simulation responses must always contain `synthetic=true` and the scenario, seed, assumptions version, and policy version. They must never read or write production operational tables.

### 3.3 Actions outside MCP for P0

Copilot must not:

- perform, infer, or record identity/e-card verification;
- confirm or correct extracted coverage facts;
- approve an eligibility or billing result;
- mark a patient `ready` or override a readiness gate;
- issue, replace, or reset a patient ticket;
- approve, modify, apply, or reverse a real staff/counter allocation;
- rank clinical urgency, recommend care, or allocate unqualified staff;
- reveal a full NRIC/FIN/passport identifier;
- submit a real payment or TPA claim;
- perform an arbitrary NRIC/email patient search; or
- return source-document binaries, signed URLs, raw document text, credentials, or connection strings.

Human approval remains in the dedicated UI because it requires explicit review, role checks, re-authentication where applicable, transactional writes, and an immutable audit event. Copilot may direct an authorized staff member to that screen.

## 4. Epicenter MCP Tool Catalogue

Use project-prefixed, action-oriented names. Group tools so Copilot Studio can enable only the subset needed by each agent.

### 4.1 Core P0 tools

| Tool | Purpose | Mutation | App permission |
| --- | --- | --- | --- |
| `epicenter_get_extraction_status` | Return the state of one authorized extraction job | No | `epicenter:read` |
| `epicenter_start_document_extraction` | Create or return the active idempotent extraction job | Yes, idempotent | `epicenter:extract` |
| `epicenter_preview_eligibility` | Run/read the deterministic appointment-scoped match without confirming it | No final state change | `epicenter:read` |
| `epicenter_get_visit_ticket` | Return the one ticket, lifecycle, readiness, counter, waiting age, and update time | No | `epicenter:read` |
| `epicenter_get_appointment_summary` | Return prerequisite states and stored readiness reason | No | `epicenter:read` |
| `epicenter_list_review_cases` | Return a bounded assisted-review worklist | No | `epicenter:read` |

### 4.2 Intelligence and allocation tools

| Tool | Purpose | Mutation | App permission |
| --- | --- | --- | --- |
| `epicenter_get_operational_summary` | Return aggregate P50/P90 waits, readiness, stage pressure, utilisation, and fairness measures | No | `epicenter:operations_read` |
| `epicenter_list_allocation_recommendations` | List bounded, current recommendations for an authorized clinic/date | No | `epicenter:operations_read` |
| `epicenter_get_allocation_recommendation` | Return evidence, constraints checked, no-change baseline, expected effect, decision state, and expiry | No | `epicenter:operations_read` |

These tools never approve or apply an allocation. The response may identify a configured staff/resource ID only when the caller is authorized; patient-facing agents must not receive staff-allocation details.

### 4.3 Synthetic simulator tools

| Tool | Purpose | Mutation | App permission |
| --- | --- | --- | --- |
| `epicenter_list_simulation_scenarios` | List approved versioned synthetic scenarios and configurable fields | No | `epicenter:simulate` |
| `epicenter_run_simulation` | Run or return an idempotent deterministic simulation for a scenario/seed/config hash | Synthetic only | `epicenter:simulate` |
| `epicenter_get_simulation_run` | Return run state, assumptions, metrics, and safe event-summary references | No | `epicenter:simulate` |
| `epicenter_compare_simulation_runs` | Compare compatible baseline/Epicenter runs and flag invalid comparisons | No | `epicenter:simulate` |

Do not pass arbitrary executable policies or code through a simulation tool. Accept only a validated scenario ID plus bounded overrides defined by [simulator.md](./simulator.md).

## 5. Tool Contracts

### 5.1 Visit ticket response

```json
{
  "ticket_id": "qe_01J...",
  "appointment_reference": "APT-DEMO-0417",
  "ticket_number": "Q-015",
  "visit_status": "ongoing",
  "readiness_state": "needs_review",
  "readiness_reason": "missing_document",
  "counter_number": 4,
  "waiting_since": "2026-08-09T09:15:00+08:00",
  "waiting_age_seconds": 780,
  "updated_at": "2026-08-09T09:28:00+08:00",
  "requires_staff_action": true
}
```

`processing`, `ready`, and `needs_review` are states on one ticket. Tool text and agent instructions must never describe them as separate patient queues or tell a patient to take another number.

### 5.2 Allocation recommendation response

```json
{
  "recommendation_id": "ar_01J...",
  "status": "pending",
  "pressured_stage": "assisted_review",
  "observed_pressure": {
    "oldest_wait_seconds": 1080,
    "estimated_staff_minutes": 42
  },
  "recommended_change": {
    "resource_type": "flexible_counter",
    "resource_reference": "counter_2",
    "target_workstream": "review",
    "duration_minutes": 30
  },
  "constraints": {
    "role_and_skill": "pass",
    "minimum_coverage": "pass",
    "planned_break": "pass",
    "stability_window": "pass",
    "reassignment_frequency": "pass"
  },
  "expected_effect": {
    "review_p90_delta_seconds": -360
  },
  "expires_at": "2026-08-09T09:35:00+08:00",
  "approval_url": "/staff/counters/recommendations/ar_01J..."
}
```

The URL is an application route, not a signed credential. The tool never returns an action token and never treats the recommendation as approved.

### 5.3 Simulation comparison response

```json
{
  "synthetic": true,
  "comparison_valid": true,
  "shared_seed": 20260809,
  "assumptions_version": "demo-v1",
  "baseline_run_id": "sim_base_01J...",
  "epicenter_run_id": "sim_epic_01J...",
  "differences": {
    "throughput_per_hour": 4.5,
    "admin_wait_p90_seconds": -510,
    "walk_in_fairness_gap_seconds": -180,
    "reassignments_per_hour": 0.5
  },
  "disclaimer": "Synthetic scenario output; not an observed clinic result."
}
```

### 5.4 Rules for every response

- return opaque IDs and masked display references;
- use enumerated states/reasons, not model-generated judgments;
- cap lists and provide cursors;
- distinguish `not_authorized_or_not_found` without leaking record existence;
- include `updated_at`, source/rule version, and `requires_staff_confirmation` where relevant;
- label simulated and estimated values explicitly;
- never return raw patient documents or direct identifiers; and
- return a stable error code plus a safe recovery action.

### 5.5 MCP annotations

- lookup/list/compare tools: `readOnlyHint=true`, `destructiveHint=false`;
- extraction start: `readOnlyHint=false`, `destructiveHint=false`, `idempotentHint=true`;
- simulation run: `readOnlyHint=false`, `destructiveHint=false`, `idempotentHint=true`;
- every Epicenter tool: `openWorldHint=false`.

Annotations guide orchestration but are not authorization controls.

## 6. Server Implementation

### 6.1 Repository boundary

```text
backend/
├── api/                       # FastAPI web routes
├── mcp/
│   ├── server.py              # Streamable HTTP MCP endpoint
│   ├── auth.py                # token and app-permission mapping
│   └── tools/
│       ├── documents.py
│       ├── appointments.py
│       ├── operations.py
│       └── simulator.py
├── worker/                    # asynchronous document worker
└── core/
    ├── extraction/
    ├── eligibility/
    ├── queue/
    ├── operations/
    ├── allocation/
    └── simulation/            # or adapter to packages/simulation-core
```

FastAPI, MCP, and the simulator UI call the same core contracts. MCP declarations validate input, establish an authorized actor, call one service, and serialize a minimal typed result. No tool contains its own eligibility, readiness, allocation, or simulation algorithm.

### 6.2 Transport

Use the official MCP SDK and pin the tested version when implementation begins. Serve Streamable HTTP over HTTPS at:

```text
https://api.epicenter.example/mcp
```

The endpoint may be mounted in the existing ASGI service. Keep `/healthz` separate and free of patient data. `localhost` is suitable for MCP Inspector only.

### 6.3 Input, idempotency, and errors

- Define bounded Pydantic schemas with descriptions and enums.
- Reject unknown fields, excessive list limits, unsupported filters, and unapproved simulator overrides.
- Key extraction jobs by authorized document ID and idempotency key.
- Key simulation runs by scenario version, seed, policy version, and normalized configuration hash.
- Apply timeouts around storage, database, and model-provider calls.
- Return non-leaking errors such as `not_authorized_or_not_found`, `document_not_ready`, `recommendation_expired`, `incompatible_simulation_runs`, and `rate_limited`.

## 7. Authentication and Authorization

### 7.1 Epicenter custom MCP

The current stack uses Clerk for web identity. For the custom MCP connection:

- **Preferred application profile:** OAuth 2.0 with an explicitly registered client and per-user mapping to an Epicenter actor.
- **Synthetic hackathon fallback:** a rotated API key in the Copilot connection, mapped to a read/extract/simulate-only service actor.
- **Microsoft-native enterprise profile:** Microsoft Entra ID may replace the MCP connection identity when the clinic tenant is available, but the backend must still map the Entra subject and tenant to Epicenter roles and record scope.

Do not silently combine Clerk and Entra identities. If both exist, maintain an explicit reviewed identity mapping. Validate issuer, audience, tenant, signature, expiry, and allowed client application before checking Epicenter permissions.

Application permissions such as `epicenter:read`, `epicenter:operations_read`, and `epicenter:simulate` are enforced by Epicenter even when the OAuth provider does not issue matching custom scopes.

### 7.2 First-party Microsoft MCPs

- Microsoft Learn MCP serves public documentation and currently requires no authentication. That is why it must not receive patient or clinic-operational context.
- Dataverse, Fabric, and Power BI access follow Microsoft Entra identity plus their respective environment/workspace/semantic-model permissions.
- Azure MCP uses Azure credentials or managed identity and Azure RBAC. Its local server is intended for internal development/operations, not an external patient application.

### 7.3 Server-side authorization sequence

Every Epicenter tool call enforces:

1. valid MCP connection identity;
2. allowed client/tenant;
3. required Epicenter application permission;
4. staff/service role;
5. clinic, appointment, patient, ticket, or simulator scope;
6. RLS-compatible database access; and
7. correlation/audit recording for calls and mutations.

Never use a global service-role database client without an explicit actor and authorization decision.

## 8. Microsoft MCP Deployment Profiles

### 8.1 P0 — Minimal and credible

Connect the Copilot Studio demo agent only to the Epicenter MCP. Connect the maker/developer environment to Microsoft Learn MCP for current Microsoft implementation guidance.

This profile preserves the existing Vercel + Railway + Supabase + Clerk baseline and avoids adding preview data platforms merely for branding.

### 8.2 P1 — Microsoft analytics profile

1. Export only de-identified aggregate `operational_events` measures to a governed Fabric/Power BI model.
2. Keep patient records, raw documents, exact identifiers, and staff-level productivity data out of that model.
3. Connect an analytics-specific Copilot agent to the Power BI remote MCP after the tenant admin enables the preview endpoint and approves the Entra app/permissions.
4. Use Fabric Core MCP only in a developer/admin agent to inspect or manage the workspace—not in the staff operations agent.

This profile answers questions such as “Which stage had the highest P90 wait this week?” without giving the analytics agent access to source documents or individual patient journeys.

### 8.3 Optional Dataverse profile

Use Dataverse MCP only if the project deliberately adopts Dataverse as the authoritative store for a defined bounded context. Do not dual-write the same live queue or eligibility state to Supabase and Dataverse.

A viable bounded context could be non-patient operational configuration or approved allocation decisions, but splitting transactions across stores adds failure modes and is not recommended for P0. The Dataverse MCP Server is preview; tool names and parameters may change.

### 8.4 Optional Azure operations profile

If Epicenter later moves services to Azure, use Azure MCP in the internal engineering agent for read-only inspection of App Service/Container Apps, Storage, Azure Monitor, and related resources. Start in read-only or learn mode and expose only required namespaces/tools.

Do not connect Key Vault secret-returning tools, resource-deletion tools, or broad subscription-management tools to the staff operations agent.

## 9. Copilot Studio Configuration

1. Enable generative orchestration for the agent.
2. Deploy and verify the Epicenter Streamable HTTP endpoint.
3. In Copilot Studio, open **Tools → Add a tool → New tool → Model Context Protocol**.
4. Configure:
   - **Server name:** `Epicenter Operations`
   - **Description:** `Retrieves authorized Epicenter document, one-ticket readiness, operational, allocation-advice, and synthetic simulation information. It never approves identity, eligibility, billing, clinical priority, or real staffing changes.`
   - **Server URL:** `https://<deployment-domain>/mcp`
5. Configure OAuth, or the restricted synthetic-demo API key.
6. Add the MCP server to the agent.
7. Turn off **Allow all** and enable only the tools required for the demo.
8. Leave future/newly discovered tools disabled until reviewed.
9. Apply the environment's Power Platform data policy.
10. Add the instructions in §10 and run the acceptance tests in §12.

The onboarding wizard is preferred. A Power Apps custom connector remains a fallback when required connection settings cannot be represented by the wizard.

## 10. Suggested Agent Instructions

```text
Use Epicenter tools only for authorized operational or explicitly synthetic
simulation questions. Never infer identity, e-card, eligibility, billing,
clinical priority, or staffing approval.

Every visit has one Q-* ticket. PROCESSING, READY, and NEEDS_REVIEW are states
on that same ticket. Never tell a patient to take a second number or imply that
resolving review resets their waiting time.

Report stored deterministic readiness and eligibility results only. A result is
not final unless the tool explicitly reports the required staff confirmation.
Do not infer missing coverage facts or turn model confidence into READY.

Allocation recommendations are advisory. Explain their evidence, constraints,
expected effect, and expiry, then direct authorized staff to the approval UI.
Never claim a recommendation was applied unless a later read reports an audited
human decision. Never substitute staff across unqualified roles.

Treat every simulation result as synthetic. State the scenario, seed, and
assumptions version. Never present simulated improvement as an observed clinic
outcome. Compare runs only when the tool reports comparison_valid=true.

Do not ask for or display direct identifiers, raw source documents, credentials,
signed URLs, or another patient's data. If a tool returns
not_authorized_or_not_found, do not speculate whether the record exists.
```

Backend rules remain the source of truth; these instructions only improve orchestration and wording.

## 11. Demo Agent Flows

### 11.1 “Why does this patient need review?”

1. Call `epicenter_get_appointment_summary` or `epicenter_get_visit_ticket`.
2. Report the stored `readiness_state` and `readiness_reason`.
3. Explain that the patient keeps the same `Q-*` ticket and original waiting age.
4. Direct staff to the applicable review UI; do not mark the ticket ready.

### 11.2 “Where is pressure building?”

1. Call `epicenter_get_operational_summary` for an authorized date/clinic.
2. Report ticket counts, estimated staff-minutes, oldest age, and P50/P90 by stage.
3. Distinguish observed aggregate metrics from estimates.
4. Do not expose patient or staff-level details.

### 11.3 “Should we move a counter?”

1. Call `epicenter_list_allocation_recommendations`.
2. If present, call `epicenter_get_allocation_recommendation`.
3. Explain the sustained pressure, constraints, expected effect, and expiry.
4. Direct an authorized operations lead to the approval URL.
5. Do not apply the change through MCP.

### 11.4 “Show why Epicenter helps.”

1. List the approved scenarios.
2. Run the serial baseline and Epicenter single-ticket scenario with the same seed.
3. Call `epicenter_compare_simulation_runs`.
4. Report throughput, P50/P90, fairness gap, utilisation, and allocation churn.
5. State prominently that the result is synthetic and assumptions-driven.

### 11.5 “Is reused coverage still valid?”

1. The patient chooses reuse through the scoped application flow.
2. Call `epicenter_preview_eligibility` for the current appointment.
3. The service re-runs validity and current deterministic rules.
4. Report the preview plus `requires_staff_confirmation`; never carry forward the prior visit's approval.

## 12. Testing and Acceptance

### 12.1 Epicenter MCP

- [ ] `tools/list` exposes only reviewed Epicenter tools.
- [ ] Streamable HTTP is served at `/mcp`; SSE is not exposed.
- [ ] Missing, expired, wrong-audience/tenant/client, and invalid credentials fail safely.
- [ ] Role, app-permission, record-scope, and simulation-scope checks run server-side.
- [ ] Responses omit direct identifiers, raw document content, signed URLs, and secrets.
- [ ] Extraction retries return the same active/completed job.
- [ ] Ticket responses use one `Q-*` number and current readiness state; review never resets waiting time.
- [ ] Eligibility preview calls the versioned rules service and exposes confirmation status.
- [ ] Operational summaries are aggregate and suppress small cohorts.
- [ ] Allocation tools are read-only and cannot approve/apply/reverse a real change.
- [ ] Simulation tools accept only approved bounded scenarios/overrides and always return `synthetic=true`.
- [ ] Invalid baseline comparisons are rejected when arrivals, samples, seed, or assumptions are incompatible.
- [ ] Every call has a correlation ID; mutations create an audit/event record.

### 12.2 Copilot Studio and Microsoft MCP governance

- [ ] Generative orchestration is enabled.
- [ ] **Allow all** is off for every connected MCP server.
- [ ] Only the required tools are enabled; newly discovered tools remain disabled.
- [ ] Power Platform data policies allow the intended MCP connectors and block inappropriate combinations.
- [ ] Microsoft Learn MCP is used only with public Microsoft-development context.
- [ ] Preview status, tenant setting, licensing, Entra consent, and permissions are revalidated before enabling Dataverse, Fabric, or Power BI MCP.
- [ ] Developer/admin Microsoft MCP servers are absent from the staff operations agent.
- [ ] The agent follows single-ticket, human-approval, privacy, and synthetic-result instructions in adversarial tests.

## 13. Delivery Sequence

### P0 — Hackathon

1. Implement the six core tools in §4.1.
2. Add one operational summary and one allocation-recommendation read tool for the dynamic-allocation story.
3. Add list/run/compare simulator tools only after the deterministic engine contract exists.
4. Connect the Epicenter MCP to a dedicated Copilot Studio demo agent.
5. Use Microsoft Learn MCP in the maker/developer environment to verify current Microsoft configuration guidance.
6. Demonstrate one-ticket review, an operational-pressure question, an allocation explanation, and a synthetic baseline comparison.

### P1 — Microsoft analytics profile

1. Produce a de-identified aggregate operational model.
2. Evaluate Power BI remote MCP with the clinic tenant, Entra application, data policy, licensing, and preview risk.
3. Optionally use Fabric Core MCP in a separate developer/admin agent.
4. Evaluate Dataverse only as an explicit authoritative bounded context, never as an unowned mirror.
5. Complete privacy/security review before any real operational data reaches a Microsoft analytics service.

## 14. Official References

- [MCP in Copilot Studio](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agent-extend-action-mcp)
- [Connect an existing MCP server to Copilot Studio](https://learn.microsoft.com/en-us/microsoft-copilot-studio/mcp-add-existing-server-to-agent)
- [Add and selectively enable MCP tools/resources](https://learn.microsoft.com/en-us/microsoft-copilot-studio/mcp-add-components-to-agent)
- [Microsoft Dataverse MCP Server reference (preview)](https://learn.microsoft.com/en-us/microsoft-copilot-studio/mcp-dataverse)
- [Microsoft Learn MCP Server](https://learn.microsoft.com/en-us/training/support/mcp)
- [Power BI MCP servers overview (preview)](https://learn.microsoft.com/en-us/power-bi/developer/mcp/mcp-servers-overview)
- [Power BI remote MCP external-client registration](https://learn.microsoft.com/en-us/power-bi/developer/mcp/remote-mcp-server-external-clients)
- [Fabric Core MCP Server (preview)](https://learn.microsoft.com/en-us/rest/api/fabric/articles/mcp-servers/core-remote/get-started-core)
- [Azure MCP Server tools and security](https://learn.microsoft.com/en-us/azure/developer/azure-mcp-server/tools/)
- [Power Platform data policies for MCP connectors](https://learn.microsoft.com/en-us/power-platform/admin/wp-data-loss-prevention)
- [Official Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk)

Microsoft MCP capabilities and preview terms change quickly. Revalidate transport, tool availability, authentication, licensing, tenant settings, and Power Platform policies immediately before implementation and deployment.
