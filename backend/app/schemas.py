from pydantic import BaseModel, Field


class PublicStats(BaseModel):
    """Figures shown on the simplified dashboard (user story #3)."""

    experiments: int
    subjects: int
    institutions: int


class MeResponse(BaseModel):
    email: str
    role: str


class PaperOut(BaseModel):
    title: str
    authors: str
    venue: str
    year: int
    url: str


class DemoOut(BaseModel):
    title: str
    url: str


class ExperimentOut(BaseModel):
    """What an interested researcher can see: no code, no data, no repository locations."""

    title: str
    summary: str
    description: str
    papers: list[PaperOut]
    demos: list[DemoOut]


class JoinRequestIn(BaseModel):
    message: str = Field(default="", max_length=2000)


class JoinRequestOut(BaseModel):
    id: int
    email: str
    message: str
    status: str
    decided_by: str | None = None


class DecisionIn(BaseModel):
    approve: bool
