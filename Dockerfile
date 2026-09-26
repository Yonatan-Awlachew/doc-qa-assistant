# A Docker image = your app + Python + all libraries, packed together,
# so it runs the same way on any computer.

# 1. Start from a small official Python image
FROM python:3.11-slim

# 2. Work inside the /app folder of the container
WORKDIR /app

# 3. Install the libraries first (Docker caches this step, so rebuilds are fast)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the code and the web page (v2: no prebuilt index, users upload their files)
COPY app ./app
COPY frontend ./frontend
COPY samples ./samples
RUN mkdir -p storage

# 5. The API listens on port 8000 (or on $PORT if the hosting service sets one, like Render)
EXPOSE 8000

# 6. Start the server (0.0.0.0 = reachable from outside the container)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]