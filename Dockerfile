# Start from an official Python 3.12 image
# This is the base layer — a minimal Linux OS with Python already installed
FROM python:3.12-slim

# Set the working directory inside the container
# All subsequent commands run from here
WORKDIR /app

# Copy requirements first (before copying code)
# Why? Docker caches layers. If requirements haven't changed,
# Docker skips reinstalling them — makes builds much faster
COPY requirements.txt .

# Install Python dependencies inside the container
RUN pip install --no-cache-dir -r requirements.txt

# Now copy your actual app code
COPY app/ ./app/

# Tell Docker this container listens on port 8000
EXPOSE 8000

# The command that runs when the container starts
# uvicorn is the server, app.main:app points to the FastAPI instance
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]