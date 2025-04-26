pip install -r requirements.txt

source /Users/cghuv/Documents/Project/AGENT-PROD/app/venv/bin/activate

uvicorn app:app --host 0.0.0.0 --port 8001 --reload