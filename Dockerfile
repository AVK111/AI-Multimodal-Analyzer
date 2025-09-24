# Use a full Python image
FROM python:3.12-slim

# Install system dependencies needed for some Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose port for Streamlit or your app
EXPOSE 5000

# Start your app (change app.py to your main file)
CMD ["streamlit", "run", "app.py", "--server.port=5000", "--server.address=0.0.0.0"]
