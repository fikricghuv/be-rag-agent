pip install -r requirements.txt

source .venv/bin/activate

uvicorn app:app --host 0.0.0.0 --port 8001 --reload


docker
docker build -t talkvera-app-be .
docker compose up -d