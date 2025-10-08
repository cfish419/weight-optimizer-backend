import cv2
import numpy as np
from typing import Dict, Tuple, Optional
import logging
from pathlib import Path
import os
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)

class BaggageMeasurementService:
    """
    Service for processing baggage images to extract measurements and estimate mass.
    
    This service can operate in two modes:
    1. Cloud mode: Uses AWS S3 for image storage
    2. Local mode: Stores images in a local directory
    
    The service automatically falls back to local storage if AWS credentials are not configured.
    """

    def __init__(self, calibration_data_path: Optional[str] = None):
        """
        Initialize the baggage measurement service.
        
        Args:
            calibration_data_path: Path to camera calibration data (optional)
                                 Used for accurate measurements in real-world units
        """
        self.reference_marker_size = 0.1  # Size of reference marker in meters
        self.density_calibration = 1000    # Default density calibration (kg/m³)
        
        # Try to initialize AWS S3 client
        self.s3_client = None
        self.s3_bucket = 'ibl-baggage-images'
        self.use_local_storage = True
        
        try:
            if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
                import boto3
                self.s3_client = boto3.client('s3')
                self.use_local_storage = False
                logger.info("AWS S3 client initialized successfully")
            else:
                logger.info("AWS credentials not found, using local storage")
        except Exception as e:
            logger.warning(f"Failed to initialize AWS S3 client: {str(e)}")
            logger.info("Falling back to local storage")
        
        # Create local storage directory if needed
        if self.use_local_storage:
            self.local_storage_path = Path('storage/baggage_images')
            self.local_storage_path.mkdir(parents=True, exist_ok=True)
        
        if calibration_data_path:
            self._load_calibration_data(calibration_data_path)

    async def process_baggage_image(self, image_path: str) -> Dict:
        """
        Process a baggage image to extract measurements and estimate mass.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict containing:
            - dimensions (length, width, height in meters)
            - volume (in cubic meters)
            - estimated_mass (in kg)
            - confidence_score (0-1)
            - image_url (S3 URL of stored image)
        """
        try:
            # Read and preprocess the image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Failed to load image from {image_path}")
            
            # Preprocess image
            preprocessed = self._preprocess_image(image)
            
            # Detect reference markers
            markers = self._detect_reference_markers(preprocessed)
            if not markers:
                raise ValueError("No reference markers detected in image")
            
            # Calculate scale factor using reference markers
            scale_factor = self._calculate_scale_factor(markers)
            
            # Detect baggage contours
            contours = self._detect_baggage(preprocessed)
            
            # Calculate dimensions
            dimensions = self._calculate_dimensions(contours, scale_factor)
            
            # Estimate volume and mass
            volume = self._calculate_volume(dimensions)
            estimated_mass = self._estimate_mass(volume)
            
            # Calculate confidence score based on detection quality
            confidence = self._calculate_confidence(contours, markers)
            
            # Store image in S3
            image_url = await self._store_image(image_path)
            
            return {
                "dimensions": dimensions,
                "volume": volume,
                "estimated_mass": estimated_mass,
                "confidence_score": confidence,
                "image_url": image_url
            }
            
        except Exception as e:
            logger.error(f"Error processing baggage image: {str(e)}")
            raise

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess the image for better feature detection.
        
        Steps:
        1. Convert to grayscale
        2. Apply Gaussian blur to reduce noise
        3. Apply adaptive thresholding
        4. Perform morphological operations
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Perform morphological operations
        kernel = np.ones((3,3), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return processed

    def _detect_reference_markers(self, image: np.ndarray) -> list:
        """
        Detect reference markers in the image using ArUco markers.
        
        ArUco markers are specialized fiducial markers that provide:
        - Unique identification
        - High detection accuracy
        - Rotation and perspective information
        
        Returns:
            List of tuples (marker_id, corner_points)
            corner_points is a numpy array of 4 points defining the marker corners
        """
        # Create ArUco dictionary and detector (updated for OpenCV 4.8+)
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        aruco_params = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
        
        # Detect markers in the image
        corners, ids, rejected = detector.detectMarkers(image)
        
        # If markers are found, return them with their IDs
        if ids is not None:
            return [(id_[0], corner) for id_, corner in zip(ids, corners)]
        return []

    def _calculate_scale_factor(self, markers: list) -> float:
        """
        Calculate the scale factor using detected reference markers.
        
        The scale factor converts pixel measurements to real-world units (meters)
        based on the known size of reference markers.
        """
        if not markers:
            return 1.0
            
        # Calculate average marker size in pixels
        marker_sizes = []
        for _, corner in markers:
            size = np.linalg.norm(corner[0][0] - corner[0][1])  # Use marker width
            marker_sizes.append(size)
        
        avg_marker_size = np.mean(marker_sizes)
        
        # Calculate scale factor (meters per pixel)
        return self.reference_marker_size / avg_marker_size

    def _detect_baggage(self, image: np.ndarray) -> list:
        """
        Detect baggage contours in the preprocessed image.
        
        Uses contour detection with filtering to identify baggage boundaries.
        Returns the largest contour that meets certain criteria.
        """
        # Find contours
        contours, _ = cv2.findContours(
            image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Filter contours based on area and shape
        valid_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 1000:  # Minimum area threshold
                continue
                
            # Check if contour is roughly rectangular
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
            if len(approx) < 4 or len(approx) > 6:
                continue
                
            valid_contours.append(contour)
            
        return valid_contours

    def _calculate_dimensions(self, contours: list, scale_factor: float) -> Tuple[float, float, float]:
        """
        Calculate real-world dimensions of the baggage.
        
        Uses the minimum area rectangle approach to find length and width.
        Height is estimated using shadow analysis or secondary camera angle if available.
        """
        if not contours:
            raise ValueError("No valid contours found for dimension calculation")
            
        # Get the largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Find minimum area rectangle
        rect = cv2.minAreaRect(largest_contour)
        width, length = rect[1]
        
        # Convert to real-world units
        length = length * scale_factor
        width = width * scale_factor
        
        # Estimate height (simplified - assuming standard aspect ratio)
        # In a real implementation, this would use depth sensors or multiple camera angles
        height = min(length, width) * 0.75
        
        return (length, width, height)

    def _calculate_volume(self, dimensions: Tuple[float, float, float]) -> float:
        """
        Calculate volume based on measured dimensions.
        
        Args:
            dimensions: Tuple of (length, width, height) in meters
            
        Returns:
            Volume in cubic meters
        """
        length, width, height = dimensions
        return length * width * height

    def _estimate_mass(self, volume: float) -> float:
        """
        Estimate mass based on volume and calibrated density.
        
        This is a simplified estimation - in a real implementation,
        this would use machine learning models trained on historical data
        to provide more accurate estimates based on baggage appearance.
        """
        return volume * self.density_calibration

    def _calculate_confidence(self, contours: list, markers: list) -> float:
        """
        Calculate confidence score for the measurements.
        
        Considers factors such as:
        - Quality of marker detection
        - Clarity of baggage contours
        - Lighting conditions
        - Camera angle
        """
        score = 1.0
        
        # Reduce confidence if no markers detected
        if not markers:
            score *= 0.5
            
        # Reduce confidence if contour detection is poor
        if not contours:
            score *= 0.5
        
        # Add more sophisticated confidence calculations here
        
        return max(0.1, min(score, 1.0))  # Ensure score is between 0.1 and 1.0

    async def _store_image(self, image_path: str) -> str:
        """
        Store the processed image either in S3 or locally.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            URL or path to the stored image
        """
        try:
            file_name = Path(image_path).name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_filename = f"{timestamp}_{file_name}"
            
            if not self.use_local_storage and self.s3_client:
                # Store in S3
                s3_key = f"baggage-images/{new_filename}"
                self.s3_client.upload_file(image_path, self.s3_bucket, s3_key)
                return f"https://{self.s3_bucket}.s3.amazonaws.com/{s3_key}"
            else:
                # Store locally
                destination = self.local_storage_path / new_filename
                shutil.copy2(image_path, destination)
                return str(destination.absolute())
            
        except Exception as e:
            logger.error(f"Error storing image: {str(e)}")
            raise

    def _load_calibration_data(self, calibration_path: str):
        """
        Load camera calibration data for accurate measurements.
        
        This would include:
        - Camera matrix
        - Distortion coefficients
        - Density calibration data
        """
        try:
            # Load calibration data
            # This is a placeholder - implement actual calibration loading
            logger.info(f"Loading calibration data from {calibration_path}")
            
        except Exception as e:
            logger.warning(f"Failed to load calibration data: {str(e)}")
            logger.warning("Using default calibration values")