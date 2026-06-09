# Container image for the pDST-calc Shiny (Python) web app.
# Build:  docker build -t pdst-calc:poc .
# Run:    docker run -p 3838:3838 pdst-calc:poc   ->  http://localhost:3838
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim
WORKDIR /app
COPY . /app

# Install runtime deps from the committed lockfile (no dev/lint/test groups).
RUN uv sync --frozen --no-dev

# Run the pre-built venv directly (no `uv run` re-sync at container start).
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 3838
CMD ["shiny", "run", "app/shiny/app.py", "--host", "0.0.0.0", "--port", "3838"]
