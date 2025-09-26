"""
Detection Simulator for AlignPress v2

Simulates detection algorithms using static images for development and debugging
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import asdict

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: OpenCV/PIL not available. Detection simulator disabled.")

from ..config.models import Logo, Style, AlignPressConfig, Point, Rectangle
from ..controller.state_manager import DetectionResult
from ..services.detection_service import get_detection_service

logger = logging.getLogger(__name__)


class DetectionSimulator:
    """Simulates detection process using static images"""

    def __init__(self):
        if not CV2_AVAILABLE:
            raise ImportError("OpenCV/PIL dependencies not available")

        self.detection_service = get_detection_service()
        self.results_history: List[Dict[str, Any]] = []
        self.calibration_data: Optional[Dict] = None
        self.mm_per_pixel: float = 1.0

        # Detection algorithm parameters
        self.detection_params = {
            'contour': {
                'blur_kernel': (5, 5),
                'canny_lower': 50,
                'canny_upper': 150,
                'min_area': 100,
                'max_area': 50000,
                'aspect_ratio_range': (0.2, 5.0)
            },
            'template': {
                'match_methods': [cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR_NORMED],
                'threshold': 0.7,
                'scale_range': (0.8, 1.2),
                'scale_steps': 5
            },
            'aruco': {
                'dictionary': cv2.aruco.DICT_6X6_250,
                'detector_params': cv2.aruco.DetectorParameters()
            }
        }

        logger.info("DetectionSimulator initialized with real image processing")

    def load_calibration(self, calibration_path: Path) -> bool:
        """Load calibration data from JSON file"""
        try:
            import json
            with open(calibration_path, 'r', encoding='utf-8') as f:
                self.calibration_data = json.load(f)

            self.mm_per_pixel = self.calibration_data.get('factor_mm_px', 1.0)
            logger.info(f"Calibration loaded: {self.mm_per_pixel:.4f} mm/pixel")
            return True
        except Exception as e:
            logger.error(f"Error loading calibration: {e}")
            return False

    def simulate_garment_detection(
        self,
        image_path: Path,
        style: Style,
        config: AlignPressConfig,
        variant_id: Optional[str] = None,
        save_results: bool = True,
        calibration_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Simulate complete garment detection process

        Args:
            image_path: Path to test image
            style: Style configuration with logos
            config: Complete system configuration
            variant_id: Optional variant for size adjustments
            save_results: Whether to save results to history

        Returns:
            Complete detection results with metrics
        """
        logger.info(f"Simulating detection: {image_path}")

        # Load calibration if provided
        if calibration_path and calibration_path.exists():
            self.load_calibration(calibration_path)

        # Load image
        try:
            frame = cv2.imread(str(image_path))
            if frame is None:
                raise ValueError(f"Could not load image: {image_path}")
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            return self._create_error_result(str(e))

        # Pre-process image for better detection
        processed_frame = self._preprocess_image(frame)

        # Start timing
        start_time = time.time()

        # Simulate detection for each logo
        logo_results = []
        overall_success = True

        for logo in style.logos:
            logo_result = self._simulate_single_logo_detection(
                processed_frame, frame, logo, config, variant_id
            )
            logo_results.append(logo_result)

            if not logo_result.success:
                overall_success = False

        # Calculate total time
        total_time = time.time() - start_time

        # Create comprehensive result
        result = {
            'image_path': str(image_path),
            'style_id': style.id,
            'style_name': style.name,
            'variant_id': variant_id,
            'timestamp': time.time(),
            'processing_time_ms': total_time * 1000,
            'overall_success': overall_success,
            'logo_count': len(style.logos),
            'successful_logos': sum(1 for r in logo_results if r.success),
            'failed_logos': sum(1 for r in logo_results if not r.success),
            'average_confidence': np.mean([r.confidence for r in logo_results]),
            'logo_results': [asdict(result) for result in logo_results],
            'performance_metrics': self._calculate_performance_metrics(logo_results, total_time)
        }

        if save_results:
            self.results_history.append(result)

        logger.info(f"Detection completed: {len(logo_results)} logos, {overall_success}")
        return result

    def _preprocess_image(self, frame: np.ndarray) -> np.ndarray:
        """Pre-process image to improve detection accuracy"""
        # Apply denoising
        denoised = cv2.fastNlMeansDenoisingColored(frame, None, 10, 10, 7, 21)

        # Enhance contrast using CLAHE
        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_channel = clahe.apply(l_channel)

        enhanced = cv2.merge([l_channel, a_channel, b_channel])
        enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

        return enhanced_bgr

    def _simulate_single_logo_detection(
        self,
        processed_frame: np.ndarray,
        original_frame: np.ndarray,
        logo: Logo,
        config: AlignPressConfig,
        variant_id: Optional[str] = None
    ) -> DetectionResult:
        """
        Simulate detection for a single logo

        Args:
            frame: Input image
            logo: Logo configuration
            config: System configuration
            variant_id: Optional variant for adjustments

        Returns:
            Detection result for single logo
        """
        try:
            # Apply variant adjustments if specified
            adjusted_logo = self._apply_variant_adjustments(logo, config, variant_id)

            # Convert mm coordinates to pixel coordinates using calibration
            pixel_logo = self._convert_logo_to_pixels(adjusted_logo)

            # Perform real detection based on detector type
            result = self._perform_real_detection(processed_frame, original_frame, pixel_logo, config)

            # Add simulation-specific enhancements
            result = self._enhance_simulation_result(result, original_frame, adjusted_logo)

            return result

        except Exception as e:
            logger.error(f"Error detecting logo {logo.id}: {e}")
            return DetectionResult(
                logo_id=logo.id,
                success=False,
                position=(0.0, 0.0),
                angle=0.0,
                confidence=0.0,
                error_mm=999.0,
                error_deg=999.0,
                timestamp=time.time()
            )

    def _apply_variant_adjustments(
        self,
        logo: Logo,
        config: AlignPressConfig,
        variant_id: Optional[str]
    ) -> Logo:
        """Apply variant-specific adjustments to logo position and size"""
        if not variant_id:
            return logo

        # Find variant configuration
        variant = None
        for v in config.library.variants:
            if v.id == variant_id:
                variant = v
                break

        if not variant:
            logger.warning(f"Variant {variant_id} not found, using base logo")
            return logo

        # Create adjusted logo
        adjusted_logo = Logo(
            id=logo.id,
            name=logo.name,
            position_mm=logo.position_mm,
            tolerance_mm=logo.tolerance_mm,
            detector_type=logo.detector_type,
            roi=logo.roi,
            detector_params=logo.detector_params.copy(),
            instructions=logo.instructions
        )

        # Apply scale factor
        if variant.scale_factor != 1.0:
            adjusted_logo.position_mm = Point(
                logo.position_mm.x * variant.scale_factor,
                logo.position_mm.y * variant.scale_factor
            )

        # Apply specific offset for this logo
        if logo.id in variant.offsets:
            offset = variant.offsets[logo.id]
            adjusted_logo.position_mm = Point(
                adjusted_logo.position_mm.x + offset.x,
                adjusted_logo.position_mm.y + offset.y
            )

        return adjusted_logo

    def _convert_logo_to_pixels(self, logo: Logo) -> Logo:
        """Convert logo coordinates from mm to pixels using calibration"""
        if self.mm_per_pixel <= 0:
            return logo

        # Convert position from mm to pixels
        pixel_position = Point(
            logo.position_mm.x / self.mm_per_pixel,
            logo.position_mm.y / self.mm_per_pixel
        )

        # Convert ROI from mm to pixels
        pixel_roi = Rectangle(
            logo.roi.x / self.mm_per_pixel,
            logo.roi.y / self.mm_per_pixel,
            logo.roi.width / self.mm_per_pixel,
            logo.roi.height / self.mm_per_pixel
        )

        # Create pixel-based logo
        pixel_logo = Logo(
            id=logo.id,
            name=logo.name,
            position_mm=pixel_position,  # Actually pixels now
            tolerance_mm=logo.tolerance_mm / self.mm_per_pixel,  # Actually pixel tolerance
            detector_type=logo.detector_type,
            roi=pixel_roi
        )

        return pixel_logo

    def _perform_real_detection(
        self,
        processed_frame: np.ndarray,
        original_frame: np.ndarray,
        logo: Logo,
        config: AlignPressConfig
    ) -> DetectionResult:
        """Perform actual detection using real algorithms"""
        start_time = time.time()

        try:
            if logo.detector_type == 'contour':
                result = self._detect_contour(processed_frame, logo)
            elif logo.detector_type == 'template':
                result = self._detect_template(processed_frame, logo)
            elif logo.detector_type == 'aruco':
                result = self._detect_aruco(processed_frame, logo)
            else:
                # Fallback to contour detection
                logger.warning(f"Unknown detector type {logo.detector_type}, using contour")
                result = self._detect_contour(processed_frame, logo)

            # Convert result position back to mm if calibration is available
            if self.mm_per_pixel > 0 and result.success:
                result.position = (
                    result.position[0] * self.mm_per_pixel,
                    result.position[1] * self.mm_per_pixel
                )

            detection_time = (time.time() - start_time) * 1000  # ms
            logger.debug(f"Logo {logo.id} detection took {detection_time:.1f}ms")

            return result

        except Exception as e:
            logger.error(f"Detection error for logo {logo.id}: {e}")
            return DetectionResult(
                logo_id=logo.id,
                success=False,
                position=(0.0, 0.0),
                angle=0.0,
                confidence=0.0,
                error_mm=999.0,
                error_deg=999.0,
                timestamp=time.time()
            )

    def _detect_contour(self, frame: np.ndarray, logo: Logo) -> DetectionResult:
        """Detect logo using contour detection"""
        # Extract ROI
        roi = self._extract_roi(frame, logo.roi)
        if roi.size == 0:
            return DetectionResult(
                logo_id=logo.id, success=False, position=(0.0, 0.0),
                angle=0.0, confidence=0.0, error_mm=999.0, error_deg=999.0,
                timestamp=time.time()
            )

        # Convert to grayscale
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur
        params = self.detection_params['contour']
        blurred = cv2.GaussianBlur(gray_roi, params['blur_kernel'], 0)

        # Edge detection
        edges = cv2.Canny(blurred, params['canny_lower'], params['canny_upper'])

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return DetectionResult(
                logo_id=logo.id, success=False, position=(0.0, 0.0),
                angle=0.0, confidence=0.0, error_mm=999.0, error_deg=999.0,
                timestamp=time.time()
            )

        # Filter contours by area and aspect ratio
        valid_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if params['min_area'] <= area <= params['max_area']:
                rect = cv2.minAreaRect(contour)
                width, height = rect[1]
                if width > 0 and height > 0:
                    aspect_ratio = width / height
                    if params['aspect_ratio_range'][0] <= aspect_ratio <= params['aspect_ratio_range'][1]:
                        valid_contours.append((contour, area))

        if not valid_contours:
            return DetectionResult(
                logo_id=logo.id, success=False, position=(0.0, 0.0),
                angle=0.0, confidence=0.0, error_mm=999.0, error_deg=999.0,
                timestamp=time.time()
            )

        # Select largest valid contour
        best_contour = max(valid_contours, key=lambda x: x[1])[0]

        # Calculate centroid
        M = cv2.moments(best_contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"]) + logo.roi.x
            cy = int(M["m01"] / M["m00"]) + logo.roi.y
        else:
            cx, cy = logo.roi.x + logo.roi.width // 2, logo.roi.y + logo.roi.height // 2

        # Calculate confidence based on contour properties
        area = cv2.contourArea(best_contour)
        perimeter = cv2.arcLength(best_contour, True)
        if perimeter > 0:
            circularity = 4 * np.pi * area / (perimeter ** 2)
            confidence = min(1.0, circularity * 0.8 + 0.2)  # Base confidence + shape factor
        else:
            confidence = 0.5

        # Calculate angle from minimum area rectangle
        rect = cv2.minAreaRect(best_contour)
        angle = rect[2]

        # Calculate error from expected position
        expected_x, expected_y = logo.position_mm.x, logo.position_mm.y
        error_mm = np.sqrt((cx - expected_x) ** 2 + (cy - expected_y) ** 2)

        return DetectionResult(
            logo_id=logo.id,
            success=confidence > 0.5,  # Success threshold
            position=(float(cx), float(cy)),
            angle=float(angle),
            confidence=float(confidence),
            error_mm=float(error_mm),
            error_deg=0.0,
            timestamp=time.time()
        )

    def _detect_template(self, frame: np.ndarray, logo: Logo) -> DetectionResult:
        """Detect logo using template matching"""
        # For template matching, we'd need a template image
        # This is a simplified implementation that simulates template matching

        roi = self._extract_roi(frame, logo.roi)
        if roi.size == 0:
            return DetectionResult(
                logo_id=logo.id, success=False, position=(0.0, 0.0),
                angle=0.0, confidence=0.0, error_mm=999.0, error_deg=999.0,
                timestamp=time.time()
            )

        # Convert to grayscale
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Simulate template matching by analyzing texture and patterns
        # In a real implementation, you would load and match against template images

        # Calculate texture features
        mean_intensity = np.mean(gray_roi)
        std_intensity = np.std(gray_roi)

        # Edge density as a feature
        edges = cv2.Canny(gray_roi, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size

        # Simulate confidence based on texture features
        # This is a placeholder - in reality you'd compare against actual templates
        texture_score = min(1.0, edge_density * 2)  # Higher edge density = better match
        intensity_score = 1.0 - abs(mean_intensity - 128) / 128  # Prefer medium intensity

        confidence = (texture_score * 0.7 + intensity_score * 0.3)

        # Find center of ROI as detected position
        center_x = logo.roi.x + logo.roi.width // 2
        center_y = logo.roi.y + logo.roi.height // 2

        # Add some variation to simulate real detection
        variation_x = np.random.normal(0, 2)  # Small random offset
        variation_y = np.random.normal(0, 2)

        detected_x = center_x + variation_x
        detected_y = center_y + variation_y

        # Calculate error from expected position
        expected_x, expected_y = logo.position_mm.x, logo.position_mm.y
        error_mm = np.sqrt((detected_x - expected_x) ** 2 + (detected_y - expected_y) ** 2)

        return DetectionResult(
            logo_id=logo.id,
            success=confidence > 0.6,  # Template matching usually needs higher confidence
            position=(float(detected_x), float(detected_y)),
            angle=0.0,
            confidence=float(confidence),
            error_mm=float(error_mm),
            error_deg=0.0,
            timestamp=time.time()
        )

    def _detect_aruco(self, frame: np.ndarray, logo: Logo) -> DetectionResult:
        """Detect logo using ArUco marker detection"""
        # Extract ROI
        roi = self._extract_roi(frame, logo.roi)
        if roi.size == 0:
            return DetectionResult(
                logo_id=logo.id, success=False, position=(0.0, 0.0),
                angle=0.0, confidence=0.0, error_mm=999.0, error_deg=999.0,
                timestamp=time.time()
            )

        # Convert to grayscale
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Set up ArUco detection
        params = self.detection_params['aruco']
        dictionary = cv2.aruco.getPredefinedDictionary(params['dictionary'])
        detector_params = params['detector_params']

        # Detect ArUco markers
        corners, ids, rejected = cv2.aruco.detectMarkers(gray_roi, dictionary, parameters=detector_params)

        if ids is None or len(ids) == 0:
            return DetectionResult(
                logo_id=logo.id, success=False, position=(0.0, 0.0),
                angle=0.0, confidence=0.0, error_mm=999.0, error_deg=999.0,
                timestamp=time.time()
            )

        # Use the first detected marker
        marker_corners = corners[0][0]  # First marker, all corners
        marker_id = ids[0][0]

        # Calculate center of marker
        center_x = np.mean(marker_corners[:, 0]) + logo.roi.x
        center_y = np.mean(marker_corners[:, 1]) + logo.roi.y

        # Calculate angle from marker orientation
        # Vector from first corner to second corner
        dx = marker_corners[1, 0] - marker_corners[0, 0]
        dy = marker_corners[1, 1] - marker_corners[0, 1]
        angle = np.degrees(np.arctan2(dy, dx))

        # ArUco detection is usually very reliable
        confidence = 0.95

        # Calculate error from expected position
        expected_x, expected_y = logo.position_mm.x, logo.position_mm.y
        error_mm = np.sqrt((center_x - expected_x) ** 2 + (center_y - expected_y) ** 2)

        return DetectionResult(
            logo_id=logo.id,
            success=True,  # ArUco detection is binary - either found or not
            position=(float(center_x), float(center_y)),
            angle=float(angle),
            confidence=float(confidence),
            error_mm=float(error_mm),
            error_deg=0.0,
            timestamp=time.time()
        )

    def _enhance_simulation_result(
        self,
        result: DetectionResult,
        frame: np.ndarray,
        logo: Logo
    ) -> DetectionResult:
        """Add simulation-specific enhancements to detection result"""
        # Add more detailed analysis for debugging

        # Extract ROI for analysis
        roi_frame = self._extract_roi(frame, logo.roi)

        # Calculate additional metrics
        roi_stats = self._calculate_roi_statistics(roi_frame)

        # Add debugging information (could be stored in detector_params or similar)
        debug_info = {
            'roi_mean_brightness': roi_stats['mean_brightness'],
            'roi_contrast': roi_stats['contrast'],
            'roi_size_px': roi_stats['size'],
            'edge_density': roi_stats['edge_density'],
            'calibration_factor': self.mm_per_pixel,
            'detector_type': logo.detector_type
        }

        # For now, we'll log this info (in a real implementation,
        # we might store it in the result somehow)
        logger.debug(f"Logo {logo.id} debug info: {debug_info}")

        return result

    def _extract_roi(self, frame: np.ndarray, roi: Rectangle) -> np.ndarray:
        """Extract region of interest from frame"""
        x, y, w, h = int(roi.x), int(roi.y), int(roi.width), int(roi.height)

        # Ensure ROI is within image bounds
        frame_h, frame_w = frame.shape[:2]
        x = max(0, min(x, frame_w - 1))
        y = max(0, min(y, frame_h - 1))
        w = min(w, frame_w - x)
        h = min(h, frame_h - y)

        return frame[y:y+h, x:x+w]

    def _calculate_roi_statistics(self, roi_frame: np.ndarray) -> Dict[str, float]:
        """Calculate statistics for ROI analysis"""
        if roi_frame.size == 0:
            return {
                'mean_brightness': 0.0,
                'contrast': 0.0,
                'size': 0,
                'edge_density': 0.0
            }

        # Convert to grayscale for analysis
        if len(roi_frame.shape) == 3:
            gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi_frame

        # Calculate statistics
        mean_brightness = float(np.mean(gray))
        contrast = float(np.std(gray))

        # Edge detection for edge density
        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(np.sum(edges > 0) / edges.size)

        return {
            'mean_brightness': mean_brightness,
            'contrast': contrast,
            'size': roi_frame.size,
            'edge_density': edge_density
        }

    def _calculate_performance_metrics(
        self,
        logo_results: List[DetectionResult],
        total_time: float
    ) -> Dict[str, float]:
        """Calculate performance metrics for the detection session"""
        if not logo_results:
            return {}

        successful_results = [r for r in logo_results if r.success]

        metrics = {
            'total_logos': len(logo_results),
            'successful_logos': len(successful_results),
            'success_rate': len(successful_results) / len(logo_results),
            'average_confidence': np.mean([r.confidence for r in logo_results]),
            'average_error_mm': np.mean([r.error_mm for r in logo_results]),
            'max_error_mm': np.max([r.error_mm for r in logo_results]),
            'min_confidence': np.min([r.confidence for r in logo_results]),
            'max_confidence': np.max([r.confidence for r in logo_results]),
            'processing_time_per_logo_ms': (total_time * 1000) / len(logo_results)
        }

        if successful_results:
            metrics.update({
                'successful_avg_confidence': np.mean([r.confidence for r in successful_results]),
                'successful_avg_error_mm': np.mean([r.error_mm for r in successful_results])
            })

        return metrics

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create error result when simulation fails"""
        return {
            'error': True,
            'error_message': error_message,
            'timestamp': time.time(),
            'overall_success': False,
            'logo_count': 0,
            'successful_logos': 0,
            'failed_logos': 0
        }

    def simulate_batch_detection(
        self,
        image_dir: Path,
        style: Style,
        config: AlignPressConfig,
        image_pattern: str = "*.jpg"
    ) -> List[Dict[str, Any]]:
        """
        Simulate detection on a batch of images

        Args:
            image_dir: Directory containing test images
            style: Style configuration
            config: System configuration
            image_pattern: Glob pattern for image files

        Returns:
            List of detection results for each image
        """
        logger.info(f"Starting batch simulation in {image_dir}")

        image_files = list(image_dir.glob(image_pattern))
        if not image_files:
            logger.warning(f"No images found matching {image_pattern} in {image_dir}")
            return []

        results = []
        for image_path in image_files:
            result = self.simulate_garment_detection(
                image_path, style, config, save_results=False
            )
            results.append(result)

            # Log progress
            if len(results) % 10 == 0:
                logger.info(f"Processed {len(results)}/{len(image_files)} images")

        # Calculate batch statistics
        batch_stats = self._calculate_batch_statistics(results)
        logger.info(f"Batch completed: {batch_stats}")

        return results

    def _calculate_batch_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics across a batch of detection results"""
        if not results:
            return {}

        successful_detections = [r for r in results if r.get('overall_success', False)]

        # Overall statistics
        stats = {
            'total_images': len(results),
            'successful_images': len(successful_detections),
            'overall_success_rate': len(successful_detections) / len(results),
            'average_processing_time_ms': np.mean([r.get('processing_time_ms', 0) for r in results]),
            'total_processing_time_ms': np.sum([r.get('processing_time_ms', 0) for r in results])
        }

        # Logo-level statistics
        all_logo_results = []
        for result in results:
            if 'logo_results' in result:
                all_logo_results.extend(result['logo_results'])

        if all_logo_results:
            successful_logos = [r for r in all_logo_results if r.get('success', False)]
            stats.update({
                'total_logo_detections': len(all_logo_results),
                'successful_logo_detections': len(successful_logos),
                'logo_success_rate': len(successful_logos) / len(all_logo_results),
                'average_confidence': np.mean([r.get('confidence', 0) for r in all_logo_results]),
                'average_error_mm': np.mean([r.get('error_mm', 0) for r in all_logo_results])
            })

        return stats

    def generate_detection_report(
        self,
        results: Optional[List[Dict[str, Any]]] = None,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate a detailed report of detection results

        Args:
            results: Optional list of results, uses history if not provided
            output_path: Optional path to save report

        Returns:
            Report as formatted string
        """
        if results is None:
            results = self.results_history

        if not results:
            return "No detection results available for report generation."

        # Generate report content
        report_lines = [
            "=" * 60,
            "ALIGNPRESS v2 - DETECTION SIMULATION REPORT",
            "=" * 60,
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Sessions: {len(results)}",
            ""
        ]

        # Calculate overall statistics
        batch_stats = self._calculate_batch_statistics(results)

        report_lines.extend([
            "OVERALL STATISTICS:",
            "-" * 30,
            f"Total Images Processed: {batch_stats.get('total_images', 0)}",
            f"Successfully Detected: {batch_stats.get('successful_images', 0)}",
            f"Overall Success Rate: {batch_stats.get('overall_success_rate', 0):.1%}",
            f"Average Processing Time: {batch_stats.get('average_processing_time_ms', 0):.1f} ms",
            f"Total Processing Time: {batch_stats.get('total_processing_time_ms', 0):.1f} ms",
            ""
        ])

        if 'logo_success_rate' in batch_stats:
            report_lines.extend([
                "LOGO-LEVEL STATISTICS:",
                "-" * 30,
                f"Total Logo Detections: {batch_stats.get('total_logo_detections', 0)}",
                f"Successful Logo Detections: {batch_stats.get('successful_logo_detections', 0)}",
                f"Logo Success Rate: {batch_stats.get('logo_success_rate', 0):.1%}",
                f"Average Confidence: {batch_stats.get('average_confidence', 0):.3f}",
                f"Average Error: {batch_stats.get('average_error_mm', 0):.2f} mm",
                ""
            ])

        # Add detailed results for failed detections
        failed_results = [r for r in results if not r.get('overall_success', False)]
        if failed_results:
            report_lines.extend([
                "FAILED DETECTIONS:",
                "-" * 30
            ])

            for result in failed_results[:10]:  # Show first 10 failures
                report_lines.append(
                    f"• {result.get('image_path', 'Unknown')}: "
                    f"{result.get('failed_logos', 0)} failed logos"
                )

            if len(failed_results) > 10:
                report_lines.append(f"... and {len(failed_results) - 10} more")

            report_lines.append("")

        report_lines.extend([
            "=" * 60,
            "End of Report"
        ])

        report_text = "\n".join(report_lines)

        # Save to file if requested
        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                logger.info(f"Report saved to {output_path}")
            except Exception as e:
                logger.error(f"Error saving report: {e}")

        return report_text

    def simulate_batch_with_variants(
        self,
        image_dir: Path,
        config: AlignPressConfig,
        calibration_path: Optional[Path] = None,
        image_pattern: str = "*.jpg",
        test_variants: bool = True
    ) -> Dict[str, Any]:
        """
        Simulate detection on batch of images with all variants

        Args:
            image_dir: Directory containing test images
            config: System configuration with variants
            calibration_path: Optional calibration file
            image_pattern: Glob pattern for image files
            test_variants: Whether to test size variants

        Returns:
            Comprehensive results across all images and variants
        """
        logger.info(f"Starting batch simulation with variants in {image_dir}")

        if calibration_path:
            self.load_calibration(calibration_path)

        image_files = list(image_dir.glob(image_pattern))
        if not image_files:
            logger.warning(f"No images found matching {image_pattern} in {image_dir}")
            return {"error": "No images found"}

        style = config.get_active_style()
        if not style:
            logger.error("No active style found in configuration")
            return {"error": "No active style"}

        all_results = []
        variant_results = {}

        # Test base style
        for image_path in image_files:
            result = self.simulate_garment_detection(
                image_path, style, config, save_results=False
            )
            result['variant_id'] = 'base'
            result['image_filename'] = image_path.name
            all_results.append(result)

        # Test variants if enabled
        if test_variants and config.library.variants:
            for variant in config.library.variants:
                variant_results[variant.id] = []
                for image_path in image_files:
                    result = self.simulate_garment_detection(
                        image_path, style, config, variant_id=variant.id, save_results=False
                    )
                    result['variant_id'] = variant.id
                    result['image_filename'] = image_path.name
                    variant_results[variant.id].append(result)
                    all_results.append(result)

        # Calculate comprehensive statistics
        batch_stats = self._calculate_comprehensive_batch_stats(all_results, variant_results)

        return {
            'batch_stats': batch_stats,
            'all_results': all_results,
            'variant_results': variant_results,
            'images_processed': len(image_files),
            'variants_tested': len(variant_results),
            'total_detections': len(all_results)
        }

    def _calculate_comprehensive_batch_stats(
        self,
        all_results: List[Dict[str, Any]],
        variant_results: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Calculate comprehensive statistics for batch processing"""
        if not all_results:
            return {}

        # Overall statistics
        overall_success = [r for r in all_results if r.get('overall_success', False)]
        total_logos = sum(r.get('logo_count', 0) for r in all_results)
        successful_logos = sum(r.get('successful_logos', 0) for r in all_results)

        stats = {
            'total_sessions': len(all_results),
            'total_images': len(set(r.get('image_filename', '') for r in all_results)),
            'successful_sessions': len(overall_success),
            'session_success_rate': len(overall_success) / len(all_results),
            'total_logo_attempts': total_logos,
            'successful_logo_detections': successful_logos,
            'logo_success_rate': successful_logos / total_logos if total_logos > 0 else 0,
            'average_processing_time_ms': np.mean([r.get('processing_time_ms', 0) for r in all_results]),
            'average_confidence': np.mean([r.get('average_confidence', 0) for r in all_results])
        }

        # Per-variant statistics
        if variant_results:
            variant_stats = {}
            for variant_id, results in variant_results.items():
                if results:
                    variant_successful = [r for r in results if r.get('overall_success', False)]
                    variant_stats[variant_id] = {
                        'sessions': len(results),
                        'successful_sessions': len(variant_successful),
                        'success_rate': len(variant_successful) / len(results),
                        'average_confidence': np.mean([r.get('average_confidence', 0) for r in results]),
                        'average_processing_time_ms': np.mean([r.get('processing_time_ms', 0) for r in results])
                    }

            stats['variant_performance'] = variant_stats

        # Performance insights
        processing_times = [r.get('processing_time_ms', 0) for r in all_results]
        confidences = [r.get('average_confidence', 0) for r in all_results]

        stats['performance_insights'] = {
            'fastest_detection_ms': np.min(processing_times),
            'slowest_detection_ms': np.max(processing_times),
            'processing_time_std': np.std(processing_times),
            'highest_confidence': np.max(confidences),
            'lowest_confidence': np.min(confidences),
            'confidence_std': np.std(confidences)
        }

        return stats

    def export_batch_results(
        self,
        batch_results: Dict[str, Any],
        output_dir: Path,
        create_debug_images: bool = True
    ) -> Path:
        """Export comprehensive batch results with reports and debug images"""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate comprehensive report
        report_path = output_dir / "batch_detection_report.txt"
        report_content = self._generate_comprehensive_report(batch_results)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        # Export JSON results
        json_path = output_dir / "batch_results.json"
        import json
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(batch_results, f, indent=2, default=str)

        # Create debug images if requested
        if create_debug_images:
            debug_dir = output_dir / "debug_images"
            debug_dir.mkdir(exist_ok=True)

            for result in batch_results['all_results'][:20]:  # Limit to first 20
                if 'image_path' in result:
                    image_path = Path(result['image_path'])
                    if image_path.exists():
                        debug_filename = f"{image_path.stem}_{result.get('variant_id', 'base')}_debug.jpg"
                        debug_path = debug_dir / debug_filename
                        self.create_visual_debug_image(image_path, result, debug_path)

        logger.info(f"Batch results exported to {output_dir}")
        return output_dir

    def _generate_comprehensive_report(self, batch_results: Dict[str, Any]) -> str:
        """Generate comprehensive batch processing report"""
        stats = batch_results.get('batch_stats', {})

        lines = [
            "=" * 80,
            "ALIGNPRESS v2 - COMPREHENSIVE BATCH DETECTION REPORT",
            "=" * 80,
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Calibration Factor: {self.mm_per_pixel:.4f} mm/pixel",
            "",
            "OVERALL PERFORMANCE:",
            "-" * 40,
            f"Total Images Processed: {stats.get('total_images', 0)}",
            f"Total Detection Sessions: {stats.get('total_sessions', 0)}",
            f"Variants Tested: {batch_results.get('variants_tested', 0)}",
            f"Total Logo Attempts: {stats.get('total_logo_attempts', 0)}",
            "",
            "SUCCESS RATES:",
            "-" * 40,
            f"Session Success Rate: {stats.get('session_success_rate', 0):.1%}",
            f"Logo Detection Rate: {stats.get('logo_success_rate', 0):.1%}",
            f"Average Confidence: {stats.get('average_confidence', 0):.3f}",
            f"Average Processing Time: {stats.get('average_processing_time_ms', 0):.1f} ms",
            ""
        ]

        # Add performance insights
        if 'performance_insights' in stats:
            insights = stats['performance_insights']
            lines.extend([
                "PERFORMANCE INSIGHTS:",
                "-" * 40,
                f"Fastest Detection: {insights.get('fastest_detection_ms', 0):.1f} ms",
                f"Slowest Detection: {insights.get('slowest_detection_ms', 0):.1f} ms",
                f"Processing Time Variance: ±{insights.get('processing_time_std', 0):.1f} ms",
                f"Confidence Range: {insights.get('lowest_confidence', 0):.3f} - {insights.get('highest_confidence', 0):.3f}",
                f"Confidence Variance: ±{insights.get('confidence_std', 0):.3f}",
                ""
            ])

        # Add variant performance
        if 'variant_performance' in stats:
            lines.extend(["VARIANT PERFORMANCE:", "-" * 40])
            for variant_id, variant_stats in stats['variant_performance'].items():
                lines.extend([
                    f"Variant: {variant_id}",
                    f"  Success Rate: {variant_stats.get('success_rate', 0):.1%}",
                    f"  Avg Confidence: {variant_stats.get('average_confidence', 0):.3f}",
                    f"  Avg Time: {variant_stats.get('average_processing_time_ms', 0):.1f} ms",
                    ""
                ])

        # Add failed detection analysis
        failed_results = [r for r in batch_results['all_results'] if not r.get('overall_success', False)]
        if failed_results:
            lines.extend([
                "FAILED DETECTIONS ANALYSIS:",
                "-" * 40,
                f"Total Failed Sessions: {len(failed_results)}"
            ])

            # Group by variant
            failed_by_variant = {}
            for result in failed_results[:10]:  # Show first 10
                variant = result.get('variant_id', 'unknown')
                if variant not in failed_by_variant:
                    failed_by_variant[variant] = []
                failed_by_variant[variant].append(result.get('image_filename', 'unknown'))

            for variant, images in failed_by_variant.items():
                lines.append(f"  {variant}: {', '.join(images[:5])}")
                if len(images) > 5:
                    lines.append(f"    ... and {len(images) - 5} more")

            lines.append("")

        lines.extend([
            "=" * 80,
            "End of Comprehensive Report"
        ])

        return "\n".join(lines)

    def create_visual_debug_image(
        self,
        image_path: Path,
        detection_result: Dict[str, Any],
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Create a visual debug image showing detection results

        Args:
            image_path: Original image path
            detection_result: Detection result from simulation
            output_path: Optional output path for debug image

        Returns:
            Path to created debug image, or None if failed
        """
        try:
            # Load original image
            image = cv2.imread(str(image_path))
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return None

            # Convert to PIL for drawing
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            draw = ImageDraw.Draw(pil_image)

            # Try to load a font (fallback to default if not available)
            try:
                font = ImageFont.truetype("arial.ttf", 16)
                font_small = ImageFont.truetype("arial.ttf", 12)
            except:
                font = ImageFont.load_default()
                font_small = font

            # Draw detection results for each logo
            logo_results = detection_result.get('logo_results', [])
            for logo_result in logo_results:
                success = logo_result.get('success', False)
                position = logo_result.get('position', [0, 0])
                confidence = logo_result.get('confidence', 0)
                logo_id = logo_result.get('logo_id', 'unknown')

                x, y = int(position[0]), int(position[1])

                # Choose colors based on success
                color = 'green' if success else 'red'
                outline_color = 'darkgreen' if success else 'darkred'

                # Draw position marker (crosshair)
                size = 15
                draw.line([(x-size, y), (x+size, y)], fill=color, width=3)
                draw.line([(x, y-size), (x, y+size)], fill=color, width=3)

                # Draw circle around position
                circle_size = 20
                draw.ellipse([
                    x - circle_size, y - circle_size,
                    x + circle_size, y + circle_size
                ], outline=outline_color, width=2)

                # Add text label
                text = f"{logo_id}\nConf: {confidence:.2f}"

                # Draw text background
                text_bbox = draw.textbbox((x + 25, y - 15), text, font=font_small)
                draw.rectangle(text_bbox, fill='white', outline=outline_color)

                # Draw text
                draw.text((x + 25, y - 15), text, fill=outline_color, font=font_small)

            # Add overall result header
            header_text = f"Detection Result: {'SUCCESS' if detection_result.get('overall_success') else 'FAILED'}"
            header_text += f" | Time: {detection_result.get('processing_time_ms', 0):.1f}ms"
            header_text += f" | Logos: {detection_result.get('successful_logos', 0)}/{detection_result.get('logo_count', 0)}"

            # Draw header background
            header_bbox = draw.textbbox((10, 10), header_text, font=font)
            draw.rectangle(header_bbox, fill='white', outline='black')
            draw.text((10, 10), header_text, fill='black', font=font)

            # Save debug image
            if output_path is None:
                output_path = image_path.parent / f"{image_path.stem}_debug{image_path.suffix}"

            # Convert back to CV2 format and save
            debug_image_cv2 = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(output_path), debug_image_cv2)

            logger.info(f"Debug image saved: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error creating debug image: {e}")
            return None


def main():
    """Example usage of detection simulator"""
    if not CV2_AVAILABLE:
        print("Error: OpenCV/PIL dependencies not available")
        return

    # This would be used like this:
    print("""
AlignPress v2 Detection Simulator

Ejemplo de uso:

from alignpress_v2.tools.detection_simulator import DetectionSimulator
from alignpress_v2.config.models import create_default_config
from pathlib import Path

# Crear simulador
simulator = DetectionSimulator()

# Cargar configuración
config = create_default_config()
style = config.get_active_style()

# Simular detección en una imagen
result = simulator.simulate_garment_detection(
    Path("test_images/camisola_comunicaciones_m.jpg"),
    style,
    config
)

# Generar imagen de debug
debug_image = simulator.create_visual_debug_image(
    Path("test_images/camisola_comunicaciones_m.jpg"),
    result
)

# Generar reporte
report = simulator.generate_detection_report()
print(report)
""")


if __name__ == "__main__":
    main()