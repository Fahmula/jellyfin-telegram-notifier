# Use the official Python image based on Alpine Linux
FROM python:3.8-alpine

# Set the working directory in the container
WORKDIR /app

# Install curl and ping
RUN apk update && \
    apk add --no-cache curl iputils

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

ENV PYTHONUNBUFFERED=1

# Define the command to run your Python script
CMD ["python", "main.py"]
