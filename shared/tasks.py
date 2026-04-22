"""Cloud Tasks enqueue helper."""

import json

from google.api_core.exceptions import AlreadyExists
from google.cloud import tasks_v2

from . import config

_client: tasks_v2.CloudTasksAsyncClient | None = None


def _get_client() -> tasks_v2.CloudTasksAsyncClient:
    """Return the module-level Cloud Tasks async client, creating it if needed.

    Uses a module-level singleton to avoid constructing a new gRPC channel on
    every enqueue call.

    Returns:
        The shared :class:`google.cloud.tasks_v2.CloudTasksAsyncClient`
        instance.
    """
    global _client
    if _client is None:
        _client = tasks_v2.CloudTasksAsyncClient()
    return _client


async def enqueue(
    url: str,
    payload: dict,
    task_id: str | None = None,
    oidc_audience: str | None = None,
    dispatch_deadline_seconds: int = 1800,
) -> None:
    """Enqueue an HTTP POST task on the configured Cloud Tasks queue.

    Args:
        url: The fully qualified HTTPS URL of the Cloud Run worker endpoint.
        payload: JSON-serialisable dict that will be sent as the request body.
        task_id: Optional deterministic task name suffix for deduplication.
        oidc_audience: OIDC token audience override. Defaults to url.
        dispatch_deadline_seconds: How long Cloud Tasks will wait for the
            worker to respond before retrying. Default 1800s (30 min) to
            accommodate long-running PLP scrapes.
    """
    from google.protobuf import duration_pb2

    client = _get_client()
    parent = client.queue_path(
        config.CLOUD_TASKS_PROJECT,
        config.CLOUD_TASKS_LOCATION,
        config.CLOUD_TASKS_QUEUE,
    )
    task: dict = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": url,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(payload).encode(),
        },
        "dispatch_deadline": duration_pb2.Duration(seconds=dispatch_deadline_seconds),
    }
    if config.CLOUD_TASKS_SA_EMAIL:
        task["http_request"]["oidc_token"] = {
            "service_account_email": config.CLOUD_TASKS_SA_EMAIL,
            "audience": oidc_audience or url,
        }
    if task_id:
        task["name"] = f"{parent}/tasks/{task_id}"

    try:
        await client.create_task(parent=parent, task=task)
    except AlreadyExists:
        pass  # task already enqueued from a prior attempt — idempotent
