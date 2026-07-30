FROM python:3.10-slim

WORKDIR /app

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1

# Install system dependencies needed for matplotlib/scipy
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpng-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install CPU PyTorch & packages without caching to keep image small
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code and models
COPY . /app/
COPY ./models /models

# Expose port
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
