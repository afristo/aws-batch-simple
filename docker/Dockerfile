# Use the latest slim version of Python
FROM python:slim

# Set the working directory
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt /app/

# Upgrade pip and install dependencies from the requirements.txt file
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the rest of the application code
COPY hello_world.py /app/

# Run app.py when the container launches
CMD ["python", "hello_world.py"]
