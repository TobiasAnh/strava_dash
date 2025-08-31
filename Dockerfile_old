# Use an official Python base image
FROM python:3.10.12-slim

# Install system dependencies and Poetry
RUN apt-get update && \
    apt-get install -y curl build-essential libpq-dev git && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# enable Poetry virtual environments
ENV POETRY_VIRTUALENVS_CREATE=false
ENV PYTHONPATH=/app
# Copy only pyproject.toml and poetry.lock to leverage Docker caching
COPY pyproject.toml poetry.lock ./

# Install dependencies (including pandas)
RUN poetry install --no-root

# Copy the application code
COPY . .

# Set environment variables (optional)
ENV PYTHONUNBUFFERED=1


# Set the default command to run the application
# CMD ["python", "strava_dash/main.py"]

# Command to run the WSGI server (-w defines number of workers)
CMD ["poetry", "run", "gunicorn", "-w", "9", "-b", "0.0.0.0:8050", "app.main:server"]

# sudo docker run -it --rm --network="host" strava_dash


