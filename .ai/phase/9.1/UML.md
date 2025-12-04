# Phase 9.1: Git Integration - UML Diagrams

**Phase:** 9.1
**Name:** Git Integration
**Dependencies:** Phase 2.3 (Execution Tools), Phase 2.1 (Tool System)

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Git Integration System                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────┐
│          <<dataclass>>              │
│            GitRemote                │
├─────────────────────────────────────┤
│ + name: str                         │
│ + url: str                          │
│ + fetch_url: str | None             │
│ + push_url: str | None              │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│          <<dataclass>>              │
│            GitBranch                │
├─────────────────────────────────────┤
│ + name: str                         │
│ + is_current: bool                  │
│ + tracking: str | None              │
│ + ahead: int                        │
│ + behind: int                       │
│ + commit: str | None                │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│          <<dataclass>>              │
│            GitCommit                │
├─────────────────────────────────────┤
│ + hash: str                         │
│ + short_hash: str                   │
│ + author: str                       │
│ + author_email: str                 │
│ + date: str                         │
│ + message: str                      │
│ + parent_hashes: list[str]          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│          <<dataclass>>              │
│         RepositoryInfo              │
├─────────────────────────────────────┤
│ + root: Path                        │
│ + is_git_repo: bool                 │
│ + current_branch: str | None        │
│ + head_commit: GitCommit | None     │
│ + is_dirty: bool                    │
│ + remotes: list[GitRemote]          │
└─────────────────────────────────────┘

                              ┌─────────────────────────────────────┐
                              │          GitRepository              │
                              ├─────────────────────────────────────┤
                              │ - _path: Path                       │
                              │ - _root: Path | None                │
                              │ - _is_repo: bool | None             │
                              ├─────────────────────────────────────┤
                              │ + __init__(path: Path | None)       │
                              │ + is_git_repo: bool                 │
                              │ + root: Path                        │
                              │ + current_branch: str | None        │
                              │ + is_dirty: bool                    │
                              │ + get_info(): RepositoryInfo        │
                              │ + get_remotes(): list[GitRemote]    │
                              │ + get_branches(all): list[GitBranch]│
                              │ + run_git(*args): tuple[str,str,int]│
                              └──────────────────┬──────────────────┘
                                                 │
                    ┌────────────────────────────┼────────────────────────────┐
                    │                            │                            │
                    ▼                            ▼                            ▼
┌─────────────────────────────┐  ┌─────────────────────────────┐  ┌─────────────────────────────┐
│       GitStatusTool         │  │         GitHistory          │  │        GitDiffTool          │
├─────────────────────────────┤  ├─────────────────────────────┤  ├─────────────────────────────┤
│ - repo: GitRepository       │  │ - repo: GitRepository       │  │ - repo: GitRepository       │
├─────────────────────────────┤  ├─────────────────────────────┤  ├─────────────────────────────┤
│ + get_status(): GitStatus   │  │ + get_log(): list[LogEntry] │  │ + diff_working(): GitDiff   │
│ + get_staged_diff(): str    │  │ + get_commit(ref): GitCommit│  │ + diff_commits(): GitDiff   │
│ + get_unstaged_diff(): str  │  │ + get_commit_files(): list  │  │ + diff_branches(): GitDiff  │
└─────────────────────────────┘  │ + get_commit_diff(): str    │  └─────────────────────────────┘
                                 └─────────────────────────────┘

┌─────────────────────────────────────┐       ┌─────────────────────────────────────┐
│          <<dataclass>>              │       │          <<dataclass>>              │
│           FileStatus                │       │            GitStatus                │
├─────────────────────────────────────┤       ├─────────────────────────────────────┤
│ + path: str                         │       │ + branch: str | None                │
│ + status: str                       │◄──────│ + tracking: str | None              │
│ + staged: bool                      │       │ + ahead: int                        │
│ + original_path: str | None         │       │ + behind: int                       │
└─────────────────────────────────────┘       │ + staged: list[FileStatus]          │
                                              │ + unstaged: list[FileStatus]        │
                                              │ + untracked: list[FileStatus]       │
                                              │ + conflicts: list[FileStatus]       │
                                              ├─────────────────────────────────────┤
                                              │ + is_clean: bool                    │
                                              │ + to_string(): str                  │
                                              └─────────────────────────────────────┘

┌─────────────────────────────────────┐       ┌─────────────────────────────────────┐
│          <<dataclass>>              │       │          <<dataclass>>              │
│            DiffFile                 │       │            GitDiff                  │
├─────────────────────────────────────┤       ├─────────────────────────────────────┤
│ + path: str                         │       │ + files: list[DiffFile]             │
│ + old_path: str | None              │◄──────│ + total_additions: int              │
│ + status: str                       │       │ + total_deletions: int              │
│ + additions: int                    │       │ + stat: str                         │
│ + deletions: int                    │       ├─────────────────────────────────────┤
│ + content: str | None               │       │ + to_string(include_content): str   │
└─────────────────────────────────────┘       └─────────────────────────────────────┘

┌─────────────────────────────────────┐       ┌─────────────────────────────────────┐
│          <<dataclass>>              │       │            GitSafety                │
│          SafetyCheck                │       ├─────────────────────────────────────┤
├─────────────────────────────────────┤       │ - repo: GitRepository               │
│ + safe: bool                        │◄──────├─────────────────────────────────────┤
│ + reason: str | None                │       │ + check_amend(): SafetyCheck        │
│ + warnings: list[str]               │       │ + check_force_push(): SafetyCheck   │
└─────────────────────────────────────┘       │ + check_branch_delete(): SafetyCheck│
                                              │ + check_hard_reset(): SafetyCheck   │
                                              │ + get_head_authorship(): tuple      │
                                              │ + is_pushed(ref): bool              │
                                              └─────────────────────────────────────┘

                              ┌─────────────────────────────────────┐
                              │          GitOperations              │
                              ├─────────────────────────────────────┤
                              │ - repo: GitRepository               │
                              │ - safety: GitSafety                 │
                              ├─────────────────────────────────────┤
                              │ + stage(paths): None                │
                              │ + unstage(paths): None              │
                              │ + stage_all(): None                 │
                              │ + commit(message, amend): GitCommit │
                              │ + create_branch(name): GitBranch    │
                              │ + switch_branch(name): None         │
                              │ + delete_branch(name, force): None  │
                              │ + fetch(remote): None               │
                              │ + pull(remote): None                │
                              │ + push(remote, branch, upstream)    │
                              └─────────────────────────────────────┘

┌─────────────────────────────────────┐
│           GitContext                │
├─────────────────────────────────────┤
│ - repo: GitRepository               │
├─────────────────────────────────────┤
│ + get_context_summary(): str        │
│ + get_status_summary(): str         │
│ + format_for_commit(diff): str      │
└─────────────────────────────────────┘
```

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Git Integration                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │  repository  │     │    status    │     │   history    │                │
│  │     .py      │◄────│     .py      │     │     .py      │                │
│  │              │     │              │     │              │                │
│  │ GitRepository│     │GitStatusTool │     │  GitHistory  │                │
│  │ RepositoryInfo│    │  GitStatus   │     │  LogEntry    │                │
│  │  GitRemote   │     │ FileStatus   │     │              │                │
│  │  GitBranch   │     └──────────────┘     └──────────────┘                │
│  │  GitCommit   │            │                    │                        │
│  └──────┬───────┘            │                    │                        │
│         │                    │                    │                        │
│         ▼                    ▼                    ▼                        │
│  ┌──────────────────────────────────────────────────────────────┐          │
│  │                        run_git()                              │          │
│  │                   (async subprocess)                          │          │
│  └──────────────────────────────────────────────────────────────┘          │
│         ▲                    ▲                    ▲                        │
│         │                    │                    │                        │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │     diff     │     │  operations  │     │    safety    │                │
│  │     .py      │     │     .py      │────▶│     .py      │                │
│  │              │     │              │     │              │                │
│  │ GitDiffTool  │     │GitOperations │     │  GitSafety   │                │
│  │   GitDiff    │     │              │     │ SafetyCheck  │                │
│  │   DiffFile   │     └──────────────┘     └──────────────┘                │
│  └──────────────┘                                                          │
│                                                                             │
│  ┌──────────────┐                                                          │
│  │   context    │                                                          │
│  │     .py      │                                                          │
│  │              │                                                          │
│  │  GitContext  │                                                          │
│  └──────────────┘                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           External: git binary                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Sequence Diagram: Get Repository Status

```
┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────┐
│  User   │     │GitStatusTool │     │GitRepository │     │   git   │
└────┬────┘     └──────┬───────┘     └──────┬───────┘     └────┬────┘
     │                 │                    │                   │
     │  get_status()   │                    │                   │
     │────────────────▶│                    │                   │
     │                 │                    │                   │
     │                 │   run_git("status",│                   │
     │                 │     "--porcelain=v2", "-b")            │
     │                 │───────────────────▶│                   │
     │                 │                    │                   │
     │                 │                    │  git status ...   │
     │                 │                    │──────────────────▶│
     │                 │                    │                   │
     │                 │                    │  porcelain output │
     │                 │                    │◀──────────────────│
     │                 │                    │                   │
     │                 │  (stdout, stderr,  │                   │
     │                 │   returncode)      │                   │
     │                 │◀───────────────────│                   │
     │                 │                    │                   │
     │                 │                    │                   │
     │                 │  [parse output]    │                   │
     │                 │  - branch info     │                   │
     │                 │  - staged files    │                   │
     │                 │  - unstaged files  │                   │
     │                 │  - untracked       │                   │
     │                 │                    │                   │
     │   GitStatus     │                    │                   │
     │◀────────────────│                    │                   │
     │                 │                    │                   │
```

---

## Sequence Diagram: Safe Commit with Amend

```
┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────┐
│  User   │     │GitOperations │     │  GitSafety   │     │GitRepository │     │   git   │
└────┬────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └────┬────┘
     │                 │                    │                    │                  │
     │ commit(msg,     │                    │                    │                  │
     │   amend=True)   │                    │                    │                  │
     │────────────────▶│                    │                    │                  │
     │                 │                    │                    │                  │
     │                 │  check_amend()     │                    │                  │
     │                 │───────────────────▶│                    │                  │
     │                 │                    │                    │                  │
     │                 │                    │ get_head_authorship()                 │
     │                 │                    │───────────────────▶│                  │
     │                 │                    │                    │                  │
     │                 │                    │                    │  git log -1      │
     │                 │                    │                    │  --format='%an %ae'
     │                 │                    │                    │─────────────────▶│
     │                 │                    │                    │                  │
     │                 │                    │                    │  author info     │
     │                 │                    │                    │◀─────────────────│
     │                 │                    │                    │                  │
     │                 │                    │  (author, email)   │                  │
     │                 │                    │◀───────────────────│                  │
     │                 │                    │                    │                  │
     │                 │                    │  is_pushed("HEAD") │                  │
     │                 │                    │───────────────────▶│                  │
     │                 │                    │                    │                  │
     │                 │                    │                    │ git branch -r    │
     │                 │                    │                    │ --contains HEAD  │
     │                 │                    │                    │─────────────────▶│
     │                 │                    │                    │                  │
     │                 │                    │                    │  (empty = not    │
     │                 │                    │                    │   pushed)        │
     │                 │                    │                    │◀─────────────────│
     │                 │                    │                    │                  │
     │                 │                    │  bool              │                  │
     │                 │                    │◀───────────────────│                  │
     │                 │                    │                    │                  │
     │                 │  SafetyCheck       │                    │                  │
     │                 │  (safe=True)       │                    │                  │
     │                 │◀───────────────────│                    │                  │
     │                 │                    │                    │                  │
     │                 │  run_git("commit", │                    │                  │
     │                 │    "--amend", "-m", msg)                │                  │
     │                 │───────────────────────────────────────▶ │                  │
     │                 │                    │                    │                  │
     │                 │                    │                    │  git commit ...  │
     │                 │                    │                    │─────────────────▶│
     │                 │                    │                    │                  │
     │                 │                    │                    │  success         │
     │                 │                    │                    │◀─────────────────│
     │                 │                    │                    │                  │
     │                 │  result            │                    │                  │
     │                 │◀──────────────────────────────────────── │                  │
     │                 │                    │                    │                  │
     │   GitCommit     │                    │                    │                  │
     │◀────────────────│                    │                    │                  │
     │                 │                    │                    │                  │
```

---

## Sequence Diagram: Get Diff Between Branches

```
┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────┐
│  User   │     │ GitDiffTool  │     │GitRepository │     │   git   │
└────┬────┘     └──────┬───────┘     └──────┬───────┘     └────┬────┘
     │                 │                    │                   │
     │ diff_branches(  │                    │                   │
     │   "main",       │                    │                   │
     │   "feature")    │                    │                   │
     │────────────────▶│                    │                   │
     │                 │                    │                   │
     │                 │  run_git("diff",   │                   │
     │                 │    "--stat",       │                   │
     │                 │    "main...feature")                   │
     │                 │───────────────────▶│                   │
     │                 │                    │                   │
     │                 │                    │  git diff --stat  │
     │                 │                    │  main...feature   │
     │                 │                    │──────────────────▶│
     │                 │                    │                   │
     │                 │                    │  stat output      │
     │                 │                    │◀──────────────────│
     │                 │                    │                   │
     │                 │  stat string       │                   │
     │                 │◀───────────────────│                   │
     │                 │                    │                   │
     │                 │  run_git("diff",   │                   │
     │                 │    "--numstat",    │                   │
     │                 │    "main...feature")                   │
     │                 │───────────────────▶│                   │
     │                 │                    │                   │
     │                 │                    │  git diff --numstat│
     │                 │                    │──────────────────▶│
     │                 │                    │                   │
     │                 │                    │  numstat output   │
     │                 │                    │◀──────────────────│
     │                 │                    │                   │
     │                 │  file stats        │                   │
     │                 │◀───────────────────│                   │
     │                 │                    │                   │
     │                 │  run_git("diff",   │                   │
     │                 │    "main...feature")                   │
     │                 │───────────────────▶│                   │
     │                 │                    │                   │
     │                 │                    │  git diff ...     │
     │                 │                    │──────────────────▶│
     │                 │                    │                   │
     │                 │                    │  diff content     │
     │                 │                    │◀──────────────────│
     │                 │                    │                   │
     │                 │  diff output       │                   │
     │                 │◀───────────────────│                   │
     │                 │                    │                   │
     │                 │  [parse and build  │                   │
     │                 │   GitDiff with     │                   │
     │                 │   DiffFile list]   │                   │
     │                 │                    │                   │
     │   GitDiff       │                    │                   │
     │◀────────────────│                    │                   │
     │                 │                    │                   │
```

---

## Sequence Diagram: Repository Detection

```
┌─────────┐     ┌──────────────┐     ┌─────────┐
│  User   │     │GitRepository │     │   git   │
└────┬────┘     └──────┬───────┘     └────┬────┘
     │                 │                   │
     │ __init__(path)  │                   │
     │────────────────▶│                   │
     │                 │                   │
     │                 │                   │
     │ is_git_repo     │                   │
     │────────────────▶│                   │
     │                 │                   │
     │                 │  git rev-parse    │
     │                 │  --git-dir        │
     │                 │──────────────────▶│
     │                 │                   │
     │                 │  .git (or error)  │
     │                 │◀──────────────────│
     │                 │                   │
     │   True/False    │                   │
     │◀────────────────│                   │
     │                 │                   │
     │ root            │                   │
     │────────────────▶│                   │
     │                 │                   │
     │                 │  git rev-parse    │
     │                 │  --show-toplevel  │
     │                 │──────────────────▶│
     │                 │                   │
     │                 │  /path/to/repo    │
     │                 │◀──────────────────│
     │                 │                   │
     │   Path          │                   │
     │◀────────────────│                   │
     │                 │                   │
```

---

## Sequence Diagram: Branch Operations with Safety

```
┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────┐
│  User   │     │GitOperations │     │  GitSafety   │     │GitRepository │     │   git   │
└────┬────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └────┬────┘
     │                 │                    │                    │                  │
     │ delete_branch(  │                    │                    │                  │
     │   "feature")    │                    │                    │                  │
     │────────────────▶│                    │                    │                  │
     │                 │                    │                    │                  │
     │                 │ check_branch_delete│                    │                  │
     │                 │   ("feature")      │                    │                  │
     │                 │───────────────────▶│                    │                  │
     │                 │                    │                    │                  │
     │                 │                    │ run_git("branch",  │                  │
     │                 │                    │   "-r", "--contains",                 │
     │                 │                    │   "feature")       │                  │
     │                 │                    │───────────────────▶│                  │
     │                 │                    │                    │                  │
     │                 │                    │                    │  git branch ...  │
     │                 │                    │                    │─────────────────▶│
     │                 │                    │                    │                  │
     │                 │                    │                    │  origin/feature  │
     │                 │                    │                    │◀─────────────────│
     │                 │                    │                    │                  │
     │                 │                    │  remote branches   │                  │
     │                 │                    │◀───────────────────│                  │
     │                 │                    │                    │                  │
     │                 │                    │ run_git("log",     │                  │
     │                 │                    │   "--oneline",     │                  │
     │                 │                    │   "feature",       │                  │
     │                 │                    │   "^main", "-1")   │                  │
     │                 │                    │───────────────────▶│                  │
     │                 │                    │                    │                  │
     │                 │                    │                    │  git log ...     │
     │                 │                    │                    │─────────────────▶│
     │                 │                    │                    │                  │
     │                 │                    │                    │  (empty = merged)│
     │                 │                    │                    │◀─────────────────│
     │                 │                    │                    │                  │
     │                 │                    │  is merged status  │                  │
     │                 │                    │◀───────────────────│                  │
     │                 │                    │                    │                  │
     │                 │  SafetyCheck       │                    │                  │
     │                 │  (safe=True,       │                    │                  │
     │                 │   warnings=        │                    │                  │
     │                 │   ["pushed to      │                    │                  │
     │                 │    remote"])       │                    │                  │
     │                 │◀───────────────────│                    │                  │
     │                 │                    │                    │                  │
     │                 │  run_git("branch", │                    │                  │
     │                 │    "-d", "feature")│                    │                  │
     │                 │───────────────────────────────────────▶ │                  │
     │                 │                    │                    │                  │
     │                 │                    │                    │  git branch -d   │
     │                 │                    │                    │─────────────────▶│
     │                 │                    │                    │                  │
     │                 │                    │                    │  deleted         │
     │                 │                    │                    │◀─────────────────│
     │                 │                    │                    │                  │
     │                 │  success           │                    │                  │
     │                 │◀──────────────────────────────────────── │                  │
     │                 │                    │                    │                  │
     │   None          │                    │                    │                  │
     │◀────────────────│                    │                    │                  │
     │                 │                    │                    │                  │
```

---

## State Diagram: Git Working Tree States

```
                              ┌─────────────────┐
                              │                 │
                              │     Clean       │
                              │   (no changes)  │
                              │                 │
                              └────────┬────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
           ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
           │                │  │                │  │                │
           │   Untracked    │  │   Modified     │  │    Deleted     │
           │   (new files)  │  │   (changed)    │  │   (removed)    │
           │                │  │                │  │                │
           └───────┬────────┘  └───────┬────────┘  └───────┬────────┘
                   │                   │                   │
                   │    git add        │    git add        │    git add
                   │                   │                   │
                   ▼                   ▼                   ▼
           ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
           │                │  │                │  │                │
           │  Staged New    │  │ Staged Modified│  │ Staged Deleted │
           │                │  │                │  │                │
           └───────┬────────┘  └───────┬────────┘  └───────┬────────┘
                   │                   │                   │
                   │                   │                   │
                   └───────────────────┼───────────────────┘
                                       │
                                       │    git commit
                                       │
                                       ▼
                              ┌─────────────────┐
                              │                 │
                              │   Committed     │
                              │                 │
                              └────────┬────────┘
                                       │
                            ┌──────────┴──────────┐
                            │                     │
                            ▼                     ▼
                   ┌────────────────┐    ┌────────────────┐
                   │                │    │                │
                   │  Local Only    │    │    Pushed      │
                   │  (not pushed)  │    │   (on remote)  │
                   │                │    │                │
                   └────────────────┘    └────────────────┘
```

---

## Activity Diagram: Commit Workflow with Safety

```
                        ┌─────────────────┐
                        │     Start       │
                        │  commit(msg,    │
                        │   amend=False)  │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ Check if amend  │
                        │   requested?    │
                        └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    │ Yes                     │ No
                    ▼                         │
           ┌────────────────┐                 │
           │  check_amend() │                 │
           │  safety check  │                 │
           └───────┬────────┘                 │
                   │                          │
           ┌───────┴───────┐                  │
           │               │                  │
       SafetyCheck     SafetyCheck            │
       safe=False      safe=True              │
           │               │                  │
           ▼               │                  │
   ┌────────────────┐      │                  │
   │  Raise Error   │      │                  │
   │  with reason   │      │                  │
   └────────────────┘      │                  │
                           │                  │
                           ▼                  ▼
                  ┌────────────────────────────────┐
                  │      Get staged changes        │
                  │      (git diff --cached)       │
                  └───────────────┬────────────────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │ Any changes to  │
                        │    commit?      │
                        └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    │ No                      │ Yes
                    ▼                         ▼
           ┌────────────────┐        ┌────────────────┐
           │  Raise Error   │        │   Run commit   │
           │  "Nothing to   │        │   command      │
           │   commit"      │        └───────┬────────┘
           └────────────────┘                │
                                             ▼
                                    ┌────────────────┐
                                    │ Parse commit   │
                                    │ output for     │
                                    │ new commit hash│
                                    └───────┬────────┘
                                            │
                                            ▼
                                    ┌────────────────┐
                                    │ Get commit     │
                                    │ details        │
                                    └───────┬────────┘
                                            │
                                            ▼
                                    ┌────────────────┐
                                    │   Return       │
                                    │   GitCommit    │
                                    └────────────────┘
```

---

## Notes

- All git operations use async subprocess execution
- Safety checks run before any potentially dangerous operation
- Repository state is detected lazily and cached
- Git commands use `--porcelain` format for reliable parsing
- Error handling distinguishes between git errors and system errors
- Branch operations verify merge status before deletion
