from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Replication(Base):
    """One replication (experiment) carried out by a participating institution."""

    __tablename__ = "replications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    institution: Mapped[str] = mapped_column(String(200))
    subjects: Mapped[int] = mapped_column(Integer, default=0)
