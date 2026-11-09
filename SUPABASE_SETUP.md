# Supabase setup

The app uses Supabase Auth for email/password accounts and PostgreSQL for
agreements and calendar entries. Row-level security policies restrict every
record to its owner.

1. Create a Supabase project at [supabase.com](https://supabase.com/).
2. In the project's **SQL Editor**, run [`supabase/schema.sql`](./supabase/schema.sql).
3. In **Project Settings → API**, copy the project URL and the public anon
   (publishable) key. Do not use or expose the `service_role`/secret key.
4. Add these values to `.streamlit/secrets.toml`, preserving any existing
   application secrets:

   ```toml
   [supabase]
   url = "https://YOUR_PROJECT_ID.supabase.co"
   anon_key = "YOUR_PUBLIC_ANON_KEY"
   ```

5. In **Authentication → Providers → Email**, keep email/password enabled.
   Email confirmation may remain enabled; a new user will be asked to confirm
   their email before signing in.
6. Install the project dependencies and start the app:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   pip install -r Requirements.txt
   streamlit run app.py
   ```

Users can create their own account from the app's sign-in screen. Existing local
JSON data is not automatically imported into Supabase.
