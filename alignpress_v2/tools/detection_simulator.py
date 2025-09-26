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

        logger.info("DetectionSimulator initialized")

    def simulate_garment_detection(
        self,
        image_path: Path,
        style: Style,
        config: AlignPressConfig,
        variant_id: Optional[str] = None,
        save_results: bool = True
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

        # Load image
        try:
            frame = cv2.imread(str(image_path))
            if frame is None:
                raise ValueError(f"Could not load image: {image_path}")
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            return self._create_error_result(str(e))

        # Start timing
        start_time = time.time()

        # Simulate detection for each logo
        logo_results = []
        overall_success = True

        for logo in style.logos:
            logo_result = self._simulate_single_logo_detection(
                frame, logo, config, variant_id
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

    def _simulate_single_logo_detection(
        self,
        frame: np.ndarray,
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

            # Use the actual detection service
            result = self.detection_service.detect_logo(frame, adjusted_logo, config)

            # Add simulation-specific enhancements
            result = self._enhance_simulation_result(result, frame, adjusted_logo)

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
            'edge_density': roi_stats['edge_density']
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