# Stage 1: Build stage
FROM python:3.12-slim as build

# Set the working directory in the container
WORKDIR /app

# Copy the entire context to the container
COPY . .

# Get the current Git branch and build time
RUN DATE=$(date +'%Y%m%d-%H%M%S') && \
    echo "${DATE}" > /app/BUILT_AT

# Stage 2: Production stage
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /opt/stage0_mongodb_api

# Copy the entire source code and the BUILT_AT file from the build stage
COPY --from=build /app/ /opt/stage0_mongodb_api/

# Install pipenv and dependencies
COPY Pipfile Pipfile.lock /opt/stage0_mongodb_api/
RUN pip install pipenv && pipenv install --deploy --system

# Install the package in development mode
RUN pip install -e .

# Install Gunicorn for running the Flask app in production
RUN pip install gunicorn

# Expose the port the app will run on
EXPOSE 8081

# Set Environment Variables
ENV PYTHONPATH=/opt/stage0_mongodb_api/stage0_mongodb_api

# Command to run the application using Gunicorn 
CMD exec gunicorn --bind 0.0.0.0:8081 --timeout 120 --preload stage0_mongodb_api.server:app
