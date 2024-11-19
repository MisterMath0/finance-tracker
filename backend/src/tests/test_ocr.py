# backend/src/tests/test_ocr.py
import sys
import os
import cv2
import pytest
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ocr.service import OCRService
from services.ocr.preprocessing import ImagePreprocessor
from services.ocr.extractor import Receipt

class TestOCRService:
    @pytest.fixture
    def ocr_service(self):
        return OCRService()

    @pytest.fixture
    def sample_receipt_path(self):
        # Create tests/samples directory if it doesn't exist
        samples_dir = Path(__file__).parent / "samples"
        samples_dir.mkdir(exist_ok=True)
        return samples_dir / "sample_receipt.jpg"

    async def test_receipt_processing(self, ocr_service, sample_receipt_path):
        # Load image
        image = cv2.imread(str(sample_receipt_path))
        assert image is not None, "Failed to load test image"

        # Process receipt
        result = await ocr_service.process_receipt(image)
        
        # Basic assertions
        assert isinstance(result, Receipt)
        assert result.store_name != "Unknown Store"
        assert result.total > 0
        assert len(result.items) > 0