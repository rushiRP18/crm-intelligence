"""
Email Stream Replay Script.

Simulates real-time email ingestion by replaying email-data-advanced.json
at a configurable speed.

Usage:
    python -m scripts.replay_emails                    # 1 email/sec
    python -m scripts.replay_emails --speed 0.5        # 1 email per 0.5s (fast)
    python -m scripts.replay_emails --batch            # Ingest all at once
    python -m scripts.replay_emails --file path/to/data.json  # custom file
"""
import sys
import os
import json
import time
import argparse
from pathlib import Path

try:
    import httpx
except ImportError:
    print("httpx not installed. Run: pip install httpx")
    sys.exit(1)

# Allow running from backend/ or project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try several common locations for the dataset
SCRIPT_DIR = Path(__file__).resolve().parent
SEARCH_PATHS = [
    SCRIPT_DIR.parent.parent.parent / "email-data-advanced.json",   # SenAI2/
    SCRIPT_DIR.parent.parent.parent.parent / "email-data-advanced.json",
    Path("C:/Users/Gayatri/Desktop/SenAI2/email-data-advanced.json"),
    Path("email-data-advanced.json"),
]
API_BASE = "http://localhost:8000/api"


def find_data_file(override=None):
    if override:
        p = Path(override)
        if p.exists():
            return p
        print(f"ERROR: File not found: {override}")
        sys.exit(1)
    for path in SEARCH_PATHS:
        if path.exists():
            return path
    print("ERROR: email-data-advanced.json not found.")
    print("Searched in:")
    for p in SEARCH_PATHS:
        print(f"  {p}")
    print("\nFix: use --file <path> to specify location")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Replay email dataset into CRM Intelligence Platform")
    parser.add_argument("--speed", type=float, default=1.0, help="Seconds between emails (default: 1.0)")
    parser.add_argument("--start", type=int, default=0, help="Start from email index (default: 0)")
    parser.add_argument("--batch", action="store_true", help="Ingest all at once via batch endpoint (fastest)")
    parser.add_argument("--api", default=API_BASE, help=f"API base URL (default: {API_BASE})")
    parser.add_argument("--file", default=None, help="Path to email JSON dataset")
    parser.add_argument("--limit", type=int, default=None, help="Only process first N emails")
    args = parser.parse_args()

    # Health check
    try:
        resp = httpx.get(f"{args.api}/health", timeout=5)
        if resp.status_code != 200:
            print(f"ERROR: Backend not responding at {args.api}")
            print("Start the backend first: uvicorn app.main:app --reload --port 8000")
            sys.exit(1)
        print(f"[OK] Backend healthy: {args.api}")
    except Exception as e:
        print(f"ERROR: Cannot connect to backend at {args.api}: {e}")
        print("Start the backend first: uvicorn app.main:app --reload --port 8000")
        sys.exit(1)

    # Load dataset
    data_file = find_data_file(args.file)
    emails = json.loads(data_file.read_text(encoding="utf-8"))

    # Apply slicing
    emails = emails[args.start:]
    if args.limit:
        emails = emails[:args.limit]

    print(f"[OK] Loaded {len(emails)} emails from {data_file.name}")
    print()

    # ── Batch mode ────────────────────────────────────────────────────────────
    if args.batch:
        print(f"Batch ingesting {len(emails)} emails...")
        try:
            resp = httpx.post(f"{args.api}/emails/ingest/batch", json=emails, timeout=120)
            result = resp.json()
            ingested  = sum(1 for r in result.get("results", []) if r.get("status") == "ingested")
            skipped   = sum(1 for r in result.get("results", []) if r.get("status") == "duplicate_skipped")
            errors    = sum(1 for r in result.get("results", []) if r.get("status") == "error")
            print(f"Done! Total: {result.get('total', 0)} | Ingested: {ingested} | Skipped: {skipped} | Errors: {errors}")
            print()
            print("AI agent is now processing emails in the background.")
            print("Open http://localhost:3000 to watch the inbox fill up!")
        except Exception as e:
            print(f"Batch request failed: {e}")
        return

    # ── Stream mode ───────────────────────────────────────────────────────────
    print(f"Streaming {len(emails)} emails at {args.speed}s per email...")
    print("-" * 70)

    success = failed = duplicate = 0

    for i, email in enumerate(emails, 1):
        try:
            resp = httpx.post(f"{args.api}/emails/ingest", json=email, timeout=15)
            if resp.status_code == 201:
                data = resp.json()
                flags = data.get("heuristic_flags", [])
                flag_str = f" [{', '.join(flags)}]" if flags else ""
                sender_short = (email.get("sender", ""))[:32]
                print(f"[{i:3}/{len(emails)}] OK  {email.get('message_id','?'):<15} {sender_short}{flag_str}")
                success += 1
            elif resp.status_code == 409:
                print(f"[{i:3}/{len(emails)}] DUP {email.get('message_id','?')}")
                duplicate += 1
            else:
                print(f"[{i:3}/{len(emails)}] ERR {email.get('message_id','?')} HTTP {resp.status_code}: {resp.text[:80]}")
                failed += 1
        except Exception as e:
            print(f"[{i:3}/{len(emails)}] ERR {email.get('message_id','?')} {e}")
            failed += 1

        if i < len(emails):
            time.sleep(args.speed)

    print("-" * 70)
    print(f"Complete! Ingested: {success} | Duplicates: {duplicate} | Errors: {failed}")
    print()
    print("AI agent is now processing emails in the background.")
    print("Open http://localhost:3000 to see the results!")


if __name__ == "__main__":
    main()
