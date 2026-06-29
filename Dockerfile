FROM ghcr.io/lagrangedev/lagrange.onebot:edge

WORKDIR /app/qq-group-bot

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ADMIN_HOST=0.0.0.0 \
    LAGRANGE_BIN=/app/bin/Lagrange.OneBot \
    LAGRANGE_DATA_DIR=/app/data \
    BOT_SPAWN_ENABLED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python3 -m venv /app/venv \
    && /app/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /app/venv/bin/pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PATH=/app/venv/bin:$PATH

EXPOSE 8090 18080

ENTRYPOINT []
CMD ["python", "admin.py"]
