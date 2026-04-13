FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd -m appuser

WORKDIR /app

COPY ui/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ui/ .

USER appuser

CMD ["sh", "-c", "streamlit run app.py --server.port=${UI_PORT:-3000} --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false"]
