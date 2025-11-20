# Dockerfile for Test Execution Sandbox
# Provides isolated environment for running generated code and tests

FROM python:3.11-slim

# Set working directory
WORKDIR /sandbox

# Install pytest and common testing libraries
RUN pip install --no-cache-dir \
    pytest>=8.0.0 \
    pytest-asyncio>=0.24.0 \
    pytest-mock>=3.12.0 \
    pytest-cov>=4.1.0

# Create non-root user for security
RUN useradd -m -u 1000 sandbox && \
    chown -R sandbox:sandbox /sandbox

USER sandbox

# Default command: run pytest
CMD ["pytest", "-v"]