// Generated from backend/app/main.py. Do not edit by hand.
// Run `npm run contracts:generate` from frontend/ after changing the API schema.

export interface paths {
    "/api/v1/assistant": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Ask Nurse Assistant
         * @description Answer one bounded staff question through the server-side Responses API.
         */
        post: operations["ask_nurse_assistant_api_v1_assistant_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
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
    "/api/v1/patient/coverage/prior": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Prior Coverage */
        get: operations["get_prior_coverage_api_v1_patient_coverage_prior_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/patient/home": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Home */
        get: operations["get_home_api_v1_patient_home_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/patient/onboarding": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Onboarding */
        get: operations["get_onboarding_api_v1_patient_onboarding_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/patient/onboarding/advance": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Advance Onboarding */
        post: operations["advance_onboarding_api_v1_patient_onboarding_advance_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/patient/onboarding/coverage": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Submit Onboarding Coverage */
        post: operations["submit_onboarding_coverage_api_v1_patient_onboarding_coverage_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/patient/payment": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Payment */
        get: operations["get_payment_api_v1_patient_payment_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/patient/payment/mock-pay": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Mock Pay */
        post: operations["mock_pay_api_v1_patient_payment_mock_pay_post"];
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
    "/api/v1/patient/questionnaire": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Questionnaire */
        get: operations["get_questionnaire_api_v1_patient_questionnaire_get"];
        put?: never;
        /** Save Questionnaire */
        post: operations["save_questionnaire_api_v1_patient_questionnaire_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/patient/queue": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Queue */
        get: operations["get_queue_api_v1_patient_queue_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/patient/records": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Records */
        get: operations["get_records_api_v1_patient_records_get"];
        put?: never;
        post?: never;
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
    "/api/v1/patient/upload-links/{token}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Resolve Upload Link
         * @description Appointment-scoped upload session. Does not create a patient account.
         */
        get: operations["resolve_upload_link_api_v1_patient_upload_links__token__get"];
        put?: never;
        post?: never;
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
    "/api/v1/tickets/{ticket_id}/forms/confirm": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Confirm Forms */
        post: operations["confirm_forms_api_v1_tickets__ticket_id__forms_confirm_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tickets/{ticket_id}/identity/confirm": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Confirm Identity */
        post: operations["confirm_identity_api_v1_tickets__ticket_id__identity_confirm_post"];
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
    "/api/v1/tickets/{ticket_id}/physical-forms/received": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Mark Physical Forms Received */
        post: operations["mark_physical_forms_received_api_v1_tickets__ticket_id__physical_forms_received_post"];
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
    "/mcp/insurance-registry": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Streamable Http */
        post: operations["streamable_http_mcp_insurance_registry_post"];
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
    "/mcp/operations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Streamable Http
         * @description Stateless Streamable HTTP JSON-RPC endpoint for independent MCP clients.
         */
        post: operations["streamable_http_mcp_operations_post"];
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
        /**
         * AssistantMessage
         * @description A single grounded assistant reply returned to the nurse panel.
         */
        AssistantMessage: {
            /**
             * Content
             * @description Grounded, plain-language reply from the assistant.
             */
            content: string;
            /** Model */
            model?: string | null;
            /** Openai Response Id */
            openai_response_id?: string | null;
            /**
             * Snapshot Time
             * @description ISO timestamp of the most recent data snapshot used.
             */
            snapshot_time?: string | null;
            /**
             * Source Labels
             * @description Human-readable labels identifying the tool results used (e.g. 'queue snapshot 09:42').
             */
            source_labels?: string[];
            /**
             * Synthetic
             * @default true
             */
            synthetic: boolean;
            usage?: components["schemas"]["AssistantUsage"] | null;
        };
        /**
         * AssistantRequest
         * @description One bounded staff question sent to the server-side assistant.
         */
        AssistantRequest: {
            /** Message */
            message: string;
        };
        /**
         * AssistantUsage
         * @description Provider usage returned without exposing prompts, tool payloads, or credentials.
         */
        AssistantUsage: {
            /**
             * Input Tokens
             * @default 0
             */
            input_tokens: number;
            /**
             * Output Tokens
             * @default 0
             */
            output_tokens: number;
            /**
             * Total Tokens
             * @default 0
             */
            total_tokens: number;
        };
        /** AuditRecord */
        AuditRecord: {
            /** Action Type */
            action_type: string;
            /** Actor Reference */
            actor_reference: string;
            /** Actor Role */
            actor_role?: string | null;
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
        /** FormsConfirmRequest */
        FormsConfirmRequest: {
            /** Expected Version */
            expected_version: number;
            /** Idempotency Key */
            idempotency_key: string;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** IdentityConfirmRequest */
        IdentityConfirmRequest: {
            /** Ecard Na Reason */
            ecard_na_reason?: string | null;
            /**
             * Ecard Not Applicable
             * @default false
             */
            ecard_not_applicable: boolean;
            /** Expected Version */
            expected_version: number;
            /** Idempotency Key */
            idempotency_key: string;
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
            /**
             * Is Checkup
             * @default false
             */
            is_checkup: boolean;
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
        /** MockPaymentRequest */
        MockPaymentRequest: {
            /** Appointment Id */
            appointment_id: string;
            /**
             * Expected Version
             * @default 1
             */
            expected_version: number;
            /**
             * Idempotency Key
             * @default demo-mock-payment
             */
            idempotency_key: string;
        };
        /** OnboardingAdvanceRequest */
        OnboardingAdvanceRequest: {
            /**
             * Idempotency Key
             * @default demo-onboarding
             */
            idempotency_key: string;
            /** Insurance Completed */
            insurance_completed?: boolean | null;
            /** Questionnaire Completed */
            questionnaire_completed?: boolean | null;
            /** Singpass Authenticated */
            singpass_authenticated?: boolean | null;
            /** Singpass Fields */
            singpass_fields?: components["schemas"]["SingpassProfileField"][] | null;
            step: components["schemas"]["OnboardingStep"];
        };
        /** OnboardingCoverageRequest */
        OnboardingCoverageRequest: {
            /** File Name */
            file_name: string;
            /**
             * Idempotency Key
             * @default demo-onboarding-coverage
             */
            idempotency_key: string;
        };
        /**
         * OnboardingStep
         * @enum {string}
         */
        OnboardingStep: "singpass" | "insurance" | "questionnaire" | "complete";
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
            /**
             * Onboarding Completed
             * @default false
             */
            onboarding_completed: boolean;
            /**
             * Onboarding Step
             * @default singpass
             */
            onboarding_step: string;
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
        /** PatientAppointmentSummary */
        PatientAppointmentSummary: {
            /** Appointment Id */
            appointment_id: string;
            /** Appointment Type */
            appointment_type: string;
            /** Clinic Name */
            clinic_name: string;
            /** Location */
            location: string;
            /** Questionnaire Type */
            questionnaire_type: string;
            /**
             * Scheduled At
             * Format: date-time
             */
            scheduled_at: string;
        };
        /**
         * PatientCoverageStatus
         * @enum {string}
         */
        PatientCoverageStatus: "not_started" | "check_first" | "submitted" | "action_required";
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
        /** PatientHome */
        PatientHome: {
            appointment?: components["schemas"]["PatientAppointmentSummary"] | null;
            coverage_status: components["schemas"]["PatientCoverageStatus"];
            /** Coverage Summary */
            coverage_summary: string;
            notification?: components["schemas"]["PatientNotificationBanner"] | null;
            outcome?: components["schemas"]["PatientSubmissionOutcome"] | null;
            /** Outcome Message */
            outcome_message?: string | null;
            /** Patient Display Name */
            patient_display_name: string;
            payment_status: components["schemas"]["PatientPaymentStatus"];
            /** Payment Summary */
            payment_summary: string;
            primary_action: components["schemas"]["PatientNextAction"];
            /** Primary Action Href */
            primary_action_href: string;
            /** Primary Action Label */
            primary_action_label: string;
            questionnaire_status: components["schemas"]["PatientQuestionnaireStatus"];
            /** Queue Summary */
            queue_summary: string;
            /** Recent Visit Summary */
            recent_visit_summary?: string | null;
            /**
             * Synthetic
             * @default true
             */
            synthetic: boolean;
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
        /**
         * PatientNextAction
         * @enum {string}
         */
        PatientNextAction: "confirm_coverage" | "upload_coverage" | "complete_questionnaire" | "wait_for_review" | "view_queue" | "pay" | "none";
        /** PatientNotificationBanner */
        PatientNotificationBanner: {
            /** Category */
            category: string;
            /** Message */
            message: string;
            /** Next Action */
            next_action: string;
        };
        /** PatientOnboardingState */
        PatientOnboardingState: {
            /** Appointment Id */
            appointment_id: string;
            /**
             * Completed
             * @default false
             */
            completed: boolean;
            /** @default singpass */
            current_step: components["schemas"]["OnboardingStep"];
            /**
             * Insurance Completed
             * @default false
             */
            insurance_completed: boolean;
            /**
             * Next Href
             * @default /onboarding
             */
            next_href: string;
            /**
             * Questionnaire Completed
             * @default false
             */
            questionnaire_completed: boolean;
            /**
             * Singpass Authenticated
             * @default false
             */
            singpass_authenticated: boolean;
            /** Singpass Fields */
            singpass_fields: components["schemas"]["SingpassProfileField"][];
            /**
             * Synthetic
             * @default true
             */
            synthetic: boolean;
        };
        /**
         * PatientPaymentStatus
         * @enum {string}
         */
        PatientPaymentStatus: "not_ready" | "ready" | "mock_processing" | "mocked_paid" | "mock_failed";
        /** PatientPaymentSummary */
        PatientPaymentSummary: {
            /** Amount Covered */
            amount_covered: string;
            /** Amount Patient Payable */
            amount_patient_payable: string;
            /** Appointment Id */
            appointment_id?: string | null;
            /** Failure Reason */
            failure_reason?: string | null;
            /**
             * Mocked
             * @default true
             */
            mocked: boolean;
            /** Package Label */
            package_label: string;
            /** Paid At */
            paid_at?: string | null;
            /** Receipt Reference */
            receipt_reference?: string | null;
            status: components["schemas"]["PatientPaymentStatus"];
            /** Status Detail */
            status_detail: string;
            /**
             * Synthetic
             * @default true
             */
            synthetic: boolean;
            /**
             * Version
             * @default 1
             */
            version: number;
        };
        /** PatientQuestionnaire */
        PatientQuestionnaire: {
            /** Appointment Id */
            appointment_id: string;
            /**
             * Declaration Acknowledged
             * @default false
             */
            declaration_acknowledged: boolean;
            /** Fields */
            fields: components["schemas"]["QuestionnaireInputField"][];
            /** Prefill */
            prefill: components["schemas"]["QuestionnairePrefillField"][];
            /** Questionnaire Type */
            questionnaire_type: string;
            status: components["schemas"]["PatientQuestionnaireStatus"];
            /**
             * Synthetic
             * @default true
             */
            synthetic: boolean;
            /** Title */
            title: string;
            /**
             * Version
             * @default 1
             */
            version: number;
        };
        /**
         * PatientQuestionnaireStatus
         * @enum {string}
         */
        PatientQuestionnaireStatus: "not_required" | "not_started" | "draft" | "submitted";
        /** PatientQueueStatus */
        PatientQueueStatus: {
            /** Available */
            available: boolean;
            /** Counter Label */
            counter_label?: string | null;
            /** Patients Ahead */
            patients_ahead?: number | null;
            /**
             * Payment Ready
             * @default false
             */
            payment_ready: boolean;
            /**
             * Stale
             * @default false
             */
            stale: boolean;
            /** Status Detail */
            status_detail: string;
            /** Status Label */
            status_label: string;
            /**
             * Synthetic
             * @default true
             */
            synthetic: boolean;
            /** Ticket Id */
            ticket_id?: string | null;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            visit_phase?: components["schemas"]["VisitPhase"] | null;
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
        /** PatientVisitHistory */
        PatientVisitHistory: {
            /**
             * Synthetic
             * @default true
             */
            synthetic: boolean;
            /** Visits */
            visits: components["schemas"]["PatientVisitRecord"][];
        };
        /** PatientVisitRecord */
        PatientVisitRecord: {
            /** Appointment Id */
            appointment_id: string;
            /** Coverage Label */
            coverage_label?: string | null;
            outcome?: components["schemas"]["PatientSubmissionOutcome"] | null;
            /** Package Label */
            package_label?: string | null;
            /** Questionnaire Summary */
            questionnaire_summary?: string | null;
            /** Visit Label */
            visit_label: string;
            /**
             * Visited On
             * Format: date
             */
            visited_on: string;
        };
        /** PhysicalFormsReceivedRequest */
        PhysicalFormsReceivedRequest: {
            /** Expected Version */
            expected_version: number;
            /** Idempotency Key */
            idempotency_key: string;
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
        /** PriorCoverageSummary */
        PriorCoverageSummary: {
            /** Appointment Id */
            appointment_id: string;
            /** Document Date */
            document_date?: string | null;
            /**
             * Force Upload
             * @default false
             */
            force_upload: boolean;
            /** Has Prior Coverage */
            has_prior_coverage: boolean;
            /** Issuer Name */
            issuer_name?: string | null;
            notification?: components["schemas"]["PatientNotificationBanner"] | null;
            /** Prompt */
            prompt: string;
            /**
             * Synthetic
             * @default true
             */
            synthetic: boolean;
        };
        /** QuestionnaireInputField */
        QuestionnaireInputField: {
            /** Field Id */
            field_id: string;
            /** Field Type */
            field_type: string;
            /** Help Text */
            help_text?: string | null;
            /** Label */
            label: string;
            /** Options */
            options?: string[];
            /**
             * Required
             * @default true
             */
            required: boolean;
            /** Section */
            section?: string | null;
            /** Show If Field */
            show_if_field?: string | null;
            /** Show If Field 2 */
            show_if_field_2?: string | null;
            /**
             * Show If Mode
             * @default equals
             */
            show_if_mode: string;
            /**
             * Show If Mode 2
             * @default equals
             */
            show_if_mode_2: string;
            /** Show If Value */
            show_if_value?: string | null;
            /** Show If Value 2 */
            show_if_value_2?: string | null;
            /** Value */
            value?: string | null;
        };
        /** QuestionnairePrefillField */
        QuestionnairePrefillField: {
            /**
             * Editable
             * @default false
             */
            editable: boolean;
            /** Field Id */
            field_id: string;
            /** Label */
            label: string;
            /** Source */
            source: string;
            /** Value */
            value: string;
        };
        /** QuestionnaireSaveRequest */
        QuestionnaireSaveRequest: {
            /** Answers */
            answers?: {
                [key: string]: string | null;
            };
            /** Appointment Id */
            appointment_id: string;
            /**
             * Declaration Acknowledged
             * @default false
             */
            declaration_acknowledged: boolean;
            /**
             * Expected Version
             * @default 1
             */
            expected_version: number;
            /**
             * Idempotency Key
             * @default demo-questionnaire
             */
            idempotency_key: string;
            /**
             * Submit
             * @default false
             */
            submit: boolean;
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
            /** Completed At */
            completed_at?: string | null;
            /**
             * Documents
             * @default []
             */
            documents: components["schemas"]["Document"][];
            /** Ecard Na Reason */
            ecard_na_reason?: string | null;
            /**
             * Ecard Not Applicable
             * @default false
             */
            ecard_not_applicable: boolean;
            /**
             * Ecard Verified
             * @default false
             */
            ecard_verified: boolean;
            /** Expected Room */
            expected_room?: string | null;
            /**
             * Forms Confirmed
             * @default false
             */
            forms_confirmed: boolean;
            /** Forms Confirmed At */
            forms_confirmed_at?: string | null;
            /** Forms Confirmed By */
            forms_confirmed_by?: string | null;
            /** Id */
            id: string;
            /**
             * Identity Confirmed
             * @default false
             */
            identity_confirmed: boolean;
            /** Identity Confirmed At */
            identity_confirmed_at?: string | null;
            /** Identity Confirmed By */
            identity_confirmed_by?: string | null;
            intake_type: components["schemas"]["IntakeType"];
            /**
             * Is Checkup
             * @default false
             */
            is_checkup: boolean;
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
            /**
             * Physical Forms Received
             * @default false
             */
            physical_forms_received: boolean;
            /** Physical Forms Received At */
            physical_forms_received_at?: string | null;
            /** Physical Forms Received By */
            physical_forms_received_by?: string | null;
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
        /** SingpassProfileField */
        SingpassProfileField: {
            /**
             * Editable
             * @default false
             */
            editable: boolean;
            /** Field Id */
            field_id: string;
            /** Label */
            label: string;
            /**
             * Source
             * @default Singpass / Myinfo (synthetic)
             */
            source: string;
            /** Value */
            value: string;
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
            visit_phase?: components["schemas"]["VisitPhase"] | null;
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
        /** UploadLinkSession */
        UploadLinkSession: {
            /** Appointment Id */
            appointment_id?: string | null;
            /** Message */
            message: string;
            /** Next Action */
            next_action: string;
            /** Scheduled At */
            scheduled_at?: string | null;
            /**
             * Synthetic
             * @default true
             */
            synthetic: boolean;
            /** Valid */
            valid: boolean;
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
    ask_nurse_assistant_api_v1_assistant_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AssistantRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssistantMessage"];
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
    list_audit_api_v1_audit_get: {
        parameters: {
            query?: {
                action_type?: string | null;
                actor?: string | null;
                actor_role?: string | null;
                limit?: number;
                occurred_from?: string | null;
                occurred_to?: string | null;
                offset?: number;
                outcome?: string | null;
                search?: string | null;
                target_table?: string | null;
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
    get_prior_coverage_api_v1_patient_coverage_prior_get: {
        parameters: {
            query: {
                appointment_id: string;
                first_visit?: boolean;
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
                    "application/json": components["schemas"]["PriorCoverageSummary"];
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
    get_home_api_v1_patient_home_get: {
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
                    "application/json": components["schemas"]["PatientHome"];
                };
            };
        };
    };
    get_onboarding_api_v1_patient_onboarding_get: {
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
                    "application/json": components["schemas"]["PatientOnboardingState"];
                };
            };
        };
    };
    advance_onboarding_api_v1_patient_onboarding_advance_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["OnboardingAdvanceRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PatientOnboardingState"];
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
    submit_onboarding_coverage_api_v1_patient_onboarding_coverage_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["OnboardingCoverageRequest"];
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
    get_payment_api_v1_patient_payment_get: {
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
                    "application/json": components["schemas"]["PatientPaymentSummary"];
                };
            };
        };
    };
    mock_pay_api_v1_patient_payment_mock_pay_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MockPaymentRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PatientPaymentSummary"];
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
    get_questionnaire_api_v1_patient_questionnaire_get: {
        parameters: {
            query: {
                appointment_id: string;
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
                    "application/json": components["schemas"]["PatientQuestionnaire"];
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
    save_questionnaire_api_v1_patient_questionnaire_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["QuestionnaireSaveRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PatientQuestionnaire"];
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
    get_queue_api_v1_patient_queue_get: {
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
                    "application/json": components["schemas"]["PatientQueueStatus"];
                };
            };
        };
    };
    get_records_api_v1_patient_records_get: {
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
                    "application/json": components["schemas"]["PatientVisitHistory"];
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
    resolve_upload_link_api_v1_patient_upload_links__token__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                token: string;
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
                    "application/json": components["schemas"]["UploadLinkSession"];
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
                contact_filter?: string;
                limit?: number;
                offset?: number;
                search?: string | null;
                sort?: string;
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
    confirm_forms_api_v1_tickets__ticket_id__forms_confirm_post: {
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
                "application/json": components["schemas"]["FormsConfirmRequest"];
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
    confirm_identity_api_v1_tickets__ticket_id__identity_confirm_post: {
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
                "application/json": components["schemas"]["IdentityConfirmRequest"];
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
    mark_physical_forms_received_api_v1_tickets__ticket_id__physical_forms_received_post: {
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
                "application/json": components["schemas"]["PhysicalFormsReceivedRequest"];
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
    streamable_http_mcp_insurance_registry_post: {
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
    streamable_http_mcp_operations_post: {
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
