// Generated from backend/app/main.py. Do not edit by hand.
// Run `npm run contracts:generate` from frontend/ after changing the API schema.

export interface paths {
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
        /**
         * PatientSubmissionOutcome
         * @enum {string}
         */
        PatientSubmissionOutcome: "under_review";
        /** PreArrivalSubmissionRequest */
        PreArrivalSubmissionRequest: {
            /** Appointment Id */
            appointment_id: string;
            coverage_action: components["schemas"]["CoverageAction"];
            /** File Name */
            file_name?: string | null;
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
        /** TicketTransitionRequest */
        TicketTransitionRequest: {
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
