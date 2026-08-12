# Clinic Workflow

Reference workflow diagram covering the patient, nurse, and system interactions from registration through payment. Kept here for future reference when designing/aligning features against the real-world process.

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
        N8{Pharmacist checks prescription}
        N9[Under insurance or TPA?]
    end

    subgraph System
        S0{System keeps the information}
        S1{System autofills electronic TPA form}
        S2((Document/TPA - record info))
        S3{System checks CHAS + corporate insurance eligibility to match code to right package}
        S4{System works out billing code + uncovered cost + queue number}
        S5((Cost to be covered))
        S6{System works out total cost, offer including TPA}
        S7{System enters into TPA - what was processed}
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
    N9 -->|No, given| P10
    N9 -->|Yes| S6
    S6 --> S7
    S7 --> P10
```
