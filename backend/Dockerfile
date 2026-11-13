# FairLens v2 - local compose image only; the host never builds it.
# Build context is the repository root, so `samples/` is available.
FROM python:3.12-slim

WORKDIR /app

COPY backend/ ./
RUN pip install --no-cache-dir .

COPY samples ./samples

RUN useradd -r fairlens && chown -R fairlens /app
USER fairlens

EXPOSE 7860

ENTRYPOINT ["sh", "entrypoint.sh"]
