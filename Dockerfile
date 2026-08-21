FROM python:3.13-slim-trixie AS build

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Match the interpreter path used by the distroless runtime so venv symlinks
# remain valid after the multi-stage copy.
RUN ln -s /usr/local/bin/python /usr/bin/python \
    && /usr/bin/python -m venv /venv

COPY requirements.txt ./
RUN /venv/bin/pip install -r requirements.txt

FROM gcr.io/distroless/python3-debian13:nonroot

ARG APP_VERSION=local

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=${APP_VERSION} \
    PORT=8000

WORKDIR /app

COPY --from=build --chown=nonroot:nonroot /venv /venv
COPY --chown=nonroot:nonroot app/ ./app/
COPY --chown=nonroot:nonroot model.joblib ./

USER nonroot

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD ["/venv/bin/python3", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=2)"]

ENTRYPOINT ["/venv/bin/python3", "-m", "uvicorn"]
CMD ["app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
