FROM python:3.12-slim

WORKDIR /app

# Copy application files
COPY server.py .
COPY index.html .

# Expose the default port
EXPOSE 8040

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8040/')" || exit 1

# Start the server
CMD ["python3", "server.py"]
