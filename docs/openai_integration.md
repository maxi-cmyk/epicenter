# OpenAI Runtime and Copilot-Compatible MCP Plan

- **Status:** Implemented and independently verified locally; hosted OpenAI/Copilot checks remain deployment work
- **Development LLM:** OpenAI Responses API
- **Development analytics:** Native Next.js dashboard backed by FastAPI and Supabase
- **Deployment requirement:** Custom MCP servers must remain compatible with Microsoft Copilot Studio
- **Scale option:** Power BI/Fabric is documented for future enterprise analytics, not required for development or the core demo

## 1. Architecture Decision

Epicenter uses OpenAI for document intelligence and the authenticated nurse assistant during development and in the application runtime. It does not require Copilot Studio, Power BI, or a Microsoft tenant to run locally or demonstrate the core workflow.

The custom Epicenter MCP endpoints are deliberately client-neutral. At deployment and publication time, the same public HTTPS Streamable HTTP endpoints must be discoverable and callable by Copilot Studio without a separate implementation or a fork of the business rules.

```text
Development and normal application runtime

Nurse application → FastAPI → OpenAI Responses API ─┐
                                                     ├→ Epicenter MCP → shared services → Supabase
Document worker → OpenAI document extraction         │
                                                     │
Native dashboard → FastAPI analytics services ───────┘

Deployment/publication compatibility

Copilot Studio agent → the same custom Epicenter MCP endpoints

Future enterprise scale only

De-identified aggregate projection → Power BI/Fabric semantic model
```

OpenAI and Copilot Studio are alternative MCP clients, not a chain of models. Copilot Studio does not need to call OpenAI, and the Epicenter application does not need to call Copilot Studio.

## 2. MCP Scope Decision

Epicenter uses only its own custom MCP servers. Microsoft-hosted Copilot MCPs are not part of the architecture, development path, deployment requirements, or fallback plan.

| Capability | Implementation |
| --- | --- |
| Live queue, readiness, simulator, allocation and operational analytics | Custom Epicenter Operations MCP |
| Insurance-format mapping, fixture validation and maker/checker activation | Custom Insurance Format Registry MCP |
| Native analytics presentation | Next.js dashboard consuming FastAPI/Supabase contracts directly; no MCP required for rendering |
| Future Power BI/Fabric scalability | Optional governed aggregate export/dashboard only; no Power BI MCP dependency |

Both custom servers call the existing FastAPI service layer, so Supabase remains the single source of truth and deterministic rules remain authoritative. Copilot Studio is only a supported client for these custom servers after deployment.

## 3. Native Analytics Dashboard

The native nurse dashboard is the P0 analytics surface. Supabase aggregate views and FastAPI analytics services calculate each metric once; the dashboard, simulator, REST routes, and Operations MCP consume the same versioned contracts.

Minimum dashboard measures are:

- readiness rate and review workload;
- P50/P90 wait and oldest-ticket age;
- throughput and stage occupancy;
- staff touches and exception reasons;
- active-resource utilisation;
- recommendation evidence and estimated allocation effect; and
- baseline-versus-Epicenter simulator comparison.

Every metric response includes its clinic scope, time range, source, snapshot time, assumptions version, and stale/unavailable state. The dashboard must remain usable when OpenAI, Copilot Studio, or either MCP transport is unavailable.

The deterministic simulation event log—not chart timers or model output—drives queue animation. Agents may explain a completed snapshot but cannot create, reorder, or alter simulated events.

## 4. Shared Custom MCP Servers

FastAPI exposes two reviewed Streamable HTTP endpoints:

```text
/mcp/operations
/mcp/insurance-registry
```

Both call the same authenticated domain services as the REST API. MCP handlers validate input, establish the actor and clinic scope, invoke one service, and serialize a minimal typed response. They never contain a second implementation of extraction, readiness, eligibility, queue ordering, billing, or allocation logic.

### 4.1 Epicenter Operations MCP

Candidate read/explain and synthetic-simulation tools:

```text
epicenter_get_extraction_status(job_id)
epicenter_preview_eligibility(document_id, appointment_reference)
epicenter_get_visit_ticket(ticket_id)
epicenter_get_operational_summary(clinic_id, date_range)
epicenter_get_queue_snapshot(clinic_id, snapshot_at)
epicenter_get_allocation_recommendation(recommendation_id)
epicenter_run_simulation(scenario_id, seed, bounded_overrides)
epicenter_compare_simulation_runs(baseline_run_id, epicenter_run_id)
```

The server exposes no generic SQL, unrestricted search, arbitrary URL fetch, filesystem access, raw prompt proxy, or database service-role capability.

### 4.2 Insurance Format Registry MCP

This isolated maker/checker server operates only on approved synthetic or formally de-identified templates. It may:

- retrieve approved document-family schemas and checkbox conventions;
- propose a mapping for a new synthetic form;
- return required source-evidence fields and fixture tests;
- compare a draft mapping with an active version; and
- report regression and review status.

It cannot learn online from live patient records, activate its own proposal, write canonical patient/coverage/eligibility rows, or make an eligibility decision. Extracted facts enter a `pending_review` staging record and are promoted only by an authorized staff confirmation through the shared backend.

The registry inventory also includes `registry_review_mapping`. It rejects self-review, records maker and checker attribution, and accepts only `synthetic` or `formally_deidentified` fixtures with an approval reference. Common patient-identity fields are rejected at the adapter boundary.

### 4.3 Local protocol verification

Run the API in demo mode on an unused port, then use the independent MCP Python SDK client:

```bash
cd backend
EPICENTER_DEMO_MODE=true EPICENTER_PERSISTENCE_MODE=demo .venv/bin/uvicorn app.main:app --port 8017
.venv/bin/python scripts/verify_mcp_client.py --base-url http://127.0.0.1:8017
```

The verifier initializes each server and lists its exact bounded inventory. Contract tests separately cover calls, invalid input, role and clinic authorization, the 25,000-character response bound, maker/checker attribution, and the exact two-server inventory.

## 5. OpenAI Responsibilities

### 5.1 Document extraction

The private worker sends a synthetic PDF/image to an evaluated OpenAI document-capable model with a strict output schema. It validates the response, records field-level page/excerpt evidence and confidence, and stages the result for deterministic rules and staff review.

Model confidence is advisory. Exact identifiers, dates, appointment scope, required evidence, versioned rules, and staff confirmation remain authoritative.

### 5.2 Nurse assistant

The browser calls FastAPI with its Clerk session. FastAPI authorizes the actor, selects only task-relevant tools, calls the OpenAI Responses API, re-authorizes each MCP execution, and returns a grounded answer with snapshot/source labels.

OpenAI may summarize, compare, and explain approved tool results. It may not approve readiness, correct canonical facts, attest identity/e-card checks, confirm billing, reorder a live queue, infer clinical urgency, or approve an allocation.

The server-side environment is:

```text
OPENAI_API_KEY
OPENAI_MODEL
OPENAI_EXTRACTION_MODEL
```

No OpenAI key, MCP credential, Clerk secret, or Supabase secret is exposed through a browser variable or tool response.

## 6. Copilot Studio Compatibility Profile

Development does not depend on Copilot Studio. Before the deployed/published build is declared compatible, each public MCP endpoint must satisfy this profile:

- public HTTPS URL on Railway with a separate `/healthz` route;
- Streamable HTTP transport, with no reliance on an SSE-only endpoint;
- standards-compliant MCP initialization and tool discovery;
- stable server, tool, input-schema, output-schema, and error contracts;
- narrow JSON schemas with useful descriptions and no OpenAI-only protocol extension;
- supported authentication: API key only for a synthetic demo where permitted, or standards-based OAuth for user-scoped production access;
- per-call role, clinic, record, and simulation-boundary authorization;
- read-only/destructive annotations that match actual behavior;
- bounded responses with no raw documents or direct identifiers in operational analytics tools; and
- versioning, audit, timeout, rate-limit, revocation, and rollback behavior.

Compatibility does not mean Copilot Studio is required for the patient or nurse applications. It means a Copilot Studio agent can onboard the deployed custom servers, list the reviewed tools, and call an allowed tool using the same contract used by OpenAI.

### 6.1 Deployment verification

1. Deploy the MCP endpoints to Railway over HTTPS.
2. Verify initialization, `tools/list`, valid calls, invalid-schema errors, unauthorized calls, timeout handling, and response bounds with an MCP inspector/client.
3. Add the existing server in Copilot Studio using the server URL and supported authentication.
4. Confirm the Copilot Studio test panel discovers only the intended tools.
5. Call at least one read-only synthetic operations tool and reconcile its result with the native dashboard/API.
6. Confirm approval-bound and out-of-scope actions remain unavailable.
7. Record each custom server version, authentication mode, tool inventory, evidence, fallback, and rollback instructions.
8. If the available trial cannot publish, retain test-panel evidence and track production publication/licensing as a manual release gate; do not misrepresent a test connection as a published channel.

## 7. Authentication Boundary

The Epicenter application uses short-lived actor-scoped authorization for remote MCP calls. Every server re-checks the signed-in actor, role, clinic, and requested record instead of trusting the client to filter results.

For Copilot Studio compatibility:

- a synthetic judge/demo endpoint may use a tightly scoped, revocable API key if the environment and brief allow it;
- any real patient/staff deployment requires user-scoped OAuth, least privilege, revocation, and a completed privacy/security review; and
- neither mode grants a generic database credential or bypasses backend authorization.

Authentication details are deployment configuration, never committed values.

## 8. Power BI/Fabric Scalability Option

Power BI is not part of development, P0 implementation, or the core judging path. The native dashboard remains the source presentation and fallback.

If Epicenter later needs cross-clinic enterprise reporting, create a one-way analytics projection:

```text
Canonical operational events
  → governed de-identified aggregate tables
  → scheduled/incremental refresh
  → Power BI/Fabric semantic model
  → enterprise Power BI/Fabric dashboards
```

Adoption gates are:

- a demonstrated multi-clinic reporting need that the native dashboard cannot reasonably serve;
- de-identified aggregates only, with no raw patient documents, direct identifiers, or unrestricted row access;
- metric reconciliation with the native FastAPI/Supabase contract;
- tenant administration, Entra application, licensing/capacity, preview-feature, data-residency, and security approval;
- documented refresh latency and stale-data behavior;
- least-privilege access and auditability; and
- a maintained native-dashboard fallback.

Power BI must never become the operational source of truth or the only way to run the simulator, inspect the live queue, or verify a recommendation.

## 9. Suggested Backend Layout

```text
backend/app/
├── ai/
│   ├── client.py                 # OpenAI Responses API adapter
│   ├── extraction.py             # strict document extraction orchestration
│   ├── assistant.py              # reviewed tool selection and grounded responses
│   └── schemas.py
├── analytics/
│   ├── service.py                # canonical metric calculations
│   └── schemas.py
├── mcp/
│   ├── operations.py             # client-neutral Streamable HTTP MCP
│   ├── insurance_registry.py     # isolated maker/checker MCP
│   ├── auth.py
│   └── schemas.py
└── core/                         # authoritative domain services
```

REST routes, the native dashboard, OpenAI tool calls, and Copilot Studio calls all converge on `core` and `analytics`; transport adapters stay thin.

## 10. Delivery Order

### Development

1. Stabilize protected patient/nurse workflows and canonical metrics.
2. Build the native dashboard and deterministic simulator from shared metric/event contracts.
3. Add the server-side OpenAI document adapter and fixture evaluation.
4. Implement the reviewed MCP tools over existing services.
5. Connect the authenticated nurse assistant through the OpenAI Responses API.
6. Test provider outage, malformed output, authorization, tool misuse, and MCP invariants.

### Deployment and publication

1. Deploy the API, worker, and Streamable HTTP MCP endpoints.
2. Run the transport/security/contract verification suite.
3. Verify Copilot Studio discovery and a reconciled read-only call.
4. Complete the applicable authentication, tenant, licensing, publication, and rollback checks.

### Future scale

1. Reassess whether multi-clinic analytics justifies Power BI/Fabric.
2. If approved, build only the governed aggregate projection and reconcile it with native metrics.
3. Keep agent access through the custom Operations MCP, backed by the reconciled FastAPI/Supabase metric contract.

## 11. Acceptance Checklist

- [x] OpenAI keys and model identifiers are server-side and environment-validated.
- [x] Extraction outputs match strict schemas and include source evidence.
- [x] Deterministic services, not the model, decide readiness and eligibility.
- [ ] The native dashboard and simulator share versioned FastAPI/Supabase contracts.
- [x] Normal workflows and native analytics work when OpenAI and MCP transport are unavailable.
- [x] Every MCP tool has a named owner, narrow schema, least privilege, tests, and removal criteria.
- [x] Operations tools expose no arbitrary SQL or direct patient-document access.
- [x] Registry proposals require maker/checker activation; deployment policy must require passing fixture regression before approval.
- [ ] Railway endpoints pass Streamable HTTP initialization, discovery, authorization, and failure tests.
- [ ] Copilot Studio discovers the intended deployed tools and reconciles at least one read-only synthetic result.
- [ ] Publication/licensing limitations are reported honestly as manual gates.
- [ ] Power BI/Fabric remains optional, aggregate-only, reconciled, and non-authoritative, with no Power BI MCP dependency.

## 12. Official References

- [OpenAI Responses API](https://developers.openai.com/api/docs/guides/migrate-to-responses)
- [OpenAI MCP and connectors](https://developers.openai.com/api/docs/guides/tools-connectors-mcp)
- [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [Add an existing MCP server to a Copilot Studio agent](https://learn.microsoft.com/en-us/microsoft-copilot-studio/mcp-add-existing-server-to-agent)
- [Copilot Studio publication fundamentals](https://learn.microsoft.com/en-gb/microsoft-copilot-studio/publication-fundamentals-publish-channels)
