# Authentication and Account Provisioning

## Core Rule

Clerk authenticates a person's identity; Epicenter authorizes what that person may access. Users must never select `nurse` during public sign-up, and no browser-supplied role, URL parameter, email pattern, or editable Clerk metadata may grant staff access.

Both panels may use the same Clerk instance and FastAPI backend, but they have different enrollment paths:

| Account | Enrollment | Epicenter authorization |
| --- | --- | --- |
| Patient | Public Clerk sign-up from the patient panel | The verified Clerk `sub` is mapped to one `patient_accounts` record |
| Nurse | Created manually or invited by an authorized clinic administrator; fake development inboxes must be created directly | The verified Clerk `sub` must match an active `staff_accounts` record with the required clinic and role scope |

## Patient Sign-Up

The patient panel is the only public account-creation surface. It must not show a role selector. A successfully verified new Clerk identity is treated only as a patient candidate.

After sign-up, the backend must:

1. verify the Clerk session token;
2. use its immutable `sub` as the account identifier;
3. create or resolve exactly one `patient_accounts` mapping;
4. attach only the authorized synthetic patient scenario for the demo; and
5. scope every patient API response to that mapping.

An email address helps Clerk verify identity, but email alone is not the authorization boundary and must not be used to grant nurse access.

## Nurse Provisioning

There is no public nurse sign-up. Nurses are provisioned through one of these controlled paths:

- an administrator creates the Clerk user and corresponding `staff_accounts` record; or
- an administrator sends a Clerk invitation, then activates the corresponding `staff_accounts` record after the invitation is accepted.

The nurse panel exposes sign-in only. Hiding the sign-up link is a user-interface safeguard, not sufficient authorization. Every nurse API route must independently verify that:

- the Clerk session is valid;
- its `sub` maps to an active staff record;
- the staff record has the required role and clinic scope; and
- any additional reverification requirement for a sensitive action is satisfied.

A signed-in patient who opens the nurse panel must receive `403 Nurse access required` from the backend. The frontend may then show a clear access-denied screen, but it must not be the only enforcement point.

For the hackathon, `staff_accounts` is the primary authorization source. Clerk Organizations and custom permissions may later represent clinic membership and coarse roles, but organization membership alone must never grant access to patient records.

The current Clerk development instance contains two directly created test users mapped in hosted Supabase: `nurse.noor+clerk_test@example.com` maps to `staff_noor`, and `nurse.aisyah+clerk_test@example.com` maps to `staff_aisyah`. Request an email code and use `424242`; Clerk suppresses delivery for these fake test inboxes. This flow is development-only and does not replace separately delivered production or judge credentials.

## Submission and Judge Flow

### Nurse Demonstration

Prepare a nurse account before judging and provide its credentials through the approved submission channel. The judge should be instructed to **sign in**, not sign up:

> Open the nurse panel and sign in using the provided clinic nurse account. Staff accounts are issued by the clinic and cannot be self-created.

Judge-specific nurse accounts are preferable because they preserve an individual audit trail. A shared demonstration account should be used only if the competition rules permit it, and its credentials must never be committed to the repository.

### Patient Demonstration

The judge opens the patient panel and selects **Create patient account**. For a Clerk development instance, each judge can use a unique test address such as `judge1+clerk_test@example.com` and the verification code `424242`. The exact same address cannot be signed up more than once, so use a unique address per judge or reset the corresponding Clerk test user between demonstrations.

Suggested instruction:

> Open the patient panel, create a patient account with the supplied unique test email, and enter verification code `424242`.

Clerk test addresses and the fixed verification code are intended for testing and development. Do not enable this convenience on a production Clerk instance. For a production-style deployment, judges should use an email inbox they can access or a pre-provisioned patient account.

## Required Demonstration Checks

Before submission, verify all of the following against the deployed applications and backend:

1. A new patient can complete patient sign-up and access only the linked synthetic patient record.
2. That same patient session receives `403` from every nurse endpoint.
3. The nurse panel does not expose a public sign-up path.
4. A pre-provisioned nurse can sign in and access only the permitted clinic and role scope.
5. An authenticated Clerk user without a `staff_accounts` mapping receives `403`, not nurse access.
6. A disabled staff record or wrong-clinic role receives `403`.
7. Sensitive nurse mutations require fresh reverification and create an attributable audit event.

## Current Implementation Status

Implemented and verified locally against the development Clerk and hosted Supabase projects:

- The patient panel exposes Clerk patient sign-up and sign-in without a role selector.
- After sign-up, the patient session token is sent to FastAPI and idempotently mapped to the configured synthetic demo scenario through `patient_accounts`.
- Patient registration and pre-arrival requests require the verified mapping in production mode and reject appointments owned by another patient.
- The nurse panel remains sign-in-only.
- FastAPI verifies Clerk session tokens, explicitly allowlists authorized frontend origins, and resolves one active `staff_accounts` role and clinic mapping for every staff request.
- Two administrator-created Clerk development nurse users are mapped to the active `staff_noor` and `staff_aisyah` rows without committing their provider IDs.
- Unit and API tests cover patient, registration nurse, operations administrator, auditor, disabled, unmapped, duplicate, and wrong-clinic authorization cases.
- Every currently implemented staff mutation requires Clerk strict reverification within ten minutes. The backend returns Clerk's standard reverification hint and the frontend retries through `useReverification` after the strongest configured factor succeeds.
- The live Playwright suite verifies patient signup, patient-to-nurse denial, nurse email-code sign-in, real Supabase-backed dashboard access, disabled-mapping denial, the Clerk verification prompt, and authenticated audit attribution. Temporary users and modified fixtures are restored during cleanup.

Repeat the local development-provider gate with:

```bash
cd frontend
npm run test:auth-live
```

The suite uses ignored local development keys, Clerk test identities, and hosted synthetic data. Do not point it at a production instance. Production nurse provisioning, credential handoff outside the repository, and a final deployed-flow rerun remain release gates under Task 11.

## Clerk References

- [Restricting sign-up and sign-in](https://clerk.com/docs/guides/secure/restricting-access)
- [Inviting application users](https://clerk.com/docs/guides/users/inviting)
- [Organization roles and permissions](https://clerk.com/docs/guides/organizations/control-access/roles-and-permissions)
- [Test emails and verification codes](https://clerk.com/docs/guides/development/testing/test-emails-and-phones)
- [Reverification](https://clerk.com/docs/guides/secure/reverification)
- [Playwright testing](https://clerk.com/docs/guides/development/testing/playwright/overview)
