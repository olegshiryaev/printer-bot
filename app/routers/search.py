from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel

from app.database import get_session
from app.models import Printer, Cartridge


router = APIRouter(prefix="/api")


# ---------- Pydantic ----------
class PrinterOut(BaseModel):
    id: int
    name: str
    cartridges: List[str]


class CartridgeOut(BaseModel):
    id: int
    name: str
    printers: List[str]


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    limit: int


# ---------- HELPERS ----------
async def paginate(query, session: AsyncSession, page: int, limit: int):
    offset = (page - 1) * limit

    # total count
    total_stmt = select(func.count()).select_from(query.subquery())
    total = (await session.execute(total_stmt)).scalar()

    # data
    stmt = query.offset(offset).limit(limit)
    result = await session.execute(stmt)
    items = result.scalars().all()

    return items, total


# ---------- ROUTES ----------
@router.get("/printers", response_model=PaginatedResponse)
async def search_printers(
    q: str = Query(..., min_length=2),
    page: int = 1,
    limit: int = 10,
    session: AsyncSession = Depends(get_session)
):
    query = (
        select(Printer)
        .options(selectinload(Printer.cartridges))
        .where(Printer.name.ilike(f"%{q}%"))
    )

    printers, total = await paginate(query, session, page, limit)

    items = [
        PrinterOut(
            id=p.id,
            name=p.name,
            cartridges=[c.name for c in p.cartridges],
        )
        for p in printers
    ]

    return PaginatedResponse(items=items, total=total, page=page, limit=limit)


@router.get("/cartridges", response_model=PaginatedResponse)
async def search_cartridges(
    q: str = Query(..., min_length=2),
    page: int = 1,
    limit: int = 10,
    session: AsyncSession = Depends(get_session)
):
    query = (
        select(Cartridge)
        .options(selectinload(Cartridge.printers))
        .where(Cartridge.name.ilike(f"%{q}%"))
    )

    cartridges, total = await paginate(query, session, page, limit)

    items = [
        CartridgeOut(
            id=c.id,
            name=c.name,
            printers=[p.name for p in c.printers],
        )
        for c in cartridges
    ]

    return PaginatedResponse(items=items, total=total, page=page, limit=limit)


@router.get("/printer/{printer_id}", response_model=PrinterOut)
async def get_printer(printer_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Printer)
        .options(selectinload(Printer.cartridges))
        .where(Printer.id == printer_id)
    )
    printer = result.scalars().first()

    if not printer:
        raise HTTPException(404, "Printer not found")

    return PrinterOut(
        id=printer.id,
        name=printer.name,
        cartridges=[c.name for c in printer.cartridges],
    )


@router.get("/cartridge/{cartridge_id}", response_model=CartridgeOut)
async def get_cartridge(cartridge_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Cartridge)
        .options(selectinload(Cartridge.printers))
        .where(Cartridge.id == cartridge_id)
    )
    cartridge = result.scalars().first()

    if not cartridge:
        raise HTTPException(404, "Cartridge not found")

    return CartridgeOut(
        id=cartridge.id,
        name=cartridge.name,
        printers=[p.name for p in cartridge.printers],
    )
