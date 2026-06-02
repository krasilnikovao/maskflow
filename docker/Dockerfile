# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS deps

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_NO_CACHE=1 \
    # Corporate SSL-inspection proxies (Zscaler, Cisco Umbrella, etc.) perform
    # HTTPS MITM and present their own CA, which is not trusted inside the
    # container. UV_INSECURE_HOST disables certificate verification for these
    # hosts — equivalent to pip's --trusted-host. TLS is still used, only the
    # certificate chain is not verified. Remove this line if not behind a proxy.
    UV_INSECURE_HOST="pypi.org files.pythonhosted.org download.pytorch.org"

WORKDIR /build

ARG MASKFLOW_EXTRAS=""

# Corporate proxy support: pass HTTP_PROXY/HTTPS_PROXY as build args.
# Set them in .env or via Docker Desktop → Settings → Resources → Proxies.
# Leave empty if not behind a proxy.
ARG HTTP_PROXY=""
ARG HTTPS_PROXY=""
ARG NO_PROXY="localhost,127.0.0.1"
ENV http_proxy=${HTTP_PROXY} \
    https_proxy=${HTTPS_PROXY} \
    no_proxy=${NO_PROXY} \
    HTTP_PROXY=${HTTP_PROXY} \
    HTTPS_PROXY=${HTTPS_PROXY} \
    NO_PROXY=${NO_PROXY}

COPY pyproject.toml README.md uv.lock ./

# Bootstrap uv from the official Docker image — completely bypasses pypi.org.
# uv handles build dependencies natively in Rust without spawning a pip
# subprocess, so the build does not fail when pypi.org SSL is intercepted.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN uv venv /opt/venv \
    && mkdir -p maskflow \
    && touch maskflow/__init__.py \
    && if [ -n "$MASKFLOW_EXTRAS" ]; then \
        uv pip install \
            --python /opt/venv/bin/python \
            --extra-index-url https://download.pytorch.org/whl/cpu \
            ".[${MASKFLOW_EXTRAS}]"; \
    else \
        uv pip install --python /opt/venv/bin/python .; \
    fi


FROM deps AS builder

COPY maskflow ./maskflow

# --no-build-isolation: reuse setuptools/wheel already present in /opt/venv
# instead of fetching build tools from pypi.org again.
# --no-deps: all runtime dependencies were already resolved in the deps stage.
RUN uv pip install \
    --python /opt/venv/bin/python \
    --no-deps \
    --no-build-isolation \
    .


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
