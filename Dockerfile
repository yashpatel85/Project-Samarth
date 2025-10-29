# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed system dependencies (if any, unlikely for this app)
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from requirements.txt
# Using --no-cache-dir reduces image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend directory into the container's /app/backend directory
COPY ./backend /app/backend
# Copy the .env file (we'll override with Render's env vars, but good practice)
COPY .env .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable (can be overridden by Render)
ENV MODULE_NAME="backend.app.main"
ENV VARIABLE_NAME="app"

# When the container launches, run uvicorn
# Use 0.0.0.0 to listen on all interfaces within the container
# Use the port Render expects (usually provided via $PORT, defaults here to 8000)
# Add --factory for better app loading in some environments
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8000", "--factory", "backend.app.main:app"]