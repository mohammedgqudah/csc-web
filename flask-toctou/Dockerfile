FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

EXPOSE 8000

WORKDIR /app

ADD . /app
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []
CMD ["sh", "-c", "gunicorn -w 10 -b 0.0.0.0:8000 main:app"]

