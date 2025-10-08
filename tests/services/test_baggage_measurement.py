import pytest
import numpy as np
import cv2
from unittest.mock import Mock, patch
from src.services.computer_vision.baggage_measurement import BaggageMeasurementService

@pytest.fixture
def measurement_service():
    """
    Fixture to create a BaggageMeasurementService instance for testing.
    Mocks AWS S3 client to avoid actual cloud interactions.
    """
    with patch('boto3.client') as mock_s3:
        service = BaggageMeasurementService()
        service.s3_client = mock_s3
        yield service

@pytest.fixture
def sample_image():
    """
    Create a sample test image with known dimensions and markers.
    """
    # Create a 1000x1000 black image
    image = np.zeros((1000, 1000, 3), dtype=np.uint8)
    
    # Draw a white rectangle (simulated baggage)
    cv2.rectangle(image, (300, 300), (700, 700), (255, 255, 255), -1)
    
    # Save temporary image
    temp_path = "test_baggage.jpg"
    cv2.imwrite(temp_path, image)
    yield temp_path
    
    # Cleanup
    import os
    os.remove(temp_path)

class TestBaggageMeasurementService:
    """
    Test suite for BaggageMeasurementService.
    Tests image processing, measurement calculations, and error handling.
    """

    async def test_process_baggage_image_success(self, measurement_service, sample_image):
        """
        Test successful processing of a baggage image with valid markers.
        """
        # Configure mock S3 client
        measurement_service.s3_client.upload_file.return_value = None
        
        # Process test image
        result = await measurement_service.process_baggage_image(sample_image)
        
        # Verify result structure and values
        assert isinstance(result, dict)
        assert all(key in result for key in [
            'dimensions', 'volume', 'estimated_mass', 
            'confidence_score', 'image_url'
        ])
        
        # Verify measurements are reasonable
        length, width, height = result['dimensions']
        assert 0 < length < 3  # Normal baggage shouldn't exceed 3 meters
        assert 0 < width < 3
        assert 0 < height < 3
        
        # Verify volume calculation
        assert abs(result['volume'] - (length * width * height)) < 0.001
        
        # Verify mass estimation
        assert 0 < result['estimated_mass'] < 100  # Normal baggage range
        
        # Verify confidence score
        assert 0 <= result['confidence_score'] <= 1

    async def test_process_invalid_image_path(self, measurement_service):
        """
        Test handling of invalid image path.
        """
        with pytest.raises(ValueError) as exc_info:
            await measurement_service.process_baggage_image("nonexistent.jpg")
        assert "Failed to load image" in str(exc_info.value)

    def test_calculate_dimensions_no_contours(self, measurement_service):
        """
        Test handling of image with no detectable baggage contours.
        """
        with pytest.raises(ValueError) as exc_info:
            measurement_service._calculate_dimensions([], 1.0)
        assert "No valid contours found" in str(exc_info.value)

    def test_calculate_volume(self, measurement_service):
        """
        Test volume calculation with known dimensions.
        """
        dimensions = (2.0, 1.5, 1.0)  # 3m³
        volume = measurement_service._calculate_volume(dimensions)
        assert volume == pytest.approx(3.0)

    def test_estimate_mass(self, measurement_service):
        """
        Test mass estimation with known volume.
        """
        volume = 0.5  # 0.5m³
        mass = measurement_service._estimate_mass(volume)
        # With default density calibration (1000 kg/m³)
        assert mass == pytest.approx(500)  # 500kg

    def test_calculate_confidence_no_markers(self, measurement_service):
        """
        Test confidence calculation with missing reference markers.
        """
        confidence = measurement_service._calculate_confidence(
            contours=[Mock()],  # Some contours
            markers=[]  # No markers
        )
        assert confidence < 1.0  # Should be reduced due to missing markers
        assert confidence >= 0.1  # Should not go below minimum threshold

    @pytest.mark.parametrize("image_size,expected_scale", [
        ((100, 100), 0.001),  # Small image
        ((1000, 1000), 0.0001),  # Large image
    ])
    def test_calculate_scale_factor(self, measurement_service, image_size, expected_scale):
        """
        Test scale factor calculation with different image sizes.
        """
        # Create mock markers with known size
        mock_marker = np.array([[[0, 0], [100, 0], [100, 100], [0, 100]]])
        markers = [(1, mock_marker)]
        
        scale = measurement_service._calculate_scale_factor(markers)
        assert scale == pytest.approx(expected_scale, rel=0.1)

    async def test_image_storage(self, measurement_service, sample_image):
        """
        Test successful image storage in S3.
        """
        expected_url = f"https://{measurement_service.s3_bucket}.s3.amazonaws.com/baggage-images/test_baggage.jpg"
        measurement_service.s3_client.upload_file.return_value = None
        
        url = await measurement_service._store_image(sample_image)
        
        assert url == expected_url
        measurement_service.s3_client.upload_file.assert_called_once()

    def test_preprocess_image(self, measurement_service):
        """
        Test image preprocessing steps.
        """
        # Create test image
        image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        
        processed = measurement_service._preprocess_image(image)
        
        assert processed.shape == (100, 100)  # Should be grayscale
        assert processed.dtype == np.uint8
        assert 0 in processed and 255 in processed  # Should have both black and white pixels