"""
Mode modules.

define data structure.
"""
import dataclasses
import os


@dataclasses.dataclass
class TogglReportDetail:

    """Toggl report detail model."""

    id: int = ''
    pid: int = ''
    tid: int = ''
    uid: int = ''
    user: str = ''
    description: str = ''
    start: str = ''
    end: str = ''
    updated: str = ''
    dur: int = ''
    backlog_issue_key: str = ''


@dataclasses.dataclass
class TogglReportSummary:

    """Toggl report summary model."""

    backlog_issue_key: str = ''
    sum_dur: int = None
    sum_dur_hours: float = None


@dataclasses.dataclass
class BacklogIssue:

    """Backlog issue model.
        comments[n]['content']  # コメント文
        comments[n]['changeLog']  # 変更内容
        comments[n]['changeLog']['field']  # 変更項目
        comments[n]['changeLog']['originalValue']  # 変更前の値
        comments[n]['changeLog']['newValue']  # 変更後の値
    """

    issue_key: str = ''
    actual_hours: float = None
    manual_actual_hours: float = 0.0 
    comments: list = None
