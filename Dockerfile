# FILE: Dockerfile
# A Docker image = your app + Python + all libraries, packed together,
# so it runs the same way on any computer.

# 1. Start from a small official Python image
FROM python:3.11-slim

# 2. Work inside the /app folder of the container
WORKDIR /app

# 3. Install the libraries first (Docker caches this step, so rebuilds are fast)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the code and the prebuilt index
COPY app ./app
COPY data/index ./data/index

# 5. The API listens on port 8000
EXPOSE 8000

# 6. Start the server (0.0.0.0 = reachable from outside the container)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]