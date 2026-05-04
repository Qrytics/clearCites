FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY services/graph_api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY services/ /app/services/
COPY data_pipeline/ /app/data_pipeline/

# Allow `scholargraph.data_pipeline.*` imports (used by OpenAlex routes) in this image.
RUN mkdir -p /app/scholargraph && touch /app/scholargraph/__init__.py && \
    ln -sfn /app/data_pipeline /app/scholargraph/data_pipeline

ENV PYTHONPATH=/app

CMD ["uvicorn", "services.graph_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
