import sys
import uvicorn

# Ensure utf-8 encoding on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if __name__ == "__main__":
    print("=" * 60)
    print("  [*] INVENTORY TURNOVER & VELOCITY ENGINE (OBJECTIVE A)")
    print("  Server running at: http://127.0.0.1:8000")
    print("  API Docs available at: http://127.0.0.1:8000/docs")
    print("=" * 60)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
