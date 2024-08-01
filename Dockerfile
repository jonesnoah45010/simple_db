FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY . .

# Expose the port
EXPOSE 8080

# Set the entry point and command to run your application
ENTRYPOINT ["uvicorn"]
CMD ["app:app", "--host", "0.0.0.0", "--port", "8080"]