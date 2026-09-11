.\.venv\Scripts\python.exe src\pipeline.py --fetch
.\.venv\Scripts\python.exe -m uvicorn src.api:app --host 127.0.0.1 --port 4174
