export type Json = boolean | number | string | null | Json[] | { [key: string]: Json | undefined };

export type Database = {
  public: {
    Tables: {
      patients: {
        Row: {
          id: number;
          source_record_key: string;
          identifier_hash: string;
          identifier_masked: string;
          full_name: string;
          sex: string | null;
          nationality: string | null;
          date_of_birth: string | null;
          address: string | null;
          postal_code: string | null;
          contact_home: string | null;
          contact_office: string | null;
          contact_mobile: string | null;
          email: string | null;
          drug_allergy: string | null;
          is_synthetic: boolean;
          imported_at: string;
        };
        Insert: never;
        Update: never;
        Relationships: [];
      };
      questionnaire_submissions: {
        Row: {
          id: number;
          source_record_key: string;
          questionnaire_type: "general_health" | "occupational_health";
          subject_identifier_hash: string;
          subject_identifier_masked: string;
          subject_name: string;
          subject_date_of_birth: string | null;
          subject_email: string | null;
          patient_id: number | null;
          candidate_patient_id: number | null;
          verification_status: "verified" | "conflict" | "no_registration" | "ambiguous";
          verification_evidence: Json;
          acknowledged: boolean | null;
          consent_to_disclose: boolean | null;
          signed_on: string | null;
          response_payload: Json;
          is_synthetic: boolean;
          imported_at: string;
        };
        Insert: never;
        Update: never;
        Relationships: [];
      };
      medical_document_samples: {
        Row: {
          id: number;
          source_record_key: string;
          issuer_code: string;
          issuer_name: string;
          document_kind: string;
          subject_name: string | null;
          subject_identifier_hash: string | null;
          subject_identifier_masked: string | null;
          patient_id: number | null;
          issued_on: string | null;
          expires_on: string | null;
          appointment_at: string | null;
          requirements: Json;
          administrative_facts: Json;
          automation_disposition: "confirm" | "staff_review";
          review_reason: string | null;
          is_synthetic: boolean;
          imported_at: string;
        };
        Insert: never;
        Update: never;
        Relationships: [];
      };
    };
    Views: Record<string, never>;
    Functions: Record<string, never>;
    Enums: Record<string, never>;
    CompositeTypes: Record<string, never>;
  };
};
