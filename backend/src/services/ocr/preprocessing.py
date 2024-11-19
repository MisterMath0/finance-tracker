# backend/src/services/ocr/preprocessing.py
import cv2
import numpy as np
from typing import Tuple

class ImagePreprocessor:
    @staticmethod
    def preprocess_receipt(image: np.ndarray) -> np.ndarray:
        """Preprocess receipt image for better OCR results."""
        # Convert to grayscale if the image is in color
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Apply edge preservation and noise reduction
        smooth = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            smooth, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh)
        
        # Optional: Deskew the image if it's tilted
        angle = ImagePreprocessor._get_skew_angle(denoised)
        if abs(angle) > 0.5:  # Only rotate if the angle is significant
            (h, w) = denoised.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            denoised = cv2.warpAffine(denoised, M, (w, h),
                                    flags=cv2.INTER_CUBIC,
                                    borderMode=cv2.BORDER_REPLICATE)
        
        return denoised
    
    @staticmethod
    def _get_skew_angle(image: np.ndarray) -> float:
        """Compute skew angle of text in image."""
        # Detect edges
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        
        # Detect lines using Hough transform
        lines = cv2.HoughLines(edges, 1, np.pi/180, 100)
        
        if lines is not None:
            angles = []
            for rho, theta in lines[:, 0]:
                angle = np.degrees(theta) - 90
                # Only consider angles between -45 and 45 degrees
                if -45 < angle < 45:
                    angles.append(angle)
            
            if angles:
                # Return the median angle
                return np.median(angles)
        
        return 0.0
    
    @staticmethod
    def resize_image(image: np.ndarray, target_width: int = 800) -> np.ndarray:
        """Resize image while maintaining aspect ratio."""
        # Check if resizing is needed
        if image.shape[1] <= target_width:
            return image
            
        aspect_ratio = image.shape[1] / image.shape[0]
        target_height = int(target_width / aspect_ratio)
        
        # Use INTER_AREA for shrinking, INTER_CUBIC for enlarging
        interpolation = cv2.INTER_AREA if image.shape[1] > target_width else cv2.INTER_CUBIC
        
        return cv2.resize(image, (target_width, target_height), 
                         interpolation=interpolation)