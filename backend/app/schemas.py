from pydantic import BaseModel


class PublicStats(BaseModel):
    """Figures shown on the simplified dashboard (user story #3)."""

    experiments: int
    subjects: int
    institutions: int
