# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster as base

# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into the container at /app
ADD . /app

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Prevents Python from writing pyc files to disk and keeps Python from buffering stdout and stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-privileged user and switch to it
RUN adduser --disabled-password --gecos "" --home "/nonexistent" --shell "/sbin/nologin" --no-create-home --uid "10001" appuser

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

USER appuser

# Make port 80 available to the world outside this container
EXPOSE 80

# Run gunicorn server when the container launches
CMD ["gunicorn", "--chdir", "backend", "app:app"]

# Create a new image for setting permissions
FROM base AS permissions

USER root

# Set permissions for the /app/public/uploads directory
RUN mkdir -p /app/public/uploads && chmod 777 /app/public/uploads
