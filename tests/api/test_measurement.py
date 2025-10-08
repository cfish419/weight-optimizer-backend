import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import Mock, patch
import numpy as np
from src.api.routes.measurement import router
from src.services.computer_vision.baggage_measurement import BaggageMeasurementService

# Create a test FastAPI application
app = FastAPI()
app.include_router(router)

# Create a test client
client = TestClient(app)

@pytest.fixture
def mock_measurement_service():
    """
    Fixture to create a mock BaggageMeasurementService.
    """
    with patch('src.api.routes.measurement.BaggageMeasurementService') as mock:
        service = Mock(spec=BaggageMeasurementService)
        mock.return_value = service
        yield service

class TestMeasurementAPI:
    """
    Test suite for baggage measurement API endpoints.
    Tests request handling, file uploads, and response formatting.
    """

    async def test_measure_baggage_success(self, mock_measurement_service):
        """
        Test successful baggage measurement with valid image upload.
        """
        # Mock measurement service response
        mock_measurement_service.process_baggage_image.return_value = {
            'dimensions': (1.0, 0.8, 0.6),
            'volume': 0.48,
            'estimated_mass': 25.0,
            'confidence_score': 0.95,
            'image_url': '/storage/test-image.jpg'  # Using local storage path
        }
        # Skip actual image processing in tests
        mock_measurement_service._detect_reference_markers.return_value = [(1, np.array([[[0, 0], [100, 0], [100, 100], [0, 100]]]))]
        mock_measurement_service._preprocess_image.return_value = np.ones((100, 100), dtype=np.uint8) * 255
        
        # Create test image file
        test_image = b'fake image content'
        files = {'file': ('test.jpg', test_image, 'image/jpeg')}
        
        # Make request
        response = client.post(
            "/measure",
            files=files,
            params={'flight_id': 'test-flight-1'}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert 'measurements' in data
        assert 'recommendations' in data
        
        # Verify measurements
        measurements = data['measurements']
        assert len(measurements['dimensions']) == 3
        assert measurements['volume'] > 0
        assert measurements['estimated_mass'] > 0
        assert 0 <= measurements['confidence_score'] <= 1

    async def test_measure_baggage_invalid_file_type(self, mock_measurement_service):
        """
        Test handling of invalid file type upload.
        """
        # Create test text file
        test_file = b'not an image'
        files = {'file': ('test.txt', test_file, 'text/plain')}
        
        # Make request
        response = client.post("/measure", files=files)
        
        # Verify error response
        assert response.status_code == 400
        assert "File must be an image" in response.json()['detail']

    async def test_measure_baggage_processing_error(self, mock_measurement_service):
        """
        Test handling of image processing errors.
        """
        # Mock processing error
        mock_measurement_service.process_baggage_image.side_effect = \
            ValueError("Failed to process image")
        
        # Create test image file
        test_image = b'fake image content'
        files = {'file': ('test.jpg', test_image, 'image/jpeg')}
        
        # Make request
        response = client.post("/measure", files=files)
        
        # Verify error response
        assert response.status_code == 500
        assert "Failed to process image" in response.json()['detail']

    async def test_measure_baggage_low_confidence(self, mock_measurement_service):
        """
        Test handling of measurements with low confidence scores.
        """
        # Mock low confidence measurement
        mock_measurement_service.process_baggage_image.return_value = {
            'dimensions': (1.0, 0.8, 0.6),
            'volume': 0.48,
            'estimated_mass': 25.0,
            'confidence_score': 0.3,  # Low confidence
            'image_url': 'https://example.com/image.jpg'
        }
        
        # Create test image file
        test_image = b'fake image content'
        files = {'file': ('test.jpg', test_image, 'image/jpeg')}
        
        # Make request
        response = client.post("/measure", files=files)
        
        # Verify response includes warning
        assert response.status_code == 200
        data = response.json()
        recommendations = data['recommendations']
        assert any('confidence' in warning.lower() 
                  for warning in recommendations['warnings'])

    def test_generate_recommendations(self):
        """
        Test recommendation generation based on measurement results.
        """
        from src.api.routes.measurement import _generate_recommendations
        
        # Test case 1: Heavy baggage
        result = {
            'estimated_mass': 35.0,
            'dimensions': (1.0, 1.0, 1.0),
            'volume': 1.0,
            'confidence_score': 0.9
        }
        
        recommendations = _generate_recommendations(result)
        assert 'warnings' in recommendations
        assert 'handling_instructions' in recommendations
        assert any('weight limit' in warning.lower() 
                  for warning in recommendations['warnings'])
        assert any('mechanical assistance' in instruction.lower() 
                  for instruction in recommendations['handling_instructions'])
        
        # Test case 2: Large volume
        result = {
            'estimated_mass': 20.0,
            'dimensions': (2.5, 1.0, 1.0),
            'volume': 2.5,
            'confidence_score': 0.9
        }
        
        recommendations = _generate_recommendations(result)
        assert any('dimension limit' in warning.lower() 
                  for warning in recommendations['warnings'])
        assert any('early loading' in instruction.lower() 
                  for instruction in recommendations['handling_instructions'])