"""GitHub context for LLM integration."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import GitHubClient
    from .issues import GitHubIssue, IssueService
    from .pull_requests import GitHubPullRequest, PullRequestService
    from .repository import GitHubRepository, RepositoryService


class GitHubContext:
    """GitHub context for LLM."""

    def __init__(
        self,
        client: GitHubClient,
        repo_service: RepositoryService,
        issue_service: IssueService,
        pr_service: PullRequestService,
    ):
        """Initialize GitHub context."""
        self.client = client
        self.repo_service = repo_service
        self.issue_service = issue_service
        self.pr_service = pr_service

    async def get_context_summary(
        self,
        owner: str,
        repo: str,
    ) -> str:
        """Get GitHub context summary for system prompt."""
        try:
            repo_info = await self.repo_service.get(owner, repo)
            return self._format_repo_summary(repo_info)
        except Exception:
            return f"GitHub: {owner}/{repo} (unable to fetch details)"

    def _format_repo_summary(self, repo: GitHubRepository) -> str:
        """Format repository summary."""
        lines = [
            f"GitHub Repository: {repo.full_name}",
            f"  Description: {repo.description or 'No description'}",
            f"  Default branch: {repo.default_branch}",
            f"  Visibility: {'Private' if repo.private else 'Public'}",
            f"  Language: {repo.language or 'Not specified'}",
            f"  Open issues: {repo.open_issues}",
        ]
        if repo.archived:
            lines.append("  Status: ARCHIVED")
        return "\n".join(lines)

    def format_issue(self, issue: GitHubIssue) -> str:
        """Format issue for LLM context."""
        lines = [
            f"Issue #{issue.number}: {issue.title}",
            f"State: {issue.state}",
            f"Author: @{issue.author.login}",
            f"Created: {issue.created_at}",
        ]

        if issue.assignees:
            assignees = ", ".join(f"@{a.login}" for a in issue.assignees)
            lines.append(f"Assignees: {assignees}")

        if issue.labels:
            labels = ", ".join(label.name for label in issue.labels)
            lines.append(f"Labels: {labels}")

        if issue.body:
            lines.append("")
            lines.append("Description:")
            lines.append(issue.body)

        return "\n".join(lines)

    def format_pr(self, pr: GitHubPullRequest) -> str:
        """Format PR for LLM context."""
        lines = [
            f"Pull Request #{pr.number}: {pr.title}",
            f"State: {pr.state}",
            f"Author: @{pr.author.login}",
            f"Branch: {pr.head_ref} -> {pr.base_ref}",
            f"Created: {pr.created_at}",
        ]

        if pr.draft:
            lines.append("Status: DRAFT")
        if pr.merged:
            lines.append(f"Merged: {pr.merged_at}")

        lines.append(
            f"Changes: +{pr.additions} -{pr.deletions} "
            f"in {pr.changed_files} files"
        )

        if pr.assignees:
            assignees = ", ".join(f"@{a.login}" for a in pr.assignees)
            lines.append(f"Assignees: {assignees}")

        if pr.requested_reviewers:
            reviewers = ", ".join(
                f"@{r.login}" for r in pr.requested_reviewers
            )
            lines.append(f"Reviewers: {reviewers}")

        if pr.labels:
            labels = ", ".join(label.name for label in pr.labels)
            lines.append(f"Labels: {labels}")

        if pr.body:
            lines.append("")
            lines.append("Description:")
            lines.append(pr.body)

        return "\n".join(lines)

    def format_issue_list(self, issues: list[GitHubIssue]) -> str:
        """Format issue list for display."""
        if not issues:
            return "No issues found."

        lines = []
        for issue in issues:
            labels = ""
            if issue.labels:
                labels = f" [{', '.join(label.name for label in issue.labels)}]"

            lines.append(
                f"#{issue.number} {issue.title}{labels} "
                f"(@{issue.author.login})"
            )
        return "\n".join(lines)

    def format_pr_list(self, prs: list[GitHubPullRequest]) -> str:
        """Format PR list for display."""
        if not prs:
            return "No pull requests found."

        lines = []
        for pr in prs:
            status = ""
            if pr.draft:
                status = " [DRAFT]"
            elif pr.merged:
                status = " [MERGED]"

            lines.append(
                f"#{pr.number} {pr.title}{status} "
                f"({pr.head_ref} -> {pr.base_ref}) "
                f"@{pr.author.login}"
            )
        return "\n".join(lines)
