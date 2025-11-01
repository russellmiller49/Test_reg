# Online Annotation Portal

This guide shows how to stand up a lightweight, shareable annotation workspace so collaborators can label notes without cloning the full codebase. The flow uses:

- **Supabase** to host notes + annotation records (free tier is enough).
- The existing `tools/annotate_streamlit.py` UI, now capable of talking to Supabase.
- An optional Streamlit Community Cloud deployment so collaborators only need a browser.

> ⚠️ Only upload PHI‑free text. Supabase and Streamlit are cloud services—treat them as external systems.

---

## 1. Prepare the notes

1. Collect the de‑identified notes you want annotated and export each note as its own UTF‑8 `.txt` file.
2. Drop them in `data/synthetic_notes/` (or another directory of your choosing).

You can reuse the existing synthetic generator (`python tools/phi_synthesizer.py ...`) or populate the folder manually.

---

## 2. Create Supabase tables

1. Sign in at [supabase.com](https://supabase.com) and create a new project.
2. In the SQL editor run:

```sql
create table if not exists public.bronch_notes (
  id text primary key,
  display_label text,
  filename text,
  note_text text not null,
  raw_text_hash text,
  tags jsonb default '[]'::jsonb,
  created_at timestamptz default now()
);

create table if not exists public.bronch_annotations (
  id uuid primary key default gen_random_uuid(),
  note_id text not null references public.bronch_notes(id) on delete cascade,
  annotator text not null,
  record jsonb not null,
  raw_text_hash text,
  submitted_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table public.bronch_notes enable row level security;
create policy "allow note reads" on public.bronch_notes for select using (true);

alter table public.bronch_annotations enable row level security;
create policy "allow annotation reads" on public.bronch_annotations for select using (true);
create policy "allow annotation writes" on public.bronch_annotations for insert with check (true);
create policy "allow annotation updates" on public.bronch_annotations for update using (true) with check (true);
```

These policies let collaborators (using the anon key) read notes and write annotations while keeping the service role key private.

---

## 3. Seed notes into Supabase

Use the helper script to push your `.txt` files:

```bash
pip install supabase  # if not already installed
export SUPABASE_URL="https://<your-project>.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="<service-role-key>"
python tools/supabase_seed.py --note-dir data/synthetic_notes
```

You can override the target table with `--notes-table` if you chose a different name.

---

## 4. Deploy the annotation UI

### Option A – Streamlit Community Cloud

1. Create a new GitHub repo that only contains the files needed for the portal:
   - `tools/annotate_streamlit.py`
   - `tools/annotation_backend.py`
   - `tools/ui_helpers.py`
   - `tools/writer.py`
   - `bronch_schema/` package
   - `requirements.txt`
2. On [streamlit.io](https://streamlit.io/cloud), create a new app pointing at that repo and `tools/annotate_streamlit.py`.
3. In **App secrets**, add:

```toml
[backend]
type = "supabase"

[supabase]
url = "https://<your-project>.supabase.co"
anon_key = "<anon-key>"
notes_table = "bronch_notes"
annotations_table = "bronch_annotations"
```

4. Deploy. Share the resulting URL with collaborators.

### Option B – Local deployment

Run the Streamlit app locally while still persisting to Supabase:

```bash
export ANNOTATION_BACKEND="supabase"
export SUPABASE_URL="https://<your-project>.supabase.co"
export SUPABASE_ANON_KEY="<anon-key>"
streamlit run tools/annotate_streamlit.py
```

---

## 5. Collaborator workflow

1. Open the hosted URL.
2. Enter initials or a short identifier in the sidebar (“Annotator ID / initials”).
3. Pick an unannotated note (marked ⏳) and complete the form.
4. Save. The record is written to `bronch_annotations` with the validated schema (same as local v2.2).

The progress counters update automatically; annotated notes show a ✅ badge.

---

## 6. Reviewing and exporting annotations

Query Supabase anytime:

```sql
select
  note_id,
  annotator,
  submitted_at,
  record -> 'procedure' ->> 'procedure_date' as procedure_date
from public.bronch_annotations
order by submitted_at desc;
```

To retrieve full records from the CLI:

```bash
supabase db pull --table bronch_annotations > annotations.json
```

or use the Supabase UI to export CSV/JSON. Each row's `record` column matches the `GoldRecord` schema, so you can pipe the JSONL directly back into the evaluation harness if desired.

---

## 7. Operational tips

- Rotate the anon key if it leaks; the UI pulls configuration from Streamlit secrets.
- Delete or archive notes once they are fully annotated if you want to reclaim storage.
- Consider creating a view that joins `bronch_notes` with the latest `bronch_annotations` for QA dashboards.
- Keep the service role key **private**. Only use it locally for seeding.

With this setup, collaborators only need a browser, while you retain control of the dataset and schema validation. The same Streamlit UI continues to work locally (filesystem mode) for offline annotation sessions.
