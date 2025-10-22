# Use a more recent Debian base image
FROM python:3.11-bullseye

# Set the working directory in the container
WORKDIR /app

# Clean the apt cache
# Note: Cleaning cache before running update is non-standard but fine
RUN apt-get clean

# Update package lists and install core system dependencies for WeasyPrint
# Combined into one RUN instruction for faster building and smaller layers
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libglib2.0-0 && \
    # Remove unused packages and clean up the apt cache for a smaller final image
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . .

# Cloud Run defines the PORT environment variable.
# We expose 8080 for documentation, but Gunicorn must listen on $PORT.
EXPOSE 8080

# The critical change: Use the shell form (without []) to allow environment
# variable expansion and bind Gunicorn to the port specified by Cloud Run's $PORT.
CMD gunicorn --bind 0.0.0.0:$PORT main:app