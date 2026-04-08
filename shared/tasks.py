"""Cloud Tasks enqueue helper."""

import json

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


async def enqueue(url: str, payload: dict, task_id: str | None = None) -> None:
    """Enqueue an HTTP POST task on the configured Cloud Tasks queue.

    The task body is JSON-encoded and sent to ``url`` as an ``application/json``
    POST request. If :data:`config.CLOUD_TASKS_SA_EMAIL` is set, an OIDC token
    is attached to authenticate the request against the target Cloud Run service.
    Providing a ``task_id`` makes the task name deterministic, which prevents
    duplicate enqueueing for the same job.

    Args:
        url: The fully qualified HTTPS URL of the Cloud Run worker endpoint
            that should receive the task.
        payload: JSON-serialisable dict that will be sent as the request body.
        task_id: Optional deterministic task name suffix. When provided, Cloud
            Tasks will reject duplicate tasks with the same ID within the
            deduplication window.
    """
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
        }
    }
    if config.CLOUD_TASKS_SA_EMAIL:
        task["http_request"]["oidc_token"] = {
            "service_account_email": config.CLOUD_TASKS_SA_EMAIL,
            "audience": url,
        }
    if task_id:
        task["name"] = f"{parent}/tasks/{task_id}"

    await client.create_task(parent=parent, task=task)
