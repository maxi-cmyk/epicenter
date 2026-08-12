// Generated from backend/app/main.py. Do not edit by hand.
// Run `npm run contracts:generate` from frontend/ after changing the API schema.

export interface paths {
    "/api/v1/audit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Audit */
        get: operations["list_audit_api_v1_audit_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/dashboard": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Dashboard */
        get: operations["get_dashboard_api_v1_dashboard_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/kiosk/check-in": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Kiosk Check In */
        post: operations["kiosk_check_in_api_v1_kiosk_check_in_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/patient/account/activate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Activate Account */
        post: operations["activate_account_api_v1_patient_account_activate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/patient/pre-arrival/submit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Submit Pre Arrival */
        post: operations["submit_pre_arrival_api_v1_patient_pre_arrival_submit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/patient/registration/validate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Validate Registration */
        post: operations["validate_registration_api_v1_patient_registration_validate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/patients": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Patients */
        get: operations["list_patients_api_v1_patients_get"];
        put?: never;
        /** Create Patient */
        post: operations["create_patient_api_v1_patients_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/patients/{patient_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Patient */
        get: operations["get_patient_api_v1_patients__patient_id__get"];
        put?: never;
        post?: never;
        /** Delete Patient */
        delete: operations["delete_patient_api_v1_patients__patient_id__delete"];
        options?: never;
        head?: never;
        /** Update Patient */
        patch: operations["update_patient_api_v1_patients__patient_id__patch"];
        trace?: never;
    };
    "/api/v1/recommendations/{recommendation_id}/decision": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Decide Recommendation */
        post: operations["decide_recommendation_api_v1_recommendations__recommendation_id__decision_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/simulator/snapshots": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Simulator Snapshots */
        get: operations["get_simulator_snapshots_api_v1_simulator_snapshots_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tickets/{ticket_id}/counter": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Assign Counter */
        post: operations["assign_counter_api_v1_tickets__ticket_id__counter_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tickets/{ticket_id}/document-result": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Process Document */
        post: operations["process_document_api_v1_tickets__ticket_id__document_result_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tickets/{ticket_id}/transition": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Update Ticket */
        post: operations["update_ticket_api_v1_tickets__ticket_id__transition_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/healthz": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Healthcheck */
        get: operations["healthcheck_healthz_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** ActionResult */
        ActionResult: {
            /** Message */
            message: string;
            recommendation?: components["schemas"]["AllocationRecommendation"] | null;
            /** Success */
            success: boolean;
            ticket?: components["schemas"]["QueueTicket"] | null;
        };
        /** ActivityEvent */
        ActivityEvent: {
            /** Detail */
            detail: string;
            /** Id */
            id: string;
            /** Label */
            label: string;
            /**
             * Occurred At
             * Format: date-time
             */
            occurred_at: string;
            /** Tone */
            tone: string;
        };
        /** AllocationRecommendation */
        AllocationRecommendation: {
            /** Constraints Checked */
            constraints_checked: string[];
            /** Current Wait Minutes */
            current_wait_minutes: number;
            /** Expected Wait Minutes */
            expected_wait_minutes: number;
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
            /** Id */
            id: string;
            /** Pressured Workstream */
            pressured_workstream: string;
            /** Qualified Resource */
            qualified_resource: string;
            /** Rationale */
            rationale: string;
            /** Status */
            status: string;
            /**
             * Version
             * @default 1
             */
            version: number;
        };
        /** AuditRecord */
        AuditRecord: {
            /** Action Type */
            action_type: string;
            /** Actor Reference */
            actor_reference: string;
            /** Details */
            details: {
                [key: string]: unknown;
            };
            /** Id */
            id: number;
            /**
             * Occurred At
             * Format: date-time
             */
            occurred_at: string;
            /** Target Id */
            target_id: string;
            /** Target Table */
            target_table: string;
        };
        /** CounterAssignmentRequest */
        CounterAssignmentRequest: {
            /** Counter Number */
            counter_number: string;
            /** Expected Version */
            expected_version: number;
            /** Idempotency Key */
            idempotency_key: string;
        };
        /**
         * CoverageAction
         * @enum {string}
         */
        CoverageAction: "reuse" | "replace";
        /** DashboardSnapshot */
        DashboardSnapshot: {
            /** Activity */
            activity: components["schemas"]["ActivityEvent"][];
            /** Clinic Name */
            clinic_name: string;
            /**
             * Generated At
             * Format: date-time
             */
            generated_at: string;
            /** Metrics */
            metrics: components["schemas"]["Metric"][];
            recommendation: components["schemas"]["AllocationRecommendation"];
            /** Review Cases */
            review_cases: components["schemas"]["ReviewCase"][];
            /**
             * Synthetic
             * @default true
             */
            synthetic: boolean;
            /** Tickets */
            tickets: components["schemas"]["QueueTicket"][];
        };
        /** DocumentProcessingRequest */
        DocumentProcessingRequest: {
            /** All Documents Valid */
            all_documents_valid: boolean;
            /** All Required Documents Present */
            all_required_documents_present: boolean;
            /** Document Id */
            document_id: string;
            /** Expected Version */
            expected_version: number;
            /** Idempotency Key */
            idempotency_key: string;
            /** Match Status */
            match_status: string;
            /** Readiness Status */
            readiness_status: string;
            /** Reason */
            reason: string;
            /** Staff Confirmed */
            staff_confirmed: boolean;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /**
         * IntakeType
         * @enum {string}
         */
        IntakeType: "booked" | "walk_in";
        /** KioskCheckInRequest */
        KioskCheckInRequest: {
            /**
             * Clinical Escalation
             * @default false
             */
            clinical_escalation: boolean;
            /**
             * Idempotency Key
             * @default demo-kiosk-check-in
             */
            idempotency_key: string;
            /** Nurse Supervisor */
            nurse_supervisor: string;
            /** Patient Name */
            patient_name: string;
            /**
             * Registration Source
             * @default supervised_kiosk
             */
            registration_source: string;
        };
        /** Metric */
        Metric: {
            /** Detail */
            detail: string;
            /** Label */
            label: string;
            /** Trend */
            trend?: string | null;
            /** Value */
            value: string;
        };
        /** PatientAccountSession */
        PatientAccountSession: {
            /** Patient Id */
            patient_id: number;
            /** Source Record Key */
            source_record_key: string;
            /**
             * Synthetic
             * @default true
             */
            synthetic: boolean;
        };
        /** PatientCreateRequest */
        PatientCreateRequest: {
            /** Contact Mobile */
            contact_mobile?: string | null;
            /** Date Of Birth */
            date_of_birth?: string | null;
            /** Email */
            email?: string | null;
            /** Full Name */
            full_name: string;
            /** Idempotency Key */
            idempotency_key: string;
            /** Identifier Hash */
            identifier_hash: string;
            /** Identifier Masked */
            identifier_masked: string;
            /** Reason */
            reason: string;
            /** Source Record Key */
            source_record_key: string;
        };
        /** PatientDeleteRequest */
        PatientDeleteRequest: {
            /** Expected Version */
            expected_version: number;
            /** Idempotency Key */
            idempotency_key: string;
            /** Reason */
            reason: string;
        };
        /** PatientList */
        PatientList: {
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
            /** Records */
            records: components["schemas"]["PatientRecord"][];
        };
        /** PatientRecord */
        PatientRecord: {
            /** Contact Mobile */
            contact_mobile?: string | null;
            /** Date Of Birth */
            date_of_birth?: string | null;
            /** Deleted At */
            deleted_at?: string | null;
            /** Email */
            email?: string | null;
            /** Full Name */
            full_name: string;
            /** Id */
            id: number;
            /** Identifier Masked */
            identifier_masked: string;
            /** Source Record Key */
            source_record_key: string;
            /** Version */
            version: number;
        };
        /**
         * PatientSubmissionOutcome
         * @enum {string}
         */
        PatientSubmissionOutcome: "accepted" | "rejected" | "under_review";
        /** PatientUpdateRequest */
        PatientUpdateRequest: {
            /** Contact Mobile */
            contact_mobile?: string | null;
            /** Email */
            email?: string | null;
            /** Expected Version */
            expected_version: number;
            /** Full Name */
            full_name?: string | null;
            /** Idempotency Key */
            idempotency_key: string;
            /** Reason */
            reason: string;
        };
        /** PreArrivalSubmissionRequest */
        PreArrivalSubmissionRequest: {
            /** Appointment Id */
            appointment_id: string;
            coverage_action: components["schemas"]["CoverageAction"];
            /**
             * Expected Ticket Version
             * @default 1
             */
            expected_ticket_version: number;
            /** File Name */
            file_name?: string | null;
            /**
             * Idempotency Key
             * @default demo-prearrival
             */
            idempotency_key: string;
        };
        /** PreArrivalSubmissionResult */
        PreArrivalSubmissionResult: {
            /** Message */
            message: string;
            /** Next Action */
            next_action: string;
            /** @default under_review */
            outcome: components["schemas"]["PatientSubmissionOutcome"];
            /** Processing Reference */
            processing_reference: string;
            /**
             * Success
             * @default true
             */
            success: boolean;
            /**
             * Synthetic
             * @default true
             */
            synthetic: boolean;
        };
        /** QueueTicket */
        QueueTicket: {
            /** Actual Counter */
            actual_counter?: string | null;
            /** Checked In At */
            checked_in_at?: string | null;
            /**
             * Clinical Escalation
             * @default false
             */
            clinical_escalation: boolean;
            /** Expected Counter */
            expected_counter?: string | null;
            /** Id */
            id: string;
            intake_type: components["schemas"]["IntakeType"];
            /**
             * Original Ordering At
             * Format: date-time
             */
            original_ordering_at: string;
            /** Patient Id */
            patient_id: string;
            /** Patient Name */
            patient_name: string;
            /** Processing Stage */
            processing_stage: string;
            /** Readiness Reason */
            readiness_reason: string;
            readiness_state: components["schemas"]["ReadinessState"];
            /** Scheduled At */
            scheduled_at?: string | null;
            /** @default on_track */
            service_target: components["schemas"]["ServiceTarget"];
            /**
             * Staff Confirmed
             * @default false
             */
            staff_confirmed: boolean;
            /**
             * Version
             * @default 1
             */
            version: number;
            visit_phase: components["schemas"]["VisitPhase"];
            /** Waiting Minutes */
            waiting_minutes: number;
        };
        /**
         * ReadinessState
         * @enum {string}
         */
        ReadinessState: "processing" | "ready" | "needs_review";
        /** RecommendationDecisionRequest */
        RecommendationDecisionRequest: {
            /**
             * Decided By
             * @default Demo operations lead
             */
            decided_by: string;
            /** Decision */
            decision: string;
            /**
             * Expected Version
             * @default 1
             */
            expected_version: number;
            /**
             * Idempotency Key
             * @default demo-allocation
             */
            idempotency_key: string;
        };
        /** RegistrationValidationRequest */
        RegistrationValidationRequest: {
            /** Appointment Reference */
            appointment_reference: string;
            /**
             * Date Of Birth
             * Format: date
             */
            date_of_birth: string;
            /** Email */
            email: string;
            /** Full Name */
            full_name: string;
            /**
             * Idempotency Key
             * @default demo-registration-validation
             */
            idempotency_key: string;
            /** Identifier Hash */
            identifier_hash: string;
        };
        /** RegistrationValidationResult */
        RegistrationValidationResult: {
            /** Field Results */
            field_results: {
                [key: string]: string;
            };
            /** Id */
            id: string;
            outcome: components["schemas"]["PatientSubmissionOutcome"];
            /** Patient Next Action */
            patient_next_action: string;
            /** Patient Reason Code */
            patient_reason_code: string;
            /** Version */
            version: number;
        };
        /** ReviewCase */
        ReviewCase: {
            /** Document Name */
            document_name?: string | null;
            /** Evidence Summary */
            evidence_summary: string;
            /** Id */
            id: string;
            /** Next Action */
            next_action: string;
            /** Patient Name */
            patient_name: string;
            /** Reason Code */
            reason_code: string;
            /** Reason Label */
            reason_label: string;
            service_target: components["schemas"]["ServiceTarget"];
            /** Ticket Id */
            ticket_id: string;
            /** Waiting Minutes */
            waiting_minutes: number;
        };
        /**
         * ServiceTarget
         * @enum {string}
         */
        ServiceTarget: "on_track" | "approaching" | "over_target";
        /** SimulatorSnapshot */
        SimulatorSnapshot: {
            /** Assumptions Version */
            assumptions_version: string;
            /** Id */
            id: string;
            /** Scenario Id */
            scenario_id: string;
            /** Scenario Version */
            scenario_version: string;
            /** Seed */
            seed: number;
            /** Snapshot Hash */
            snapshot_hash: string;
            /** Snapshot Payload */
            snapshot_payload: {
                [key: string]: unknown;
            };
            /**
             * Synthetic
             * @default true
             */
            synthetic: boolean;
        };
        /** TicketTransitionRequest */
        TicketTransitionRequest: {
            /**
             * Expected Version
             * @default 1
             */
            expected_version: number;
            /**
             * Idempotency Key
             * @default demo-transition
             */
            idempotency_key: string;
            readiness_state: components["schemas"]["ReadinessState"];
            /** Reason */
            reason: string;
            /**
             * Staff Confirmed
             * @default false
             */
            staff_confirmed: boolean;
        };
        /** ValidationError */
        ValidationError: {
            /** Context */
            ctx?: Record<string, never>;
            /** Input */
            input?: unknown;
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
        };
        /**
         * VisitPhase
         * @enum {string}
         */
        VisitPhase: "incoming" | "ongoing" | "finished";
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    list_audit_api_v1_audit_get: {
        parameters: {
            query?: {
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuditRecord"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_dashboard_api_v1_dashboard_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DashboardSnapshot"];
                };
            };
        };
    };
    kiosk_check_in_api_v1_kiosk_check_in_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["KioskCheckInRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ActionResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    activate_account_api_v1_patient_account_activate_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PatientAccountSession"];
                };
            };
        };
    };
    submit_pre_arrival_api_v1_patient_pre_arrival_submit_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PreArrivalSubmissionRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PreArrivalSubmissionResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    validate_registration_api_v1_patient_registration_validate_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RegistrationValidationRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RegistrationValidationResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_patients_api_v1_patients_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                search?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PatientList"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_patient_api_v1_patients_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PatientCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PatientRecord"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_patient_api_v1_patients__patient_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                patient_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PatientRecord"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_patient_api_v1_patients__patient_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                patient_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PatientDeleteRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PatientRecord"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_patient_api_v1_patients__patient_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                patient_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PatientUpdateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PatientRecord"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    decide_recommendation_api_v1_recommendations__recommendation_id__decision_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                recommendation_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RecommendationDecisionRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ActionResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_simulator_snapshots_api_v1_simulator_snapshots_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SimulatorSnapshot"][];
                };
            };
        };
    };
    assign_counter_api_v1_tickets__ticket_id__counter_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CounterAssignmentRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ActionResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    process_document_api_v1_tickets__ticket_id__document_result_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DocumentProcessingRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ActionResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_ticket_api_v1_tickets__ticket_id__transition_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TicketTransitionRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ActionResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    healthcheck_healthz_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
        };
    };
}
