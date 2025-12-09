"""Tests for GitHub Actions service."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from opencode.github.actions import (
    Workflow,
    WorkflowRun,
    WorkflowJob,
    ActionsService,
)
from opencode.github.client import GitHubClient


class TestWorkflow:
    """Tests for Workflow dataclass."""

    def test_from_api(self, sample_workflow_data: dict[str, Any]) -> None:
        """Test creating from API response."""
        workflow = Workflow.from_api(sample_workflow_data)

        assert workflow.id == 111
        assert workflow.name == "CI"
        assert workflow.path == ".github/workflows/ci.yml"
        assert workflow.state == "active"


class TestWorkflowRun:
    """Tests for WorkflowRun dataclass."""

    def test_from_api(self, sample_workflow_run_data: dict[str, Any]) -> None:
        """Test creating from API response."""
        run = WorkflowRun.from_api(sample_workflow_run_data)

        assert run.id == 222
        assert run.name == "CI"
        assert run.workflow_id == 111
        assert run.status == "completed"
        assert run.conclusion == "success"
        assert run.event == "push"
        assert run.head_branch == "main"
        assert run.run_number == 42


class TestWorkflowJob:
    """Tests for WorkflowJob dataclass."""

    def test_from_api(self, sample_workflow_job_data: dict[str, Any]) -> None:
        """Test creating from API response."""
        job = WorkflowJob.from_api(sample_workflow_job_data)

        assert job.id == 333
        assert job.name == "build"
        assert job.status == "completed"
        assert job.conclusion == "success"
        assert len(job.steps) == 2


class TestActionsService:
    """Tests for ActionsService class."""

    @pytest.mark.asyncio
    async def test_list_workflows(
        self,
        actions_service: ActionsService,
        sample_workflow_data: dict[str, Any],
    ) -> None:
        """Test listing workflows."""
        with patch.object(
            actions_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = {"workflows": [sample_workflow_data]}

            workflows = await actions_service.list_workflows(
                "testuser", "test-repo"
            )

        assert len(workflows) == 1
        assert workflows[0].name == "CI"

    @pytest.mark.asyncio
    async def test_list_runs(
        self,
        actions_service: ActionsService,
        sample_workflow_run_data: dict[str, Any],
    ) -> None:
        """Test listing workflow runs."""
        with patch.object(
            actions_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = {"workflow_runs": [sample_workflow_run_data]}

            runs = await actions_service.list_runs("testuser", "test-repo")

        assert len(runs) == 1
        assert runs[0].id == 222

    @pytest.mark.asyncio
    async def test_list_runs_for_workflow(
        self,
        actions_service: ActionsService,
        sample_workflow_run_data: dict[str, Any],
    ) -> None:
        """Test listing runs for specific workflow."""
        with patch.object(
            actions_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = {"workflow_runs": [sample_workflow_run_data]}

            await actions_service.list_runs(
                "testuser", "test-repo",
                workflow_id=111,
            )

        mock_get.assert_called_once()
        call_args = mock_get.call_args[0]
        assert "workflows/111" in call_args[0]

    @pytest.mark.asyncio
    async def test_list_runs_with_filters(
        self,
        actions_service: ActionsService,
    ) -> None:
        """Test listing runs with filters."""
        with patch.object(
            actions_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = {"workflow_runs": []}

            await actions_service.list_runs(
                "testuser", "test-repo",
                branch="main",
                event="push",
                status="completed",
                actor="testuser",
            )

        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["branch"] == "main"
        assert call_kwargs["event"] == "push"
        assert call_kwargs["status"] == "completed"
        assert call_kwargs["actor"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_run(
        self,
        actions_service: ActionsService,
        sample_workflow_run_data: dict[str, Any],
    ) -> None:
        """Test getting single workflow run."""
        with patch.object(
            actions_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = sample_workflow_run_data

            run = await actions_service.get_run("testuser", "test-repo", 222)

        assert run.id == 222
        mock_get.assert_called_once_with(
            "/repos/testuser/test-repo/actions/runs/222"
        )

    @pytest.mark.asyncio
    async def test_list_run_jobs(
        self,
        actions_service: ActionsService,
        sample_workflow_job_data: dict[str, Any],
    ) -> None:
        """Test listing jobs for a run."""
        with patch.object(
            actions_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = {"jobs": [sample_workflow_job_data]}

            jobs = await actions_service.list_run_jobs(
                "testuser", "test-repo", 222
            )

        assert len(jobs) == 1
        assert jobs[0].name == "build"

    @pytest.mark.asyncio
    async def test_list_run_jobs_all(
        self,
        actions_service: ActionsService,
    ) -> None:
        """Test listing all jobs (not just latest)."""
        with patch.object(
            actions_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = {"jobs": []}

            await actions_service.list_run_jobs(
                "testuser", "test-repo", 222,
                filter_jobs="all",
            )

        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["filter"] == "all"

    @pytest.mark.asyncio
    async def test_get_run_logs(
        self,
        actions_service: ActionsService,
    ) -> None:
        """Test getting run logs."""
        with patch.object(
            actions_service.client, "get_raw", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = "https://logs.url/download"

            result = await actions_service.get_run_logs(
                "testuser", "test-repo", 222
            )

        assert result == "https://logs.url/download"

    @pytest.mark.asyncio
    async def test_rerun(
        self,
        actions_service: ActionsService,
    ) -> None:
        """Test re-running workflow."""
        with patch.object(
            actions_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = None

            await actions_service.rerun("testuser", "test-repo", 222)

        mock_post.assert_called_once_with(
            "/repos/testuser/test-repo/actions/runs/222/rerun",
            {},
        )

    @pytest.mark.asyncio
    async def test_rerun_failed(
        self,
        actions_service: ActionsService,
    ) -> None:
        """Test re-running failed jobs only."""
        with patch.object(
            actions_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = None

            await actions_service.rerun_failed("testuser", "test-repo", 222)

        mock_post.assert_called_once_with(
            "/repos/testuser/test-repo/actions/runs/222/rerun-failed-jobs",
            {},
        )

    @pytest.mark.asyncio
    async def test_cancel(
        self,
        actions_service: ActionsService,
    ) -> None:
        """Test cancelling workflow run."""
        with patch.object(
            actions_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = None

            await actions_service.cancel("testuser", "test-repo", 222)

        mock_post.assert_called_once_with(
            "/repos/testuser/test-repo/actions/runs/222/cancel",
            {},
        )

    @pytest.mark.asyncio
    async def test_get_job_logs(
        self,
        actions_service: ActionsService,
    ) -> None:
        """Test getting job logs."""
        with patch.object(
            actions_service.client, "get_raw", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = "Job log content..."

            result = await actions_service.get_job_logs(
                "testuser", "test-repo", 333
            )

        assert result == "Job log content..."
        mock_get.assert_called_once_with(
            "/repos/testuser/test-repo/actions/jobs/333/logs"
        )
