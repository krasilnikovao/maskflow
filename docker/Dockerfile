# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS deps

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

ARG MASKFLOW_EXTRAS=""

COPY pyproject.toml README.md uv.lock ./

RUN python -m venv /opt/venv \
    && mkdir -p maskflow \
    && touch maskflow/__init__.py \
    && if [ -n "$MASKFLOW_EXTRAS" ]; then \
        /opt/venv/bin/pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu ".[${MASKFLOW_EXTRAS}]"; \
    else \
        /opt/venv/bin/pip install --no-cache-dir .; \
    fi


FROM deps AS builder

COPY maskflow ./maskflow

RUN /opt/venv/bin/pip install --no-cache-dir --force-reinstall --no-deps .


FROM python:3.12-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN groupadd --system maskflow \
    && useradd --system --gid maskflow --create-home --home /home/maskflow maskflow

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY configs ./configs
COPY docker/entrypoint.sh /entrypoint.sh

RUN mkdir -p /data \
    && chown -R maskflow:maskflow /data \
    && chmod +x /entrypoint.sh

USER maskflow

ENV MASKFLOW_DATA_DIR=/data

EXPOSE 3100

ENTRYPOINT ["/entrypoint.sh"]
CMD ["web", "--host", "0.0.0.0", "--port", "3100"]
