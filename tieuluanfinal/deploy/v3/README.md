# Backend V3 — compact Render project

This directory's Blueprint is for the project exported by `scripts.package_phase32`,
not the historical V2 backend. No cloud service is created automatically.

1. Extract the active `api-bundle-*.zip` into a new folder. Its root contains apps/,
   src/, artifacts/, deploy/ and bundle_manifest.json. Keep those relative paths.
2. Upload/commit this compact project to a repository you control. It includes the
   allowlisted runtime artifacts; a normal commit of the large development repo may
   omit ignored model/data files. Do not commit local .env or job databases.
3. In Render, choose the repository and Blueprint path `deploy/v3/render.yaml`.
   Review free plan/region; set AI_CORS_ORIGINS to the exact frontend origin, without
   trailing slash. No wildcard. This step requires your account and approval.
4. Test `/health`, `/ready`, `/api/v3/openapi.json`. Readiness is diagnostic;
   artifact failures become unavailable slots rather than a startup crash loop.

Manual Web Service: Python3.11.17, repository root unchanged, build:

```sh
pip install --require-hashes -r deploy/v3/requirements-cpu.lock
python -m apps.api.v3.check_bundle
```

Start:

```sh
gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 'apps.api.v3.server:create_app()'
```

AI_SERVING_MODE=cpu. This runs the three independently trained neural weights with
NumPy portable inference; it is not native TensorFlow/PyTorch timing. Do not install
GPU frameworks on Render. Local native GPU mode uses the separate locked WSL envs.

Jobs are asynchronous, capability-owned, sequential, ephemeral, TTL30min, queue32.
Use a client-generated random token of at least128bits (e.g.24random bytes,hex48)
in X-Client-Token and a distinct Idempotency-Key. Poll accepted.poll_url with the same
token; expose neither token nor request input in URLs/logs. No train/TEST/admin API.

Local memory proxy is not a cloud SLA or guarantee that all requests fit free-tier
under every cold start/load. A memory/time budget failure returns explicit slots.
Do not upgrade to a paid plan without the project owner's agreement. React UI is
Phase33; the old UI does not automatically use the V3 contract/headers.

Sources: https://render.com/docs/deploy-flask and https://render.com/docs/blueprint-spec.
