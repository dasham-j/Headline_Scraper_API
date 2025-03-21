# Use official Python 3.11 image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy project files into the container
COPY . /app/

# Install dependencies
RUN pip install -r requirements.txt

# Expose port 5000 for Flask
EXPOSE 5000

# Run Flask app
CMD ["python", "main.py"]
