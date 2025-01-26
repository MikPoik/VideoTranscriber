FROM python:3.11 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/usr/local/bin:/usr/bin:/bin:${PATH}"
WORKDIR /app

RUN apt-get update && \
    apt-get install -y imagemagick ffmpeg && \
    rm -rf /var/lib/apt/lists/*

RUN python -m venv .venv
COPY pyproject.toml ./
RUN .venv/bin/pip install .

FROM python:3.11-slim
WORKDIR /app

# Copy ffmpeg and imagemagick installation from builder stage. More efficient
#COPY --from=builder /usr/bin/ffmpeg /usr/bin/
#COPY --from=builder /usr/bin/convert /usr/bin/
#COPY --from=builder /usr/lib/x86_64-linux-gnu/libMagick*.so* /usr/lib/x86_64-linux-gnu/

ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
# Or reinstall them (less efficient, but simpler to understand initially):
 RUN apt-get update && \
     apt-get install -y imagemagick ffmpeg && \
     rm -rf /var/lib/apt/lists/*


COPY --from=builder /app/.venv .venv/
COPY . .
CMD ["/app/.venv/bin/streamlit", "run", "main.py"]

