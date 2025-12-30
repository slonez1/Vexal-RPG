import json
import os
import time
from google.cloud import storage
from backend.cache_index import purge_older_than, add_entry, load_index

GCS_BUCKET = os.getenv("GCS_BUCKET", "")
USE_GCS = bool(GCS_BUCKET and os.getenv("USE_GCS_CACHE", "false").lower() in ("1","true","yes"))

if USE_GCS:
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET)
else:
    storage_client = None
    bucket = None

INDEX_BLOB = "audio_cache/index.json"

def load_index() -> dict:
    if not bucket:
        # local fallback: store index file in AUDIO_CACHE_DIR/index.json
        path = os.path.join(os.getenv("AUDIO_CACHE_DIR", "./audio_cache"), "index.json")
        if os.path.exists(path):
            return json.load(open(path, "r", encoding="utf-8"))
        return {}
    blob = bucket.blob(INDEX_BLOB)
    if blob.exists():
        return json.loads(blob.download_as_text())
    return {}

def save_index(index: dict):
    index_json = json.dumps(index)
    if not bucket:
        path = os.path.join(os.getenv("AUDIO_CACHE_DIR", "./audio_cache"), "index.json")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(index_json)
    else:
        blob = bucket.blob(INDEX_BLOB)
        blob.upload_from_string(index_json)

def add_entry(key: str, size: int):
    idx = load_index()
    idx[key] = {"ts": int(time.time()), "size": size}
    save_index(idx)

def purge_older_than(ttl_seconds: int = 60*60*24*7):
    idx = load_index()
    cutoff = int(time.time()) - ttl_seconds
    removed = []
    for key, meta in list(idx.items()):
        if meta.get("ts", 0) < cutoff:
            # delete blob if GCS
            if bucket:
                blob = bucket.blob(f"audio_cache/{key}")
                if blob.exists():
                    blob.delete()
            else:
                local_path = os.path.join(os.getenv("AUDIO_CACHE_DIR", "./audio_cache"), key)
                if os.path.exists(local_path):
                    os.remove(local_path)
            del idx[key]
            removed.append(key)
    save_index(idx)
    return removed
