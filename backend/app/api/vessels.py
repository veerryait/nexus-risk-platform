"""
Vessels API Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Vessel, VesselPosition
from app.schemas.vessel import VesselResponse, VesselCreate, VesselPositionResponse

router = APIRouter()


@router.get("/", response_model=List[VesselResponse])
async def get_vessels(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    carrier: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get list of tracked vessels from database"""
    query = db.query(Vessel)
    
    if carrier:
        query = query.filter(Vessel.carrier.ilike(f"%{carrier}%"))
    
    vessels = query.offset(skip).limit(limit).all()
    return vessels


@router.get("/{vessel_id}", response_model=VesselResponse)
async def get_vessel(vessel_id: int, db: Session = Depends(get_db)):
    """Get vessel by ID"""
    vessel = db.query(Vessel).filter(Vessel.id == vessel_id).first()
    if not vessel:
        raise HTTPException(status_code=404, detail="Vessel not found")
    return vessel


@router.get("/{vessel_id}/positions", response_model=List[VesselPositionResponse])
async def get_vessel_positions(
    vessel_id: int,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get recent positions for a vessel"""
    # Verify vessel exists
    vessel = db.query(Vessel).filter(Vessel.id == vessel_id).first()
    if not vessel:
        raise HTTPException(status_code=404, detail="Vessel not found")
    
    positions = db.query(VesselPosition)\
        .filter(VesselPosition.vessel_id == vessel_id)\
        .order_by(VesselPosition.timestamp.desc())\
        .limit(limit)\
        .all()
    return positions


@router.get("/carrier/{carrier_name}", response_model=List[VesselResponse])
async def get_vessels_by_carrier(carrier_name: str, db: Session = Depends(get_db)):
    """Get all vessels by carrier name"""
    vessels = db.query(Vessel).filter(Vessel.carrier.ilike(f"%{carrier_name}%")).all()
    return vessels
