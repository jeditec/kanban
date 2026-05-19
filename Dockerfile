FROM python:3.12-slim

WORKDIR /app

# Install build dependencies for pyminizip, then the package, then clean up
RUN apt-get update && apt-get install -y --no-install-recommends gcc libzip-dev && \
    pip install --no-cache-dir pyminizip && \
    apt-get purge -y gcc libzip-dev && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Environment variables
ENV KANBAN_HTTP_PORT=8060
ENV KANBAN_PASSWORD=changeme

# Expose the configured port
EXPOSE ${KANBAN_HTTP_PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:${KANBAN_HTTP_PORT}/')" || exit 1

# Start the server
CMD ["python3", "server.py"]
