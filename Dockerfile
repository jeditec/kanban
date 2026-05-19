FROM python:3.12-slim

WORKDIR /app

# Copy application files
COPY server.py .
COPY index.html .

# Install dependencies
RUN pip install --no-cache-dir pyminizip

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
