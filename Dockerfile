# Use Python 3.12 slim image
FROM python:3.12-slim

# Set the working directory
WORKDIR /opt/mongo_configurator

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better caching
COPY Pipfile Pipfile.lock ./

# Install pipenv
RUN pip install pipenv

# Copy application code 
COPY . .

# Install dependencies
RUN pipenv install --deploy --system

# Create build timestamp
RUN echo $(date +'%Y%m%d-%H%M%S') > /opt/mongo_configurator/BUILT_AT

# Install Gunicorn for production
RUN pip install gunicorn

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /opt/mongo_configurator

# Switch to non-root user
USER app

# Expose the port
EXPOSE 8081

# Set environment variables
ENV PYTHONPATH=/opt/mongo_configurator/configurator
ENV API_PORT=8081

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8081", "--timeout", "10", "--preload", "configurator.server:app"]
