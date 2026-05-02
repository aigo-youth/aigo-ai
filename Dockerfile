FROM python:3.12-slim-bookworm AS python312

FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON=python3.12 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:/root/.local/bin:$PATH \
    HF_HOME=/models/huggingface \
    TRANSFORMERS_CACHE=/models/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/models/sentence-transformers \
    PADDLEX_HOME=/models/paddle \
    TZ=Asia/Seoul

COPY --from=python312 /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=python312 /usr/local/lib/libpython3.12.so.1.0 /usr/local/lib/libpython3.12.so.1.0
COPY --from=python312 /usr/local/bin/python3.12 /usr/local/bin/python3.12
COPY --from=python312 /usr/local/include/python3.12 /usr/local/include/python3.12
RUN ldconfig \
    && ln -sf /usr/local/bin/python3.12 /usr/local/bin/python3 \
    && ln -sf /usr/local/bin/python3.12 /usr/local/bin/python \
    && python3.12 -m ensurepip --upgrade

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    tzdata \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-kor \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && ln -sf /root/.local/bin/uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY scripts ./scripts

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# PaddleOCR 백엔드 (paddlepaddle) 는 PaddleOCR 패키지가 자동 설치하지 않으므로 별도 설치.
# - cu123 인덱스에는 3.0.0 stable cp312 Linux wheel 이 없어 cu126 BOS 직접 URL 사용.
# - cu126 wheel 은 CUDA 12.4 base (12.x 계열 forward 호환) 에서 동작.
# - uv 가 ARM 빌드 호스트에서 플랫폼 태그를 aarch64 로 감지해 x86_64 wheel 을 거부하므로
#   --python-platform 으로 타겟 플랫폼을 명시해 태그 검사를 올바르게 수행.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --python /opt/venv/bin/python \
    --python-platform x86_64-unknown-linux-gnu \
    --index-url https://www.paddlepaddle.org.cn/packages/stable/cu126/ \
    --extra-index-url https://pypi.org/simple \
    --index-strategy unsafe-best-match \
    "paddlepaddle-gpu==3.0.0"

RUN mkdir -p /models/huggingface /models/sentence-transformers /models/paddle

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1

CMD ["uvicorn", "app.main:app", \
    "--host", "0.0.0.0", \
    "--port", "8000", \
    "--workers", "1", \
    "--proxy-headers", \
    "--forwarded-allow-ips", "*", \
    "--timeout-keep-alive", "75", \
    "--log-level", "info"]
