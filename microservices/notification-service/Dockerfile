# Use Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the app code
COPY app/ ./

# Expose the service port
EXPOSE 5000

# Start the app
CMD ["python", "app.py"]