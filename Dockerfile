# Use a more recent Debian base image
FROM python:3.11-bullseye

# Set the working directory in the container
WORKDIR /app

# Clean the apt cache
RUN apt-get clean

# Update package lists
RUN apt-get update

# Install core system dependencies for WeasyPrint
RUN apt-get install -y --no-install-recommends \
    libcairo2 \
    libcairo2-dev \
    libpango-1.0-0 \
    libpango1.0-dev \
    libgdk-pixbuf2.0-0 \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    libglib2.0-0 \
    libglib2.0-dev

# Copy the requirements file into the container
COPY requirements.txt .

# Install any Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . .

# Expose the port the application runs on
ENV PORT=8080

# Set environment variables (optional but recommended)
#ENV FLASK_APP=app.py
#ENV FLASK_ENV=production

# Define the command to run the application
CMD ["python", "main.py"]