# ---- Stage 1: build dependencies into a virtualenv ----
FROM python:3.12-slim AS builder
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Stage 2: minimal runtime image ----
FROM python:3.12-slim
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1
COPY --from=builder /opt/venv /opt/venv

# Run as an unprivileged user
RUN useradd --create-home --uid 1000 appuser
WORKDIR /app
COPY --chown=appuser app/ .
USER appuser

EXPOSE 5000
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request as u; u.urlopen('http://localhost:5000/health', timeout=2)"

# One worker: prometheus_client keeps metrics in process memory (and so does the task store).
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "app:app"]
