# Use an official Python base image
FROM python:3.10.12-slim

# Install system dependencies and Poetry
RUN apt-get update && \
    apt-get install -y curl build-essential libpq-dev git && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory to the project root inside the container
# This is where pyproject.toml and src/ will live
WORKDIR /app

    # Tell poetry not to create a virtual environment in a separate location
ENV POETRY_VIRTUALENVS_CREATE=false

# Copy only pyproject.toml and poetry.lock to leverage Docker caching
# We will copy them to the WORKDIR, which is /app
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root

# Copy the source code. This copies the src/ folder and its contents
# from your local machine into the /app directory in the container.
COPY . /app

# Set the PATH to include Poetry's executables and the source code
# This is a critical step for a containerized environment
ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONPATH=/app/src

# Set the default command to run the application
# CMD ["poetry", "run", "gunicorn", "-w", "9", "-b", "0.0.0.0:8050", "app.main:server"]
# Assuming your main application is in src/app/main.py, the above command is correct.
# gunicorn will look for the 'app' package, which is inside the 'src' directory.
# Since we set PYTHONPATH=/app/src, it will find it.
CMD ["poetry", "run", "gunicorn", "-w", "9", "-b", "0.0.0.0:8050", "strava_dash.main:server"]