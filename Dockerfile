# Review Issue Classifier — Streamlit app
FROM python:3.13-slim

# Avoid .pyc files and buffer-delayed logs in the container.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first so the layer is cached unless requirements change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only what the app needs at runtime.
COPY review_classifier_python.py review_classifier_core.py ./

# Run logs are written here; keep the directory writable.
RUN mkdir -p /app/logs

EXPOSE 8501

# OPENAI_API_KEY must be supplied at runtime (do NOT bake it into the image):
#   docker run -p 8501:8501 -e OPENAI_API_KEY=sk-... review-classifier
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

CMD ["streamlit", "run", "review_classifier_python.py", \
     "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
