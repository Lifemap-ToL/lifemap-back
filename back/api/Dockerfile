FROM ghcr.io/astral-sh/uv:alpine

# Copy the project into the image
COPY . /app

# Disable development dependencies
ENV UV_NO_DEV=1

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
RUN uv sync --locked

EXPOSE 80

CMD ["uv", "run", "fastapi", "run", "app.py", "--port", "80"]
