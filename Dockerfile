# Use the official Python runtime image as the baseline
FROM python:3.11-slim

# Establish an active working directory inside the container
WORKDIR /app

# Install the Gemini SDK used by ai_manager.py
RUN pip install --no-cache-dir google-genai

# Copy the program files into the container workspace
# (secrets_local.py is deliberately NOT copied: the API key is passed in at run time)
COPY main.py .
COPY io_manager.py .
COPY ai_manager.py .
COPY logic_manager.py .
COPY data_manager.py .
COPY test_logic_manager.py .

# Define the execution command to run when the container starts
CMD ["python", "main.py"]
