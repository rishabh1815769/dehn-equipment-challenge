from sqlalchemy import BigInteger, Column, Integer, Text, TIMESTAMP, CheckConstraint, ForeignKey, Index
from sqlalchemy.sql import func
from .db import Base


class Solution(Base):
    __tablename__ = "solutions"

    id = Column(BigInteger, primary_key=True)
    name = Column(Text, nullable=False)
    type = Column(Text, nullable=False)  # 'Hauptprozess' | 'Teilprozess'

    merkmalsklasse_1 = Column(Text)
    merkmalsklasse_2 = Column(Text)
    merkmalsklasse_3 = Column(Text)

    randbedingung_1 = Column(Text)
    randbedingung_2 = Column(Text)
    verknuepfungen_prozessebene = Column(Text)
    verknuepfungen_baukastenebene = Column(Text)
    hinweise = Column(Text)
    ablageort_konstruktiv = Column(Text)
    ablageort_steuerungstechnisch = Column(Text)
    ablageort_prueftechnisch = Column(Text)
    ablageort_robotertechnisch = Column(Text)

    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True))

    __table_args__ = (
        Index("idx_solutions_type", "type"),
        CheckConstraint("type IN ('Hauptprozess','Teilprozess')", name="solutions_type_check"),
    )


class Module(Base):
    __tablename__ = "modules"

    id = Column(BigInteger, primary_key=True)
    name = Column(Text, nullable=False)
    version = Column(Text)
    bauteilkategorie = Column(Text)
    hersteller = Column(Text)
    typ = Column(Text)
    eigenschaft_1 = Column(Text)
    wert_1 = Column(Text)
    eigenschaft_2 = Column(Text)
    wert_2 = Column(Text)
    eigenschaft_3 = Column(Text)
    wert_3 = Column(Text)
    ablageort_konstruktiv = Column(Text)
    ablageort_steuerungstechnisch = Column(Text)
    ablageort_prueftechnisch = Column(Text)
    ablageort_robotertechnisch = Column(Text)
    sonstiges = Column(Text)
    spalte1 = Column(Text)

    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True))


class SolutionPart(Base):
    __tablename__ = "solution_parts"

    parent_solution_id = Column(BigInteger, ForeignKey("solutions.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    child_solution_id = Column(BigInteger, ForeignKey("solutions.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    qty = Column(Integer, nullable=False, server_default="1")
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True))


class SolutionModule(Base):
    __tablename__ = "solution_modules"

    solution_id = Column(BigInteger, ForeignKey("solutions.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    module_id = Column(BigInteger, ForeignKey("modules.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    role = Column(Text, primary_key=True)
    qty = Column(Integer, nullable=False, server_default="1")
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True))

    __table_args__ = (
        Index("idx_solution_modules_module", "module_id"),
        CheckConstraint("qty > 0", name="solution_modules_qty_pos"),
    )


