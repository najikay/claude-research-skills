# The reference checker as a small web service (see hosting/README.md). Standard library only: no pip step.
FROM python:3.12-slim
WORKDIR /app
COPY servers/reference_lookup/server.py servers/reference_lookup/remote.py /app/
ENV PORT=8080 PYTHONUNBUFFERED=1
EXPOSE 8080
USER nobody
CMD ["python3", "/app/remote.py"]
