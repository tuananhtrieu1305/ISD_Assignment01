FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN groupadd --system modelapp && useradd --system --gid modelapp --home /app modelapp

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --requirement /tmp/requirements.txt

COPY --chown=modelapp:modelapp __init__.py model_registry.json /app/term_paper/deployment/
COPY --chown=modelapp:modelapp app /app/term_paper/deployment/app
COPY --from=source --chown=modelapp:modelapp . /app/term_paper/src
COPY --from=models --chown=modelapp:modelapp . /app/term_paper/artifacts/models
COPY --from=ch3_manifest --chown=modelapp:modelapp ch3_eurosat_subset_keys.csv /app/term_paper/artifacts/manifests/ch3/ch3_eurosat_subset_keys.csv
COPY --from=ch4_manifest --chown=modelapp:modelapp ch4_online_retail_customer_week_processed.npz /app/term_paper/artifacts/manifests/ch4/ch4_online_retail_customer_week_processed.npz
COPY --from=ch4_manifest --chown=modelapp:modelapp ch4_aapl_next_close_processed.npz /app/term_paper/artifacts/manifests/ch4/ch4_aapl_next_close_processed.npz
COPY --from=a06_preprocessing --chown=modelapp:modelapp . /app/A06/models/preprocessing
COPY --from=eurosat_demo --chown=modelapp:modelapp AnnualCrop_1321.jpg /app/A05/datasets/eurosat/EuroSAT_RGB/AnnualCrop/AnnualCrop_1321.jpg

USER modelapp
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
CMD ["python", "-m", "term_paper.deployment.app.server", "--host", "0.0.0.0", "--port", "8000", "--workspace", "/app"]
