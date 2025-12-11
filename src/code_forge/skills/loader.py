"""
Skill loading from files and directories.

Discovers and loads skills from various sources.
"""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import ClassVar

from .base import Skill
from .parser import SkillParser

logger = logging.getLogger(__name__)


class SkillLoadError(Exception):
    """Error loading skill."""

    pass


class SkillLoader:
    """Loads skills from files and directories."""

    # Supported file extensions
    SKILL_EXTENSIONS: ClassVar[set[str]] = {".yaml", ".yml", ".md"}

    def __init__(
        self,
        search_paths: list[Path] | None = None,
        parser: SkillParser | None = None,
    ) -> None:
        """Initialize loader.

        Args:
            search_paths: Directories to search for skills
            parser: Parser instance (created if None)
        """
        self.search_paths = search_paths or []
        self.parser = parser or SkillParser()
        self._on_error: list[Callable[[str, list[str]], None]] = []

    def add_search_path(self, path: Path) -> None:
        """Add a search path.

        Args:
            path: Directory to search
        """
        if path not in self.search_paths:
            self.search_paths.append(path)

    def on_error(self, callback: Callable[[str, list[str]], None]) -> None:
        """Register error callback.

        Callback receives (file_path, errors).
        """
        self._on_error.append(callback)

    def load_from_file(self, path: Path) -> Skill | None:
        """Load a skill from a file.

        Args:
            path: Path to skill file

        Returns:
            Skill instance or None if failed
        """
        if not path.exists():
            self._report_error(str(path), [f"File not found: {path}"])
            return None

        if path.suffix not in self.SKILL_EXTENSIONS:
            self._report_error(str(path), [f"Unsupported file type: {path.suffix}"])
            return None

        result = self.parser.parse_file(path)

        if result.errors:
            self._report_error(str(path), result.errors)
            return None

        if result.warnings:
            for warning in result.warnings:
                logger.warning("%s: %s", path, warning)

        if result.definition:
            return Skill(result.definition)

        return None

    def load_from_directory(self, directory: Path) -> list[Skill]:
        """Load all skills from a directory.

        Args:
            directory: Directory to load from

        Returns:
            List of loaded skills
        """
        skills: list[Skill] = []

        if not directory.exists():
            logger.debug("Skill directory not found: %s", directory)
            return skills

        if not directory.is_dir():
            self._report_error(str(directory), [f"Not a directory: {directory}"])
            return skills

        for path in self._get_skill_files(directory):
            skill = self.load_from_file(path)
            if skill:
                skills.append(skill)

        return skills

    def discover_skills(self) -> list[Skill]:
        """Discover all skills in search paths.

        Returns:
            List of all discovered skills
        """
        skills: list[Skill] = []
        seen_names: set[str] = set()

        for search_path in self.search_paths:
            directory_skills = self.load_from_directory(search_path)

            for skill in directory_skills:
                if skill.name in seen_names:
                    logger.warning(
                        "Duplicate skill '%s' in %s, using first found",
                        skill.name,
                        search_path,
                    )
                    continue

                seen_names.add(skill.name)
                skills.append(skill)

        return skills

    def reload_skill(self, name: str) -> Skill | None:
        """Reload a skill by name.

        Searches for the skill file and reloads it.

        Args:
            name: Skill name

        Returns:
            Reloaded skill or None if not found
        """
        for search_path in self.search_paths:
            for ext in self.SKILL_EXTENSIONS:
                path = search_path / f"{name}{ext}"
                if path.exists():
                    return self.load_from_file(path)

        return None

    def _get_skill_files(self, directory: Path) -> list[Path]:
        """Get all skill files from a directory.

        Args:
            directory: Directory to search

        Returns:
            List of skill file paths
        """
        files: list[Path] = []
        for ext in self.SKILL_EXTENSIONS:
            files.extend(directory.glob(f"*{ext}"))
        return sorted(files)  # Sort for deterministic order

    def _report_error(self, path: str, errors: list[str]) -> None:
        """Report loading errors."""
        for error in errors:
            logger.error("Skill load error (%s): %s", path, error)

        for callback in self._on_error:
            try:
                callback(path, errors)
            except Exception as e:
                logger.error("Error callback failed: %s", e)


def get_default_search_paths() -> list[Path]:
    """Get default skill search paths.

    Returns:
        List of paths to search for skills
    """
    paths: list[Path] = []

    # User skills directory
    user_dir = Path.home() / ".forge" / "skills"
    if user_dir.exists():
        paths.append(user_dir)

    # Project skills directory
    project_dir = Path.cwd() / ".forge" / "skills"
    if project_dir.exists():
        paths.append(project_dir)

    return paths


__all__ = [
    "SkillLoadError",
    "SkillLoader",
    "get_default_search_paths",
]
