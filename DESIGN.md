# Design Doc: Care Plan Service

## 1. Overview

**Customer:** A specialty pharmacy (CVS)

**Problem:** Pharmacists currently spend 20–40 minutes per patient manually
writing care plans. This is required for compliance and for reimbursement
from Medicare and pharma. The team is short-staffed and backlogged.

**Solution:** A backend service that lets a medical assistant enter patient
and order information through a webform, validates that data, detects
duplicate patients/orders/providers, and calls an LLM to generate a care
plan that can be downloaded as a text file and exported for pharma
reporting.

## 2. Users

- **Primary user:** CVS medical workers (pharmacists / medical assistants).
  Patients do not interact with the system directly.
- **Workflow:** A medical worker enters order info when a medication is
  prescribed, the system generates a care plan, the worker prints it and
  hands it to the patient.

## 3. Core Concepts

- **One care plan = one order = one medication.** A patient with multiple
  medications gets multiple care plans (one per order).
- **Care plan output must include:**
  - Problem list / Drug therapy problems (DTPs)
  - Goals (SMART)
  - Pharmacist interventions / plan
  - Monitoring plan & lab schedule

## 4. Data Model (Inputs)

| Field | Type | Notes |
| --- | --- | --- |
| Patient First Name | string | |
| Patient Last Name | string | |
| Referring Provider | string | |
| Referring Provider NPI | 10-digit number | unique identifier for provider |
| Patient MRN | unique 6-digit number | unique identifier for patient |
| Patient Primary Diagnosis | ICD-10 code | |
| Medication Name | string | defines the order |
| Additional Diagnosis | list of ICD-10 codes | |
| Medication History | list of strings | |
| Patient Records | string or PDF | supporting clinical context for LLM |

## 5. Duplicate Detection Rules

| Scenario | Handling | Reason |
| --- | --- | --- |
| Same patient + same medication + **same day** | ❌ **ERROR** — block | Certain duplicate submission |
| Same patient + same medication + **different day** | ⚠️ **WARNING** — allow to confirm & continue | Could be a refill |
| Same MRN + different name or DOB | ⚠️ **WARNING** — allow to confirm & continue | Possible data-entry error |
| Same name + DOB + different MRN | ⚠️ **WARNING** — allow to confirm & continue | Could be the same person |
| Same NPI + different provider name | ❌ **ERROR** — must be corrected | NPI is the unique identifier for a provider |

Providers are entered into the system once (keyed by NPI) and reused across
orders.

## 6. Feature Requirements (MVP)

| Feature | Required | Notes |
| --- | --- | --- |
| Patient/order duplicate detection | ✅ | Must not disrupt existing workflow |
| Care plan generation (via LLM) | ✅ | Core value of the product |
| Provider duplicate detection | ✅ | Affects pharma reporting accuracy |
| Export report | ✅ | Needed for pharma reporting |
| Care plan download | ✅ | Users upload the result into their own systems |

## 7. Production-Readiness Requirements

- Every input is validated.
- Integrity rules always enforce consistency (e.g., one provider record per NPI).
- Errors are safe, clear, and contained — warnings vs. errors are handled distinctly.
- Code is modular and navigable.
- Critical logic (duplicate detection, validation) is covered by automated tests.
- The project runs end-to-end out of the box.

## 8. Tech Stack

Python, Django REST Framework, PostgreSQL, Celery, Redis, LLM APIs.

## 9. Open Questions (to revisit as the design evolves)

- Exact LLM prompt/response contract for care plan generation.
- Exact export format required for pharma reporting.
- Auth/access control model for medical workers.
- Async processing: does LLM generation need to be handled via Celery given response time?

---
*This is a first-pass design doc based on the clarified requirements from
Day 1 (needs analysis). Details will be refined as the project develops.*
