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


class ExperimentDetails(Base):
    """Descriptive content about the experiment, shown to interested researchers (#1).

    There is a single row. It holds no code or data of the replications.
    """

    __tablename__ = "experiment_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(String(5000))


class Paper(Base):
    """A paper derived from the project."""

    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    authors: Mapped[str] = mapped_column(String(300))
    venue: Mapped[str] = mapped_column(String(200))
    year: Mapped[int] = mapped_column(Integer)
    url: Mapped[str] = mapped_column(String(500))


class Demo(Base):
    """A promotional demo of the experiment."""

    __tablename__ = "demos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(500))
