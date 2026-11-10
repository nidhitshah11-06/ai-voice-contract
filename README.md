# AI Voice Contract

**Good promises deserve a good record.**

AI Voice Contract helps people turn an everyday spoken agreement into a clear, reviewable record. Record a short voice note, check the draft details, and save the agreement to your account so you can find it again.

| Project | Link |
|---|---|
| Source code | [GitHub repository](https://github.com/nidhitshah11-06/ai-voice-contract) |
| Live demo | Not published yet |

## The solution pitch

Every day, people make small commitments in conversation: a shopkeeper gives groceries on credit, a plumber agrees to finish a repair, or a neighbor promises to return a borrowed tool. These commitments matter, but the details can be easy to forget. Paperwork can feel like too much for an everyday promise, so people rely on memory, messages, or a scrap of paper.

**AI Voice Contract makes keeping a clear record feel as natural as making the agreement.** Speak in your own words. The app transcribes the recording and prepares a draft of details such as the person, amount, and due date. Review the original words, correct the draft if needed, and save the record to your private account.

We are not trying to turn daily life into legal paperwork. We are helping people remember what was agreed and when to follow up—starting with local businesses and expanding to anyone who wants a simpler way to keep track.

**AI Voice Contract isn’t about adding paperwork to life. It’s about helping people remember what matters.**

## Two-minute demo video script

**Length:** 2:00
**Demo setup:** Sign in to a fictional demo account before recording. Use fictional names and agreements. Keep secrets, email addresses, and real customer data off-screen.

| Time | Show | Friendly professional voice-over |
|---|---|---|
| 0:00–0:12 | A shop counter, a repair visit, and a handwritten reminder. | “Every day, people make small promises that matter. But when the details live only in conversation, it can be hard to remember exactly what was agreed.” |
| 0:12–0:23 | Open AI Voice Contract and show the signed-in dashboard. | “AI Voice Contract makes keeping a clear record feel as simple as making the agreement.” |
| 0:23–0:38 | Move quickly through all six scenario options: **shopkeeper credit**, **electrician or plumber**, **friend or family loan**, **rent or deposit**, **freelance work**, and **borrowed item**. | “It’s designed for everyday situations: shop credit, repair work, a personal loan, rent, freelance work, or something borrowed.” |
| 0:38–0:55 | Select Shopkeeper credit and record: “Priya ji, 500 rupaye udhaar, agle somvar tak de dena.” | “No long form and no special wording. Just speak naturally.” |
| 0:55–1:12 | Show the waveform, clean transcript, original words, and detected language. | “The voice service transcribes the recording and keeps the original words visible alongside the clean transcript.” |
| 1:12–1:28 | Review the person, amount, and due date; correct a field if needed. | “The app prepares a draft of important details. The user checks it and can correct anything before saving.” |
| 1:28–1:43 | Save the agreement, then open Agreements and Calendar. | “Once saved, the agreement is available in the user’s account, alongside its due date.” |
| 1:43–1:54 | Show the record detail and account overview. | “It’s a simpler way to return to what was agreed and remember when to follow up.” |
| 1:54–2:00 | End on the product name and tagline. | “AI Voice Contract. Good promises deserve a good record.” |

**Important demo note:** The app’s “YES” confirmation is simulated. Calendar dates appear in the app, but it does not currently send SMS, WhatsApp, email, or push reminders. Do not present those as live features.

## Use cases

- **Shopkeeper credit:** Record items given on credit and when payment is expected.
- **Electrician or plumber:** Keep a record of a job, agreed amount, and target date.
- **Friend or family loan:** Note an amount and expected repayment date.
- **Rent or deposit:** Keep a simple record of the amount and due date.
- **Freelance work:** Record a work agreement and expected payment date.
- **Borrowed item:** Note what was borrowed and when it should be returned.

These are record-keeping examples, not claims that the app creates a legally binding contract.

## How it works

1. A user creates an account or signs in with Supabase Auth.
2. They select an agreement scenario and record a short voice message in the browser.
3. The Streamlit app sends the audio to the Vachana speech API for verbatim and clean transcription.
4. Python rules prepare a draft of likely names, amounts, and due dates.
5. The user reviews and edits the draft.
6. The app saves the agreement to Supabase PostgreSQL.
7. The user can view saved agreements and due dates in the app.

The AI result is a draft: names, dates, and amounts can be misunderstood. The user should review the details before saving.

## Architecture

```text
Browser
  ├─ Streamlit UI and microphone capture
  └─ Python application
       ├─ Vachana API (Prisma v3.0) — speech transcription
       ├─ Python rules — draft field extraction
       └─ Supabase
            ├─ Auth — email/password accounts
            └─ PostgreSQL — agreements and calendar entries
                 └─ Row Level Security — restrict rows to their owner
```

The current product is a Streamlit application; it does not have a separate backend API or background worker.

## Technology stack

| Layer | Technology |
|---|---|
| Language | Python |
| Web application | Streamlit |
| Speech transcription | Vachana API, Prisma v3.0 |
| HTTP client | Requests |
| Authentication | Supabase Auth |
| Database | Supabase-hosted PostgreSQL |
| Per-user access control | PostgreSQL Row Level Security |
| Hosting | Streamlit Community Cloud |

## Run locally

### 1. Create and configure Supabase

Create a Supabase project, then run [`supabase/schema.sql`](supabase/schema.sql) in its SQL Editor. The schema creates the agreements and calendar tables and enables per-user Row Level Security.

### 2. Add local secrets

Create `.streamlit/secrets.toml` (this file is ignored by Git) with your own credentials:

```toml
GNANI_API_KEY = "YOUR_REPLACEMENT_VACHANA_API_KEY"

[supabase]
url = "https://YOUR_PROJECT_ID.supabase.co"
anon_key = "YOUR_SUPABASE_PUBLIC_ANON_OR_PUBLISHABLE_KEY"
```

Use the Supabase public anon/publishable key—not a `service_role` or secret key. Never commit secrets or paste them into issues, screenshots, or chat. If an API key has been exposed, revoke it and use a replacement.

### 3. Install and start

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Open [Streamlit Community Cloud](https://share.streamlit.io/) and connect GitHub.
2. Create an app from this repository, branch `main`, with `app.py` as the entry point.
3. In the app’s **Advanced settings → Secrets**, add the TOML configuration shown above using your own keys. Do not put credentials in the repository.
4. Deploy. The dependencies are listed in [`requirements.txt`](requirements.txt).
5. In Supabase **Authentication → URL Configuration**, set the Site URL to the deployed `*.streamlit.app` address and add that address to the allowed Redirect URLs.

Because account creation is public, visitors can use the configured speech API quota. Monitor usage and configure provider-side limits before sharing the app widely.

## Privacy and current limitations

- Supabase Row Level Security is intended to keep each user’s agreement and calendar records private to their account.
- The app stores the transcript and verbatim text with the agreement. It does not store raw audio in the agreements table.
- Public sign-up is enabled in the app; email confirmation behavior depends on Supabase project settings.
- The other-party confirmation flow is simulated, not a real message or acceptance.
- Calendar/reminder dates are displayed in the app; no external reminders are delivered.
- The product is a record-keeping aid, not legal advice or a guarantee of enforceability.
- Existing local JSON data is not automatically imported into Supabase.

## Project files

```text
app.py                 Streamlit app, authentication, recording, and review flow
agreements.py          Agreement database operations and agreement list
calendar_view.py       Calendar database operations and calendar UI
lang_data.py           Language and date phrase data
requirements.txt       Python dependencies for local and Cloud deployment
supabase/schema.sql    PostgreSQL tables, indexes, grants, and RLS policies
SUPABASE_SETUP.md      Supabase configuration notes
```

## Product direction

The next steps are to test with local users, measure how often transcripts and extracted fields need correction, improve multilingual and noisy-audio handling, and add opt-in real notifications only after the core record-keeping flow is trusted. For heavier usage, add monitoring, backups, rate limits, pagination, and background audio processing as needed.
