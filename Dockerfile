FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install the required Python packages
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy the app to the container
COPY app.py .
# Copy the .env file into the container at /app
COPY .env /app/
COPY . /app


# Set the command to run your application
ENTRYPOINT ["uvicorn"]
CMD ["app:app", "--host=0.0.0.0"]