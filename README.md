GM Stream + CBOR TTS (Cloud Run-ready) 

Overview
- FastAPI backend streams LLM output, splits into linguistically-aware fragments (spaCy), synthesizes each fragment via Google Text-to-Speech using SSML, and streams binary frames (CBOR meta + raw audio) to a browser client that schedules gap-free playback.

Repo layout
- backend/ : FastAPI app, TTS, cache index
- frontend/ : static UI
- scripts/make_tarball.sh : create tarball for upload

Quick start (local)
1) Create project folder and paste files:
   mkdir gm-tts && cd gm-tts
   mkdir backend frontend scripts
   # create files per the repo layout (paste the files in the README)

2) Create venv & install:
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm

3) Configure env:
   cp .env.example .env
   export $(cat .env | xargs)   # or set env variables manually
   Ensure GOOGLE_APPLICATION_CREDENTIALS points to a valid service account JSON

4) Run:
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload

5) Open http://localhost:8000 and test.

Cloud Run deployment (overview)
- Build & push image:
  gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/gm-tts
- Deploy:
  gcloud run deploy gm-tts --image gcr.io/YOUR_PROJECT_ID/gm-tts --platform managed --region YOUR_REGION --allow-unauthenticated
- Grant the Cloud Run service account permission to use Text-to-Speech and Storage (roles/texttospeech.admin, roles/storage.objectAdmin OR narrower roles).

GCS cache TTL & index
- The backend keeps a small index (audio_cache/index.json) in your GCS bucket to track timestamps and sizes; purge_older_than runs on new synthesizes and deletes items older than TTL.

Drive OAuth & per-user saves (notes)
- The repo contains placeholders for Drive OAuth variables. Implement these steps to enable per-user saves:
  1) Create OAuth client in Google Cloud Console (OAuth consent + credentials).
  2) Add redirect URI (e.g., https://your-cloud-run-url/oauth2callback or localhost-based).
  3) Implement endpoints to start oauth flow (/auth/drive), and callback (/oauth2callback) to exchange code for tokens and store refresh tokens per user.
  4) Use googleapiclient or google-auth libraries to upload files to user's Drive.

Why CBOR and GCS
- CBOR reduces overhead vs JSON/base64 and is robust for binary framing.
- GCS cache keeps audio fragments persistent across instances, lowering TTS cost.

Switching to protobuf
- If you prefer protobuf framing, define a simple message:
  message AudioMeta { string id = 1; string encoding = 2; uint32 length = 3; }
- Compile .proto to Python and JS; then write a 4-byte metaLen + protoBytes + audio bytes frame similarly.

Next steps I can deliver
- Produce a git-ready tarball (I can generate and provide a downloadable tar.gz of the repo).
- Add Drive OAuth handlers and example UI for per-user login & saves.
- Replace CBOR CDN with an npm-bundled CBOR library and convert frontend to React.
- Add more advanced SSML mapping from Memory Summary emotional beats (use an emotion classifier to pick presets).
- Add a small metrics endpoint (cache hits, synth count).

If you'd like, I’ll:
- Generate and upload the repo tarball for you to download now; OR
- Walk you through creating the files on your machine step-by-step and running locally.

Which would you prefer? I can produce the tarball right now for you to download, or (if you want) give a one-line script to create the entire repo from the code above on your machine.
