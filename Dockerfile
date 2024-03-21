# Use an official Python runtime as a parent image
FROM mcr.microsoft.com/devcontainers/python:1-3.8-bookworm

# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into the container at /app
ADD backend /app

# Install any needed packages specified in requirements.txt
RUN apt-get update && apt-get install -y ffmpeg
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Run gunicorn server when the container launches
CMD ["gunicorn", "--chdir", "app", "app:app"]