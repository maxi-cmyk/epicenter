# Authentication and Account Provisioning

## Core Rule

Clerk authenticates a person's identity; Epicenter authorizes what that person may access. Users must never select `nurse` during public sign-up, and no browser-supplied role, URL parameter, email pattern, or editable Clerk metadata may grant staff access.

Both panels may use the same Clerk instance and FastAPI backend, but they have different enrollment paths:

| Account | Enrollment | Epicenter authorization |
| --- | --- | --- |
| Patient | Public Clerk sign-up from the patient panel | The verified Clerk `sub` is mapped to one `patient_accounts` record |
| Nurse | Created manually or invited by an authorized clinic administrator | The verified Clerk `sub` must match an active `staff_accounts` record with the required clinic and role scope |

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

## Current Implementation Gap

The nurse frontend already renders Clerk sign-in with sign-up disabled. However, the current backend `require_staff` dependency verifies a valid Clerk session but does not yet look up an active `staff_accounts` role and clinic scope. Therefore, sign-in-only presentation must not be described as complete nurse authorization until this server-side check is implemented and tested.

The patient panel also does not yet implement the Clerk sign-up and `patient_accounts` mapping flow described above. These are required before using the proposed judge instructions.

## Clerk References

- [Restricting sign-up and sign-in](https://clerk.com/docs/guides/secure/restricting-access)
- [Inviting application users](https://clerk.com/docs/guides/users/inviting)
- [Organization roles and permissions](https://clerk.com/docs/guides/organizations/control-access/roles-and-permissions)
- [Test emails and verification codes](https://clerk.com/docs/guides/development/testing/test-emails-and-phones)
