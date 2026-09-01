import uvicorn
import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    uvicorn.run("api.app:app", host="127.0.0.1", port=8000, log_level="info")
