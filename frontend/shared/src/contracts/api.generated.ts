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
    "/api/v1/pharmacy/queue": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Pharmacy Queue */
        get: operations["get_pharmacy_queue_api_v1_pharmacy_queue_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
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
    "/api/v1/staff/session": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Staff Session */
        get: operations["get_staff_session_api_v1_staff_session_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tickets/{ticket_id}/billing/confirm": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Confirm Billing */
        post: operations["confirm_billing_api_v1_tickets__ticket_id__billing_confirm_post"];
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
    "/api/v1/tickets/{ticket_id}/documents/{document_id}/confirm": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Confirm Document */
        post: operations["confirm_document_api_v1_tickets__ticket_id__documents__document_id__confirm_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tickets/{ticket_id}/medication": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Record Medication Dispense */
        post: operations["record_medication_dispense_api_v1_tickets__ticket_id__medication_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tickets/{ticket_id}/package/confirm": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Confirm Package */
        post: operations["confirm_package_api_v1_tickets__ticket_id__package_confirm_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tickets/{ticket_id}/tpa-submission": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Tpa Submission */
        get: operations["get_tpa_submission_api_v1_tickets__ticket_id__tpa_submission_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tickets/{ticket_id}/tpa-submission/confirm": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Confirm Tpa Submission */
        post: operations["confirm_tpa_submission_api_v1_tickets__ticket_id__tpa_submission_confirm_post"];
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
    "/mcp/insurance-registry/healthz": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Healthcheck */
        get: operations["healthcheck_mcp_insurance_registry_healthz_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/mcp/insurance-registry/initialize": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Initialize */
        post: operations["initialize_mcp_insurance_registry_initialize_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/mcp/insurance-registry/tools/call": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Call Tool
         * @description Dispatch a registry tool call after authentication and authorization.
         */
        post: operations["call_tool_mcp_insurance_registry_tools_call_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/mcp/insurance-registry/tools/list": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Tools */
        get: operations["list_tools_mcp_insurance_registry_tools_list_get"];
        put?: never;
        /** List Tools */
        post: operations["list_tools_mcp_insurance_registry_tools_list_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/mcp/operations/healthz": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Healthcheck */
        get: operations["healthcheck_mcp_operations_healthz_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/mcp/operations/initialize": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Initialize
         * @description MCP initialization handshake.
         */
        post: operations["initialize_mcp_operations_initialize_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/mcp/operations/tools/call": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Call Tool
         * @description Dispatch a tool call after authentication and per-tool authorization.
         */
        post: operations["call_tool_mcp_operations_tools_call_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/mcp/operations/tools/list": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Tools
         * @description Return the MCP tool inventory. Stable — discovery requires no auth.
         */
        get: operations["list_tools_mcp_operations_tools_list_get"];
        put?: never;
        /**
         * List Tools
         * @description Return the MCP tool inventory. Stable — discovery requires no auth.
         */
        post: operations["list_tools_mcp_operations_tools_list_post"];
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
            medication?: components["schemas"]["MedicationDispense"] | null;
            /** Message */
            message: string;
            recommendation?: components["schemas"]["AllocationRecommendation"] | null;
            /** Success */
            success: boolean;
            ticket?: components["schemas"]["QueueTicket"] | null;
            tpa_submission?: components["schemas"]["TpaSubmission"] | null;
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
        /** BillingConfirmRequest */
        BillingConfirmRequest: {
            /** Corrected Billing Code */
            corrected_billing_code?: string | null;
            /** Corrected Queue Number */
            corrected_queue_number?: string | null;
            /** Corrected Uncovered Cost */
            corrected_uncovered_cost?: number | null;
            /** Expected Version */
            expected_version: number;
            /** Idempotency Key */
            idempotency_key: string;
        };
        /** ChecklistItem */
        ChecklistItem: {
            /** Detail */
            detail?: string | null;
            /** Label */
            label: string;
            status: components["schemas"]["ChecklistStatus"];
        };
        /**
         * ChecklistStatus
         * @enum {string}
         */
        ChecklistStatus: "pass" | "pending" | "fail" | "not_required";
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
        /**
         * Document
         * @description One piece of payer paperwork on file for a patient (see DocumentCategory for
         *     the distinct kinds it can be). Each carries a shared envelope (issuer, category,
         *     validity) plus a `facts` map for whatever fields are specific to that category
         *     (e.g. a benefit structure's plan tier vs. an authorisation letter's approval
         *     number).
         */
        Document: {
            category: components["schemas"]["DocumentCategory"];
            /**
             * Confirmed
             * @default false
             */
            confirmed: boolean;
            /** Confirmed At */
            confirmed_at?: string | null;
            /** Confirmed By */
            confirmed_by?: string | null;
            /** Document Type */
            document_type: string;
            /**
             * Facts
             * @default {}
             */
            facts: {
                [key: string]: string;
            };
            /** Id */
            id: string;
            /** Issuer Code */
            issuer_code: string;
            /** Issuer Name */
            issuer_name: string;
            /** Reference Number */
            reference_number?: string | null;
            /** Valid From */
            valid_from?: string | null;
            /** Valid To */
            valid_to?: string | null;
            /**
             * Version
             * @default 1
             */
            version: number;
        };
        /**
         * DocumentCategory
         * @description Payer paperwork (TPA, CHAS, corporate insurance, ...) splits into distinct
         *     kinds, each with different fields worth capturing.
         * @enum {string}
         */
        DocumentCategory: "form" | "authorisation_letter" | "benefit_structure" | "coding_scheme";
        /** DocumentConfirmRequest */
        DocumentConfirmRequest: {
            /** Expected Version */
            expected_version: number;
            /** Facts */
            facts?: {
                [key: string]: string;
            } | null;
            /** Idempotency Key */
            idempotency_key: string;
            /** Reference Number */
            reference_number?: string | null;
            /** Valid From */
            valid_from?: string | null;
            /** Valid To */
            valid_to?: string | null;
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
        /** MedicationDispense */
        MedicationDispense: {
            /**
             * Dispensed At
             * Format: date-time
             */
            dispensed_at: string;
            /** Dispensed By */
            dispensed_by: string;
            /** Id */
            id: string;
            /** Items */
            items: components["schemas"]["MedicationItem"][];
            /** Ticket Id */
            ticket_id: string;
            /** Total Cost */
            total_cost: number;
            /**
             * Version
             * @default 1
             */
            version: number;
        };
        /** MedicationDispenseRequest */
        MedicationDispenseRequest: {
            /** Idempotency Key */
            idempotency_key: string;
            /** Items */
            items: components["schemas"]["MedicationItem"][];
        };
        /** MedicationItem */
        MedicationItem: {
            /** Name */
            name: string;
            /** Quantity */
            quantity: number;
            /** Unit Cost */
            unit_cost: number;
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
        /** PackageConfirmRequest */
        PackageConfirmRequest: {
            /** Corrected Package */
            corrected_package?: string | null;
            /** Expected Version */
            expected_version: number;
            /** Idempotency Key */
            idempotency_key: string;
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
        /** PatientSummary */
        PatientSummary: {
            /** Address */
            address?: string | null;
            /** Contact Mobile */
            contact_mobile?: string | null;
            /** Date Of Birth */
            date_of_birth?: string | null;
            /** Full Name */
            full_name: string;
            /** Identifier Masked */
            identifier_masked: string;
        };
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
            /** Actual Room */
            actual_room?: string | null;
            /** Billing Code */
            billing_code?: string | null;
            /**
             * Billing Confirmed
             * @default false
             */
            billing_confirmed: boolean;
            /** Billing Confirmed At */
            billing_confirmed_at?: string | null;
            /** Billing Confirmed By */
            billing_confirmed_by?: string | null;
            /** Checked In At */
            checked_in_at?: string | null;
            /**
             * Clinical Escalation
             * @default false
             */
            clinical_escalation: boolean;
            /**
             * Documents
             * @default []
             */
            documents: components["schemas"]["Document"][];
            /** Expected Room */
            expected_room?: string | null;
            /** Id */
            id: string;
            intake_type: components["schemas"]["IntakeType"];
            /** Matched Package */
            matched_package?: string | null;
            /**
             * Original Ordering At
             * Format: date-time
             */
            original_ordering_at: string;
            /**
             * Package Confirmed
             * @default false
             */
            package_confirmed: boolean;
            /** Package Confirmed At */
            package_confirmed_at?: string | null;
            /** Package Confirmed By */
            package_confirmed_by?: string | null;
            /** Patient Id */
            patient_id: string;
            /** Patient Name */
            patient_name: string;
            /** Processing Stage */
            processing_stage: string;
            /** Queue Number */
            queue_number?: string | null;
            /** Readiness Reason */
            readiness_reason: string;
            readiness_state: components["schemas"]["ReadinessState"];
            record_checklist?: components["schemas"]["RecordChecklist"] | null;
            /** Scheduled At */
            scheduled_at?: string | null;
            /** @default on_track */
            service_target: components["schemas"]["ServiceTarget"];
            /**
             * Staff Confirmed
             * @default false
             */
            staff_confirmed: boolean;
            /** Uncovered Cost */
            uncovered_cost?: number | null;
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
        /** RecordChecklist */
        RecordChecklist: {
            /**
             * Items
             * @default []
             */
            items: components["schemas"]["ChecklistItem"][];
            patient?: components["schemas"]["PatientSummary"] | null;
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
        /** StaffSession */
        StaffSession: {
            /** Clinic Id */
            clinic_id: string;
            /** Role */
            role: string;
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
        /** TpaSubmission */
        TpaSubmission: {
            /** Checkup Summary */
            checkup_summary: string;
            /** Documents */
            documents: components["schemas"]["Document"][];
            /** External Reference */
            external_reference?: string | null;
            /** Id */
            id: string;
            medication?: components["schemas"]["MedicationDispense"] | null;
            status: components["schemas"]["TpaSubmissionStatus"];
            /** Submitted At */
            submitted_at?: string | null;
            /** Submitted By */
            submitted_by?: string | null;
            /** Ticket Id */
            ticket_id: string;
            /**
             * Version
             * @default 1
             */
            version: number;
        };
        /** TpaSubmissionConfirmRequest */
        TpaSubmissionConfirmRequest: {
            /** Expected Version */
            expected_version: number;
            /** Idempotency Key */
            idempotency_key: string;
        };
        /**
         * TpaSubmissionStatus
         * @enum {string}
         */
        TpaSubmissionStatus: "draft" | "submitted";
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
    get_pharmacy_queue_api_v1_pharmacy_queue_get: {
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
                    "application/json": components["schemas"]["QueueTicket"][];
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
    get_staff_session_api_v1_staff_session_get: {
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
                    "application/json": components["schemas"]["StaffSession"];
                };
            };
        };
    };
    confirm_billing_api_v1_tickets__ticket_id__billing_confirm_post: {
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
                "application/json": components["schemas"]["BillingConfirmRequest"];
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
    confirm_document_api_v1_tickets__ticket_id__documents__document_id__confirm_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                document_id: string;
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DocumentConfirmRequest"];
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
    record_medication_dispense_api_v1_tickets__ticket_id__medication_post: {
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
                "application/json": components["schemas"]["MedicationDispenseRequest"];
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
    confirm_package_api_v1_tickets__ticket_id__package_confirm_post: {
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
                "application/json": components["schemas"]["PackageConfirmRequest"];
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
    get_tpa_submission_api_v1_tickets__ticket_id__tpa_submission_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                ticket_id: string;
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
                    "application/json": components["schemas"]["TpaSubmission"];
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
    confirm_tpa_submission_api_v1_tickets__ticket_id__tpa_submission_confirm_post: {
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
                "application/json": components["schemas"]["TpaSubmissionConfirmRequest"];
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
    healthcheck_mcp_insurance_registry_healthz_get: {
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
                        [key: string]: string;
                    };
                };
            };
        };
    };
    initialize_mcp_insurance_registry_initialize_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    [key: string]: unknown;
                };
            };
        };
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
    call_tool_mcp_insurance_registry_tools_call_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    [key: string]: unknown;
                };
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
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
    list_tools_mcp_insurance_registry_tools_list_get: {
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
    list_tools_mcp_insurance_registry_tools_list_post: {
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
    healthcheck_mcp_operations_healthz_get: {
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
                        [key: string]: string;
                    };
                };
            };
        };
    };
    initialize_mcp_operations_initialize_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    [key: string]: unknown;
                };
            };
        };
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
    call_tool_mcp_operations_tools_call_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    [key: string]: unknown;
                };
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
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
    list_tools_mcp_operations_tools_list_get: {
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
    list_tools_mcp_operations_tools_list_post: {
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
