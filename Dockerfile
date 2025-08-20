# Use Python base image
FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy uv lock and config files
COPY uv.lock pyproject.toml ./

# Copy source code
COPY . .

# Install dependencies
RUN uv sync --frozen --no-cache

# Expose port
EXPOSE 8000

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8000

# Run the application
CMD ["uv", "run", "python", "webapp.py", "--host", "0.0.0.0", "--port", "8000"]