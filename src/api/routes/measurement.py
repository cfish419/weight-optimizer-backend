from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
from src.db.database import get_db
from src.services.computer_vision.baggage_measurement import BaggageMeasurementService
from src.models.baggage import BaggageCreate
import tempfile
import os
from typing import Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
measurement_service = BaggageMeasurementService()

@router.post("/measure")
async def measure_baggage(
    file: UploadFile = File(...),
    flight_id: str = None,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Process an uploaded baggage image to measure dimensions and estimate mass.
    
    Args:
        file: Uploaded image file
        flight_id: Optional ID of the flight this baggage belongs to
        db: Database session
        
    Returns:
        Dict containing:
        - dimensions: (length, width, height) in meters
        - volume: in cubic meters
        - estimated_mass: in kg
        - confidence_score: measurement confidence (0-1)
        - image_url: URL of stored image
    
    Raises:
        HTTPException: If image processing fails or file format is invalid
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write uploaded file to temporary file
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()
            
            try:
                # Process the image
                result = await measurement_service.process_baggage_image(temp_file.name)
                
                # If confidence is too low, warn but don't fail
                if result['confidence_score'] < 0.5:
                    logger.warning(
                        f"Low confidence measurement ({result['confidence_score']:.2f}). "
                        "Consider retaking the image with better lighting and clear reference markers."
                    )
                
                # If flight_id is provided, create baggage record
                if flight_id:
                    baggage = BaggageCreate(
                        flight_id=flight_id,
                        mass=result['estimated_mass'],
                        volume=result['volume'],
                        image_url=result['image_url']
                    )
                    # Note: Actual baggage creation would be handled by baggage_service
                    
                return {
                    "message": "Baggage measured successfully",
                    "measurements": result,
                    "recommendations": _generate_recommendations(result)
                }
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file.name)
                
    except Exception as e:
        logger.error(f"Error processing baggage image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process image: {str(e)}"
        )

def _generate_recommendations(result: Dict) -> Dict:
    """
    Generate handling recommendations based on measurement results.
    
    Args:
        result: Measurement results dictionary
        
    Returns:
        Dict containing handling recommendations and warnings
    """
    recommendations = {
        "handling_instructions": [],
        "warnings": []
    }
    
    # Check mass
    if result['estimated_mass'] > 32:  # Standard airline limit
        recommendations["warnings"].append(
            "Baggage exceeds standard weight limit of 32kg"
        )
    
    # Check dimensions
    dimensions = result['dimensions']
    if max(dimensions) > 2.0:  # Example size limit
        recommendations["warnings"].append(
            "Baggage exceeds maximum dimension limit"
        )
    
    # Add handling instructions based on measurements
    if result['estimated_mass'] > 25:
        recommendations["handling_instructions"].append(
            "Heavy item - Use mechanical assistance for loading"
        )
    
    if result['volume'] > 0.5:  # 0.5 cubic meters
        recommendations["handling_instructions"].append(
            "Large item - Consider early loading sequence"
        )
    
    # Add confidence-based recommendations
    if result['confidence_score'] < 0.7:
        recommendations["warnings"].append(
            "Measurement confidence is low - Consider manual verification"
        )
    
    return recommendations