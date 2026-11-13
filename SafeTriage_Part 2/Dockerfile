# Official Python runtime as the baseline
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install the Gemini SDK used by ai_manager.gemini_provider.GeminiProvider (cached layer: only reruns if requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code and tests.
# secrets_local.py and .env are deliberately NOT copied: the API key is passed in at run time.
COPY main.py application.py constants.py ./
COPY io_manager ./io_manager
COPY ai_manager ./ai_manager
COPY logic_manager ./logic_manager
COPY data_manager ./data_manager
COPY domain ./domain
COPY sessions ./sessions
COPY errors ./errors
COPY tests ./tests

# If any test fails, the image is not built (tests need no API key)
RUN python -m unittest discover -s tests -p "test_safetriage.py"

# Incident data lives here; mount a host folder over it to keep data between runs
RUN mkdir -p /app/data
VOLUME ["/app/data"]

# Default command: ask which terminal to start (user / admin)
CMD ["python", "main.py"]
