"""Additive Phase32 serving contract; frozen Phase22 specification is not edited."""

import copy

from src.common.contracts import ROOT, load_schemas, read_json


def _refs(value, context=None):
    if isinstance(value, list):
        return [_refs(v, context) for v in value]
    if not isinstance(value, dict):
        return value
    result = {}
    for key, child in value.items():
        if key in {"$id", "$schema"}:
            continue
        if key == "$ref":
            if child.startswith("urn:ai-paper:v3:"):
                name, _, fragment = child.removeprefix("urn:ai-paper:v3:").partition("#")
                child = f"#/components/schemas/{name}" + fragment
            elif ".schema.json" in child:
                file, _, fragment = child.partition("#")
                name = file.rsplit("/", 1)[-1].removesuffix(".schema.json")
                child = f"#/components/schemas/{name}" + fragment
            elif context and child.startswith("#"):
                child = f"#/components/schemas/{context}" + child[1:]
        result[key] = _refs(child, context)
    return result


def specification():
    document = _refs(read_json(ROOT / "docs/contracts/v3/openapi.json"))
    document["info"] = {
        "title": "AI term paper V3 serving API",
        "version": "3.1.0",
        "description": "Phase32 extension of frozen Phase22. Public catalog, capability-owned jobs; no train/TEST endpoints. Body schema_version remains3.0.0.",
    }
    schemas = document["components"]["schemas"] = {
        name: _refs(schema, name) for name, schema in load_schemas().items()
    }
    token = {
        "name": "X-Client-Token",
        "in": "header",
        "required": True,
        "description": "Client-generated random capability >=128bits. Store only locally; server stores SHA256. Needed for own jobs/traces.",
        "schema": {"type": "string", "pattern": "^[A-Za-z0-9_-]{32,128}$"},
    }
    for path, methods in document["paths"].items():
        for method, operation in methods.items():
            if method not in {"get", "post"}:
                continue
            if any(s in path for s in ("comparisons", "jobs/", "agent-tasks", "agent-traces")):
                operation.setdefault("parameters", []).append(copy.deepcopy(token))
            operation["responses"]["403"] = copy.deepcopy(document["components"]["responses"]["Error400"])
    envelope = {
        "type": "object",
        "additionalProperties": False,
        "required": ["schema_version", "request_id", "data"],
        "properties": {
            "schema_version": {"const": "3.0.0"},
            "request_id": {"type": "string"},
            "data": {"type": "object"},
        },
    }

    def response(schema):
        return {"description": "Success", "content": {"application/json": {"schema": schema}}}

    def enveloped(data):
        result = copy.deepcopy(envelope)
        result["properties"]["data"] = data
        return result

    # Non-neural function contracts and the preserved orphan metric have independent versions.
    schemas["function_contract"] = {
        "type": "object",
        "required": ["schema_version", "functions", "composition"],
        "properties": {
            "schema_version": {"enum": ["phase30.retrieval_pipeline.1", "phase31.agent_pipeline.1"]},
            "functions": {"type": "array"},
            "composition": {"type": "array"},
        },
    }
    document["paths"]["/api/v3/models/{model_id}/contract"]["get"]["responses"]["200"] = response(
        enveloped(
            {
                "oneOf": [
                    {"$ref": "#/components/schemas/model"},
                    {"$ref": "#/components/schemas/function_contract"},
                ]
            }
        )
    )
    artifact_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["artifact_id", "path", "sha256", "size_bytes", "content_url"],
        "properties": {
            k: {"type": "integer", "minimum": 0} if k == "size_bytes" else {"type": "string"}
            for k in ["artifact_id", "path", "sha256", "size_bytes", "content_url"]
        },
    }
    document["paths"]["/api/v3/artifacts/{artifact_id}"]["get"]["responses"]["200"] = response(
        enveloped(artifact_schema)
    )
    # A run URL adds split to original_run_id. Metric JSON inside remains byte/content unchanged.
    run_schema = {"type": "object", "required": ["run_id", "dataset_id", "metrics", "split"]}
    document["paths"]["/api/v3/runs/{run_id}"]["get"]["responses"]["200"] = response(enveloped(run_schema))
    schema = document["paths"]["/api/v3/runs"]["get"]["responses"]["200"]["content"]["application/json"][
        "schema"
    ]
    schema["properties"]["data"]["items"] = {
        "type": "object",
        "additionalProperties": False,
        "required": ["run_id", "original_run_id", "dataset_id", "chapter", "split", "record"],
        "properties": {
            "run_id": {"type": "string"},
            "original_run_id": {"type": "string"},
            "dataset_id": {"type": "string"},
            "chapter": {"type": "integer"},
            "split": {"type": "string"},
            "record": {"$ref": "#/components/schemas/common/$defs/artifact_ref"},
        },
    }
    for path, key in [
        ("/api/v3/datasets/{dataset_id}/overview", "dataset_id"),
        ("/api/v3/datasets/{dataset_id}/results", "dataset_id"),
        ("/api/v3/jobs/{job_id}/details", "job_id"),
    ]:
        document["paths"][path] = {
            "get": {
                "operationId": "get_" + path.rsplit("/", 1)[-1],
                "parameters": [{"name": key, "in": "path", "required": True, "schema": {"type": "string"}}]
                + ([copy.deepcopy(token)] if key == "job_id" else []),
                "responses": {
                    "200": response(envelope),
                    **{
                        str(c): copy.deepcopy(document["components"]["responses"][f"Error{c}"])
                        for c in [400, 404, 503]
                    },
                },
            }
        }
    document["paths"]["/api/v3/artifacts/{artifact_id}/content"] = {
        "get": {
            "operationId": "download_public_artifact",
            "parameters": [
                {"name": "artifact_id", "in": "path", "required": True, "schema": {"type": "string"}}
            ],
            "responses": {
                "200": {"description": "Allowlisted data-only attachment"},
                "404": copy.deepcopy(document["components"]["responses"]["Error404"]),
            },
        }
    }
    document["paths"]["/api/v3/openapi.json"] = {
        "get": {
            "operationId": "get_openapi",
            "responses": {"200": {"description": "Self-contained OpenAPI3.1.1"}},
        }
    }
    return document
