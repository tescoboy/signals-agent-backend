FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY pyproject.toml uv.lock ./
RUN pip install uv
RUN uv sync --frozen

# Copy application code
COPY . .

# Create config from sample (users will need to set their API key)
RUN cp config.json.sample config.json

# Initialize database
RUN uv run python database.py

# Expose port for web demo
EXPOSE 8000

# Default command (can be overridden)
CMD ["uv", "run", "python", "main.py"]