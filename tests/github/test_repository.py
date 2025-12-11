"""Tests for GitHub repository service."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from code_forge.github.repository import (
    GitHubRepository,
    GitHubBranch,
    GitHubTag,
    RepositoryService,
)
from code_forge.github.client import GitHubClient


class TestGitHubRepository:
    """Tests for GitHubRepository dataclass."""

    def test_from_api(self, sample_repository_data: dict[str, Any]) -> None:
        """Test creating from API response."""
        repo = GitHubRepository.from_api(sample_repository_data)

        assert repo.owner == "testuser"
        assert repo.name == "test-repo"
        assert repo.full_name == "testuser/test-repo"
        assert repo.description == "A test repository"
        assert repo.private is False
        assert repo.default_branch == "main"
        assert repo.language == "Python"
        assert repo.stars == 100
        assert repo.forks == 25
        assert repo.open_issues == 10
        assert repo.archived is False
        assert repo.topics == ["python", "testing"]

    def test_from_api_minimal(self) -> None:
        """Test creating from minimal API response."""
        data = {
            "name": "test-repo",
            "full_name": "testuser/test-repo",
            "owner": {"login": "testuser"},
            "description": None,
            "private": True,
            "default_branch": "main",
            "html_url": "https://github.com/testuser/test-repo",
            "clone_url": "https://github.com/testuser/test-repo.git",
            "ssh_url": "git@github.com:testuser/test-repo.git",
            "language": None,
            "stargazers_count": 0,
            "forks_count": 0,
            "open_issues_count": 0,
        }

        repo = GitHubRepository.from_api(data)

        assert repo.description is None
        assert repo.private is True
        assert repo.language is None
        assert repo.archived is False


class TestGitHubBranch:
    """Tests for GitHubBranch dataclass."""

    def test_from_api(self, sample_branch_data: dict[str, Any]) -> None:
        """Test creating from API response."""
        branch = GitHubBranch.from_api(sample_branch_data)

        assert branch.name == "main"
        assert branch.commit_sha == "abc123def456"
        assert branch.protected is True

    def test_from_api_unprotected(self) -> None:
        """Test creating unprotected branch."""
        data = {
            "name": "feature",
            "commit": {"sha": "xyz789"},
        }

        branch = GitHubBranch.from_api(data)

        assert branch.protected is False


class TestGitHubTag:
    """Tests for GitHubTag dataclass."""

    def test_from_api(self, sample_tag_data: dict[str, Any]) -> None:
        """Test creating from API response."""
        tag = GitHubTag.from_api(sample_tag_data)

        assert tag.name == "v1.0.0"
        assert tag.commit_sha == "abc123def456"
        assert "zipball" in tag.zipball_url
        assert "tarball" in tag.tarball_url


class TestRepositoryService:
    """Tests for RepositoryService class."""

    @pytest.mark.asyncio
    async def test_get(
        self,
        repo_service: RepositoryService,
        sample_repository_data: dict[str, Any],
    ) -> None:
        """Test getting repository."""
        with patch.object(
            repo_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = sample_repository_data

            repo = await repo_service.get("testuser", "test-repo")

        assert repo.name == "test-repo"
        mock_get.assert_called_once_with("/repos/testuser/test-repo")

    @pytest.mark.asyncio
    async def test_list_branches(
        self,
        repo_service: RepositoryService,
        sample_branch_data: dict[str, Any],
    ) -> None:
        """Test listing branches."""
        with patch.object(
            repo_service.client, "get_paginated", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = [sample_branch_data]

            branches = await repo_service.list_branches("testuser", "test-repo")

        assert len(branches) == 1
        assert branches[0].name == "main"

    @pytest.mark.asyncio
    async def test_list_branches_protected(
        self,
        repo_service: RepositoryService,
        sample_branch_data: dict[str, Any],
    ) -> None:
        """Test listing protected branches only."""
        with patch.object(
            repo_service.client, "get_paginated", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = [sample_branch_data]

            await repo_service.list_branches(
                "testuser", "test-repo", protected=True
            )

        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs.get("protected") == "true"

    @pytest.mark.asyncio
    async def test_get_branch(
        self,
        repo_service: RepositoryService,
        sample_branch_data: dict[str, Any],
    ) -> None:
        """Test getting single branch."""
        with patch.object(
            repo_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = sample_branch_data

            branch = await repo_service.get_branch(
                "testuser", "test-repo", "main"
            )

        assert branch.name == "main"
        mock_get.assert_called_once_with(
            "/repos/testuser/test-repo/branches/main"
        )

    @pytest.mark.asyncio
    async def test_list_tags(
        self,
        repo_service: RepositoryService,
        sample_tag_data: dict[str, Any],
    ) -> None:
        """Test listing tags."""
        with patch.object(
            repo_service.client, "get_paginated", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = [sample_tag_data]

            tags = await repo_service.list_tags("testuser", "test-repo")

        assert len(tags) == 1
        assert tags[0].name == "v1.0.0"

    @pytest.mark.asyncio
    async def test_get_readme(
        self,
        repo_service: RepositoryService,
    ) -> None:
        """Test getting README content."""
        with patch.object(
            repo_service.client, "get_raw", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = "# README\n\nTest content"

            content = await repo_service.get_readme("testuser", "test-repo")

        assert content == "# README\n\nTest content"

    @pytest.mark.asyncio
    async def test_get_readme_with_ref(
        self,
        repo_service: RepositoryService,
    ) -> None:
        """Test getting README from specific ref."""
        with patch.object(
            repo_service.client, "get_raw", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = "# README"

            await repo_service.get_readme("testuser", "test-repo", ref="v1.0.0")

        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs.get("ref") == "v1.0.0"

    @pytest.mark.asyncio
    async def test_get_content_file(
        self,
        repo_service: RepositoryService,
    ) -> None:
        """Test getting file content."""
        file_data = {
            "name": "file.py",
            "path": "src/file.py",
            "type": "file",
            "content": "cHJpbnQoJ2hlbGxvJyk=",
        }

        with patch.object(
            repo_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = file_data

            content = await repo_service.get_content(
                "testuser", "test-repo", "src/file.py"
            )

        assert content["name"] == "file.py"

    @pytest.mark.asyncio
    async def test_get_content_directory(
        self,
        repo_service: RepositoryService,
    ) -> None:
        """Test getting directory listing."""
        dir_data = [
            {"name": "file1.py", "type": "file"},
            {"name": "file2.py", "type": "file"},
        ]

        with patch.object(
            repo_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = dir_data

            content = await repo_service.get_content(
                "testuser", "test-repo", "src"
            )

        assert len(content) == 2


class TestRepositoryServiceParseRemoteUrl:
    """Tests for parse_remote_url static method."""

    def test_parse_https_url(self) -> None:
        """Test parsing HTTPS URL."""
        url = "https://github.com/owner/repo.git"
        result = RepositoryService.parse_remote_url(url)

        assert result == ("owner", "repo")

    def test_parse_https_url_no_git(self) -> None:
        """Test parsing HTTPS URL without .git suffix."""
        url = "https://github.com/owner/repo"
        result = RepositoryService.parse_remote_url(url)

        assert result == ("owner", "repo")

    def test_parse_https_url_www(self) -> None:
        """Test parsing HTTPS URL with www."""
        url = "https://www.github.com/owner/repo.git"
        result = RepositoryService.parse_remote_url(url)

        assert result == ("owner", "repo")

    def test_parse_ssh_url(self) -> None:
        """Test parsing SSH URL."""
        url = "git@github.com:owner/repo.git"
        result = RepositoryService.parse_remote_url(url)

        assert result == ("owner", "repo")

    def test_parse_ssh_url_no_git(self) -> None:
        """Test parsing SSH URL without .git suffix."""
        url = "git@github.com:owner/repo"
        result = RepositoryService.parse_remote_url(url)

        assert result == ("owner", "repo")

    def test_parse_non_github_url(self) -> None:
        """Test parsing non-GitHub URL."""
        url = "https://gitlab.com/owner/repo.git"
        result = RepositoryService.parse_remote_url(url)

        assert result is None

    def test_parse_invalid_url(self) -> None:
        """Test parsing invalid URL."""
        url = "not-a-url"
        result = RepositoryService.parse_remote_url(url)

        assert result is None

    def test_parse_http_url(self) -> None:
        """Test parsing HTTP URL."""
        url = "http://github.com/owner/repo.git"
        result = RepositoryService.parse_remote_url(url)

        assert result == ("owner", "repo")
