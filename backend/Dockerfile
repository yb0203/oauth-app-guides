# Playwright's official Python image ships Chromium and its system libraries, so the browser fallback works.
# Keep the tag in step with the playwright version in requirements.txt (1.64.x).
FROM mcr.microsoft.com/playwright/python:v1.64.0-noble

WORKDIR /srv
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Build context is the repository root: the API reads data/guides and research/composio at runtime.
COPY backend backend
COPY data data
COPY research/composio research/composio

WORKDIR /srv/backend
ENV PORT=8000 LLM_MODE=live
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.api:app --host 0.0.0.0 --port ${PORT}"]
