from enum import IntEnum


class ReportStatus(IntEnum):
    """Lifecycle of a report."""

    PENDING = 0      # created, not analysed yet
    PROCESSING = 1   # AI call in progress
    COMPLETED = 2    # summary saved
    FAILED = 3       # AI call failed, see Report.error


class ScaffoldStatus(IntEnum):
    """Lifecycle of a project scaffold generation."""

    DRAFT = 0        # Scope saved, waiting for generation
    PROCESSING = 1   # AI generating specs and markdown files
    COMPLETED = 2    # All .md files and zip ready
    FAILED = 3       # Generation failed