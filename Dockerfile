FROM python:3.12-slim
WORKDIR /app
RUN mkdir -p /data
COPY packages/roomy /app/packages/roomy
RUN pip install --no-cache-dir "/app/packages/roomy[api]"
ENV ROOMY_DB_PATH=/data/traces.db
EXPOSE 8765
CMD ["roomy", "serve", "--db", "/data/traces.db", "--host", "0.0.0.0", "--port", "8765"]
