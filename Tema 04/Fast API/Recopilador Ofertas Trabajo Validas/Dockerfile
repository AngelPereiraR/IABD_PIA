# ============================================================================
# Stage 1: Builder - Compile Python wheels and dependencies
# ============================================================================
FROM python:3.12-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies only needed for compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and create wheels (faster for final stage)
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ============================================================================
# Stage 2: Runtime - Minimal production image
# ============================================================================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

WORKDIR /app

# Install only runtime dependencies
# texlive-latex-base: Minimal LaTeX for PDF generation (much smaller than texlive-full)
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install them
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application code
COPY src/ src/
COPY data/ data/
COPY main.py .

# Copy and make entrypoint executable
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Health check for orchestration (every 30s, timeout 5s, fails after 3 retries)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run the application
ENTRYPOINT ["./entrypoint.sh"]