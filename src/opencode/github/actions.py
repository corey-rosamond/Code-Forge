"""GitHub Actions operations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import GitHubClient


@dataclass
class WorkflowRun:
    """GitHub Actions workflow run."""

    id: int
    name: str
    workflow_id: int
    status: str
    conclusion: str | None
    event: str
    head_branch: str
    head_sha: str
    run_number: int
    run_attempt: int
    created_at: str
    updated_at: str
    url: str
    html_url: str
    jobs_url: str
    logs_url: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> WorkflowRun:
        """Create from API response."""
        return cls(
            id=data["id"],
            name=data["name"],
            workflow_id=data["workflow_id"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            event=data["event"],
            head_branch=data["head_branch"],
            head_sha=data["head_sha"],
            run_number=data["run_number"],
            run_attempt=data["run_attempt"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            url=data["url"],
            html_url=data["html_url"],
            jobs_url=data["jobs_url"],
            logs_url=data["logs_url"],
        )


@dataclass
class WorkflowJob:
    """GitHub Actions workflow job."""

    id: int
    name: str
    status: str
    conclusion: str | None
    started_at: str | None
    completed_at: str | None
    run_id: int
    html_url: str
    steps: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> WorkflowJob:
        """Create from API response."""
        return cls(
            id=data["id"],
            name=data["name"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            run_id=data["run_id"],
            html_url=data["html_url"],
            steps=data.get("steps", []),
        )


@dataclass
class Workflow:
    """GitHub Actions workflow."""

    id: int
    name: str
    path: str
    state: str
    created_at: str
    updated_at: str
    url: str
    html_url: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Workflow:
        """Create from API response."""
        return cls(
            id=data["id"],
            name=data["name"],
            path=data["path"],
            state=data["state"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            url=data["url"],
            html_url=data["html_url"],
        )


class ActionsService:
    """GitHub Actions operations."""

    def __init__(self, client: GitHubClient):
        """Initialize actions service."""
        self.client = client

    async def list_workflows(
        self,
        owner: str,
        repo: str,
    ) -> list[Workflow]:
        """List repository workflows."""
        data = await self.client.get(
            f"/repos/{owner}/{repo}/actions/workflows"
        )
        return [Workflow.from_api(w) for w in data.get("workflows", [])]

    async def list_runs(
        self,
        owner: str,
        repo: str,
        workflow_id: int | str | None = None,
        branch: str | None = None,
        event: str | None = None,
        status: str | None = None,
        actor: str | None = None,
    ) -> list[WorkflowRun]:
        """
        List workflow runs.

        Args:
            workflow_id: Filter by workflow ID or filename.
            branch: Filter by branch.
            event: Filter by event type (push, pull_request, etc).
            status: Filter by status (queued, in_progress, completed).
            actor: Filter by actor (user who triggered).
        """
        params: dict[str, Any] = {}
        if branch:
            params["branch"] = branch
        if event:
            params["event"] = event
        if status:
            params["status"] = status
        if actor:
            params["actor"] = actor

        if workflow_id:
            path = f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
        else:
            path = f"/repos/{owner}/{repo}/actions/runs"

        data = await self.client.get(path, **params)
        return [WorkflowRun.from_api(r) for r in data.get("workflow_runs", [])]

    async def get_run(
        self,
        owner: str,
        repo: str,
        run_id: int,
    ) -> WorkflowRun:
        """Get workflow run."""
        data = await self.client.get(
            f"/repos/{owner}/{repo}/actions/runs/{run_id}"
        )
        return WorkflowRun.from_api(data)

    async def list_run_jobs(
        self,
        owner: str,
        repo: str,
        run_id: int,
        filter_jobs: str = "latest",
    ) -> list[WorkflowJob]:
        """
        List jobs for a workflow run.

        Args:
            filter_jobs: latest or all
        """
        data = await self.client.get(
            f"/repos/{owner}/{repo}/actions/runs/{run_id}/jobs",
            filter=filter_jobs,
        )
        return [WorkflowJob.from_api(j) for j in data.get("jobs", [])]

    async def get_run_logs(
        self,
        owner: str,
        repo: str,
        run_id: int,
    ) -> str:
        """
        Get workflow run logs.

        Returns URL to download logs (zip file).
        """
        # This endpoint redirects to download URL
        return await self.client.get_raw(
            f"/repos/{owner}/{repo}/actions/runs/{run_id}/logs"
        )

    async def rerun(
        self,
        owner: str,
        repo: str,
        run_id: int,
    ) -> None:
        """Re-run all jobs in workflow."""
        await self.client.post(
            f"/repos/{owner}/{repo}/actions/runs/{run_id}/rerun",
            {},
        )

    async def rerun_failed(
        self,
        owner: str,
        repo: str,
        run_id: int,
    ) -> None:
        """Re-run only failed jobs."""
        await self.client.post(
            f"/repos/{owner}/{repo}/actions/runs/{run_id}/rerun-failed-jobs",
            {},
        )

    async def cancel(
        self,
        owner: str,
        repo: str,
        run_id: int,
    ) -> None:
        """Cancel workflow run."""
        await self.client.post(
            f"/repos/{owner}/{repo}/actions/runs/{run_id}/cancel",
            {},
        )

    async def get_job_logs(
        self,
        owner: str,
        repo: str,
        job_id: int,
    ) -> str:
        """Get job logs."""
        return await self.client.get_raw(
            f"/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
        )
