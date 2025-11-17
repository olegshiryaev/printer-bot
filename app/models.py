from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional

class PrinterCartridgeLink(SQLModel, table=True):
    printer_id: Optional[int] = Field(default=None, foreign_key="printer.id", primary_key=True)
    cartridge_id: Optional[int] = Field(default=None, foreign_key="cartridge.id", primary_key=True)

class Printer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    cartridges: List["Cartridge"] = Relationship(back_populates="printers", link_model=PrinterCartridgeLink)

class Cartridge(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    printers: List[Printer] = Relationship(back_populates="cartridges", link_model=PrinterCartridgeLink)