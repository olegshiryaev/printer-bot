from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models import Printer, Cartridge
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/api")

class PrinterOut(BaseModel):
    id: int
    name: str
    cartridges: List[str] = []

class CartridgeOut(BaseModel):
    id: int
    name: str
    printers: List[str] = []

@router.get("/printers", response_model=List[PrinterOut])
async def search_printers(
    q: str = Query(..., min_length=2),
    page: int = 1,
    limit: int = 10,
    session: AsyncSession = Depends(get_session)
):
    offset = (page - 1) * limit
    stmt = select(Printer).options(selectinload(Printer.cartridges)) \
        .where(Printer.name.ilike(f"%{q}%")) \
        .offset(offset).limit(limit)
    result = await session.execute(stmt)
    printers = result.scalars().all()
    
    return [
        PrinterOut(id=p.id, name=p.name, cartridges=[c.name for c in p.cartridges])
        for p in printers
    ]

@router.get("/cartridges", response_model=List[CartridgeOut])
async def search_cartridges(
    q: str = Query(..., min_length=2),
    page: int = 1,
    limit: int = 10,
    session: AsyncSession = Depends(get_session)
):
    offset = (page - 1) * limit
    stmt = select(Cartridge).options(selectinload(Cartridge.printers)) \
        .where(Cartridge.name.ilike(f"%{q}%")) \
        .offset(offset).limit(limit)
    result = await session.execute(stmt)
    cartridges = result.scalars().all()
    
    return [
        CartridgeOut(id=c.id, name=c.name, printers=[p.name for p in c.printers])
        for c in cartridges
    ]

@router.get("/printer/{printer_id}", response_model=PrinterOut)
async def get_printer(printer_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Printer).options(selectinload(Printer.cartridges)).where(Printer.id == printer_id)
    )
    printer = result.scalars().first()
    if not printer:
        raise HTTPException(404, "Printer not found")
    return PrinterOut(id=printer.id, name=printer.name, cartridges=[c.name for c in printer.cartridges])

@router.get("/cartridge/{cartridge_id}", response_model=CartridgeOut)
async def get_cartridge(cartridge_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Cartridge).options(selectinload(Cartridge.printers)).where(Cartridge.id == cartridge_id)
    )
    cartridge = result.scalars().first()
    if not cartridge:
        raise HTTPException(404, "Cartridge not found")
    return CartridgeOut(id=cartridge.id, name=cartridge.name, printers=[p.name for p in cartridge.printers])