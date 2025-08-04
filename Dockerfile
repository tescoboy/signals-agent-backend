FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY pyproject.toml ./
RUN pip install uv
RUN uv pip install --system fastmcp pydantic rich google-generativeai requests

# Copy application code
COPY . .

# Create config from sample (users will need to set their API key)
RUN cp config.json.sample config.json

# Initialize database
RUN python database.py

# Expose port for web demo
EXPOSE 8000

# Default command - run FastMCP with streamable HTTP transport for web access
CMD ["fastmcp", "run", "--transport", "http", "--host", "0.0.0.0", "--port", "8000", "main.py"]