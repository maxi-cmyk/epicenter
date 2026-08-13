# Clinic Workflow

The first diagram is the as-is clinic process this product is designed against. The second diagram is how the current Epicenter demo implements that process across the patient panel, nurse panel, and FastAPI backend.

## As-is clinic process

```mermaid
flowchart TD
    subgraph Patient
        P1[Does the user preregister?]
        P2{User walks in directly to counter}
        P3{User sends info + documents into system}
        P4[Did the patient preregister?]
        P8{Patient fills in the forms}
        P9{Patient waits + consultation}
        P10{Patient pays + leaves}
    end

    subgraph Nurse
        N1{Nurse checks the document + info is correct}
        N2{Nurse fills in the info + document manually}
        N3[Does patient have TPA?]
        N4{Nurse writes physical TPA form on paper}
        N5[Is it a checkup?]
        N6{Nurse rechecks package is correct}
        N7{Nurse checks and informs patient about cost + queue number}
        N8{Medication dispensed}
        N9[Does additional document need to be processed? e.g. TPA]
    end

    subgraph System
        S0{System keeps the information}
        S1{System autofills electronic TPA form}
        S2((Document/TPA - record info))
        S3{System checks CHAS + corporate insurance eligibility to match code to right package}
        S4{System works out billing code + uncovered cost + queue number}
        S5((Cost to be covered))
        S6{System records which documents are present}
        S7{System records what was processed for TPA}
    end

    P1 -->|No| P2
    P1 -->|Yes| P3
    P2 --> P4
    P4 -->|No| N2
    P4 -->|Yes| N1
    P3 --> N1
    N2 --> N1
    N1 --> S0
    N1 --> N3
    S0 --> S2
    N3 -->|Yes| N4
    N3 -->|Yes| S1
    N3 -->|No| S3
    N4 --> S2
    S1 --> S2
    S2 -.->|referenced| N3
    S2 -.->|preloaded| P8
    S3 --> N6
    N6 -.->|referenced| S3
    N6 --> N5
    N5 -->|Yes| P8
    N5 -->|No| N7
    P8 --> N7
    N7 --> S4
    S4 -.->|referenced| N7
    S4 --> S5
    S5 -.->|referenced| N7
    N7 --> P9
    P9 --> N8
    N8 --> N9
    N9 -->|No| P10
    N9 -->|Yes| S6
    S6 --> S7
    S7 --> P10
```

## Implemented Epicenter path

Patient panel (`localhost:3000`): signed-in Home → coverage upload/reuse → questionnaire (when required) → Queue (queue number + assigned counter) → mocked Payment → Records.

Nurse panel (`localhost:3001`): Today board (Incoming / Ongoing / Finished) → open a ticket into the gated task flow. Walk-in kiosk is `/kiosk`. Database, Audit, and Simulator are separate destinations and do not interrupt the Today workflow.

```mermaid
flowchart TD
    subgraph PatientApp[Patient panel]
        H[Home]
        C[Coverage upload or reuse]
        QN[Questionnaire when required]
        Q[Queue: number + counter]
        PAY[Mocked payment]
        R[Records]
        H --> C --> QN --> Q --> PAY --> R
    end

    subgraph Intake[Intake]
        BOOK[Booked: pre-arrival processing]
        WALK[Walk-in: nurse-supervised kiosk]
    end

    subgraph Route[Counter routing]
        FAST[Fast F1-F2: booked and ready only]
        SLOW[Slow S1-S4: all walk-ins and any booked case with issues]
    end

    subgraph NurseApp[Nurse task flow — same Q-* ticket]
        T0[Today: Incoming / Ongoing / Finished]
        T1[Identity and e-card]
        T2[Forms guidance]
        T3[Forms review]
        T4[Confirm package if documents on file]
        T5[Billing and queue]
        T6[Summary]
        T0 --> T1 --> T2 --> T3 --> T4 --> T5 --> T6
    end

    BOOK --> FAST
    BOOK -->|needs review| SLOW
    WALK --> SLOW
    FAST --> T0
    SLOW --> T0
    T6 --> Q
```

### Nurse task gates

Opening a ticket walks through these persisted confirmations. Package is skipped when the ticket has no documents. Exceptions stay on the same ticket.

| Step | Screen | Gate |
| --- | --- | --- |
| 1 | Identity & e-card | Nurse attests the in-person identity check (`identity_confirmed`) |
| 2 | Forms guidance | System shows which forms apply; no separate confirm action |
| 3 | Forms review | Nurse confirms e-forms (`forms_confirmed`) |
| 4 | Confirm package | Nurse confirms CHAS/corporate package when documents exist (`package_confirmed`) |
| 5 | Billing & queue | Nurse confirms billing code, uncovered cost, and queue (`billing_confirmed`) |
| 6 | Summary | Queue number, counter, billing code, and uncovered cost |

### Counter assignment

- Walk-ins always receive a slow counter (`S1`–`S4`).
- Only booked patients with `readiness_state` `ready` receive a fast counter (`F1`–`F2`).
- The patient Queue screen and nurse dashboard both show the assigned queue number and counter.
- Overflow (simulator `dynamic_allocation` only): idle fast counters may take slow-queue patients when the fast queue is empty; overflow uses slow duration and does not preempt a fast case.
