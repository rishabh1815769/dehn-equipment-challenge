from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy import select, insert, update, delete
from sqlalchemy.exc import IntegrityError
from .db import SessionLocal
from .models import Solution, Module, SolutionPart, SolutionModule
from .sync_neo4j import upsert_solutions, upsert_modules, upsert_has_part, sync_effective_bom


app = FastAPI(title="DEHN Solutions API", version="0.1.0")


class SolutionIn(BaseModel):
    id: int
    name: str
    type: str = Field(regex="^(Hauptprozess|Teilprozess)$")
    merkmalsklasse_1: Optional[str] = None
    merkmalsklasse_2: Optional[str] = None
    merkmalsklasse_3: Optional[str] = None
    randbedingung_1: Optional[str] = None
    randbedingung_2: Optional[str] = None
    verknuepfungen_prozessebene: Optional[str] = None
    verknuepfungen_baukastenebene: Optional[str] = None
    hinweise: Optional[str] = None
    ablageort_konstruktiv: Optional[str] = None
    ablageort_steuerungstechnisch: Optional[str] = None
    ablageort_prueftechnisch: Optional[str] = None
    ablageort_robotertechnisch: Optional[str] = None


class ModuleIn(BaseModel):
    id: int
    name: str
    version: Optional[str] = None
    bauteilkategorie: Optional[str] = None
    hersteller: Optional[str] = None
    typ: Optional[str] = None


class PartLinkIn(BaseModel):
    parent_solution_id: int
    child_solution_id: int
    qty: Optional[int] = 1


class BomLinkIn(BaseModel):
    solution_id: int
    module_id: int
    qty: Optional[int] = 1
    role: Optional[str] = None


@app.post("/solutions", status_code=201)
def create_solution(payload: SolutionIn):
    with SessionLocal() as db:
        try:
            db.execute(
                insert(Solution).values(**payload.model_dump())
            )
            db.commit()
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e.orig))
    # sync to Neo4j
    upsert_solutions([(payload.id, payload.name, payload.type)])
    return {"ok": True}


@app.get("/solutions/{sid}")
def get_solution(sid: int):
    with SessionLocal() as db:
        row = db.execute(select(Solution).where(Solution.id == sid)).scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Solution not found")
        return {
            k: getattr(row, k)
            for k in [
                "id",
                "name",
                "type",
                "merkmalsklasse_1",
                "merkmalsklasse_2",
                "merkmalsklasse_3",
                "randbedingung_1",
                "randbedingung_2",
            ]
        }


@app.get("/solutions")
def list_solutions(limit: int = 100, offset: int = 0):
    with SessionLocal() as db:
        rows = db.execute(select(Solution).offset(offset).limit(limit)).scalars().all()
        return [{"id": r.id, "name": r.name, "type": r.type} for r in rows]


@app.patch("/solutions/{sid}")
def update_solution(sid: int, payload: SolutionIn):
    with SessionLocal() as db:
        res = db.execute(update(Solution).where(Solution.id == sid).values(**payload.model_dump()))
        if res.rowcount == 0:
            raise HTTPException(status_code=404, detail="Solution not found")
        db.commit()
    upsert_solutions([(payload.id, payload.name, payload.type)])
    return {"ok": True}


@app.post("/modules", status_code=201)
def create_module(payload: ModuleIn):
    with SessionLocal() as db:
        try:
            db.execute(insert(Module).values(**payload.model_dump()))
            db.commit()
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e.orig))
    upsert_modules([(payload.id, payload.name, payload.typ or "", payload.hersteller or "")])
    return {"ok": True}


@app.get("/modules/{mid}")
def get_module(mid: int):
    with SessionLocal() as db:
        row = db.execute(select(Module).where(Module.id == mid)).scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Module not found")
        return {"id": row.id, "name": row.name, "typ": row.typ, "hersteller": row.hersteller}


@app.get("/modules")
def list_modules(limit: int = 100, offset: int = 0):
    with SessionLocal() as db:
        rows = db.execute(select(Module).offset(offset).limit(limit)).scalars().all()
        return [{"id": r.id, "name": r.name, "typ": r.typ} for r in rows]


@app.put("/solutions/{sid}/parts")
def upsert_parts(sid: int, links: List[PartLinkIn]):
    rows = [(l.parent_solution_id, l.child_solution_id, l.qty or 1) for l in links]
    with SessionLocal() as db:
        for p, c, q in rows:
            db.execute(
                insert(SolutionPart)
                .values(parent_solution_id=p, child_solution_id=c, qty=q)
                .on_conflict_do_update(index_elements=[SolutionPart.parent_solution_id, SolutionPart.child_solution_id], set_={"qty": q})
            )
        db.commit()
    upsert_has_part(rows)
    return {"ok": True}


@app.put("/solutions/{sid}/modules")
def upsert_bom(sid: int, links: List[BomLinkIn]):
    rows = [(l.solution_id, l.module_id, l.qty or 1, l.role or None) for l in links]
    with SessionLocal() as db:
        for s, m, q, r in rows:
            db.execute(
                insert(SolutionModule)
                .values(solution_id=s, module_id=m, qty=q, role=r)
                .on_conflict_do_update(index_elements=[SolutionModule.solution_id, SolutionModule.module_id, SolutionModule.role], set_={"qty": q, "role": r})
            )
        db.commit()
        # compute effective BOM rows for these solution_ids using the SQL view
        sids = list({s for s, *_ in rows})
        eff = []
        for s in sids:
            result = db.execute(
                select(
                    SolutionModule.solution_id,
                    SolutionModule.module_id,
                    SolutionModule.qty,
                    SolutionModule.role,
                ).select_from(SolutionModule)
                .where(SolutionModule.solution_id == s)
            ).all()
            eff.extend(result)
    for s, m, q, r in eff:
        sync_effective_bom(s, [(s, m, q, r)])
    return {"ok": True}


@app.delete("/solutions/{sid}")
def delete_solution(sid: int, hard: bool = False):
    with SessionLocal() as db:
        if hard:
            db.execute(delete(Solution).where(Solution.id == sid))
        else:
            db.execute(update(Solution).where(Solution.id == sid).values(deleted_at=func.now()))
        db.commit()
    return {"ok": True}


@app.delete("/modules/{mid}")
def delete_module(mid: int, hard: bool = False):
    with SessionLocal() as db:
        if hard:
            db.execute(delete(Module).where(Module.id == mid))
        else:
            db.execute(update(Module).where(Module.id == mid).values(deleted_at=func.now()))
        db.commit()
    return {"ok": True}


@app.delete("/solutions/{sid}/parts/{child_id}")
def delete_part(sid: int, child_id: int):
    with SessionLocal() as db:
        db.execute(
            delete(SolutionPart)
            .where(SolutionPart.parent_solution_id == sid)
            .where(SolutionPart.child_solution_id == child_id)
        )
        db.commit()
    # Graph detach for HAS_PART could be added here with a follow-up sync
    return {"ok": True}


@app.delete("/solutions/{sid}/modules/{mid}")
def delete_bom(sid: int, mid: int, role: Optional[str] = None):
    with SessionLocal() as db:
        stmt = (
            delete(SolutionModule)
            .where(SolutionModule.solution_id == sid)
            .where(SolutionModule.module_id == mid)
        )
        if role is not None:
            stmt = stmt.where(SolutionModule.role == role)
        db.execute(stmt)
        db.commit()
    # A subsequent effective sync will remove the edge in Neo4j
    return {"ok": True}


