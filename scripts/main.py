import argparse
import pathlib
import time

import cv2

from alignpress.core.camera import Camera
from alignpress.core.calibration import load_calibration
from alignpress.core.geometry import Pose2D
from alignpress.core.presets import load_preset
from alignpress.core.alignment import LogoAligner
from alignpress.gui.overlay import draw_ghost_rect, draw_detected_rect, draw_arrows, put_hud

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--image", type=str, default=None, help="Procesar una imagen fija en vez de cámara")
    ap.add_argument("--resolution", type=str, default=None, help="e.g. 1280x720")
    ap.add_argument("--preset", type=str, required=True)
    ap.add_argument("--calibration", type=str, required=True)
    args = ap.parse_args()

    res = None
    if args.resolution:
        w,h = args.resolution.lower().split("x")
        res = (int(w), int(h))

    preset = load_preset(pathlib.Path(args.preset))
    calib = load_calibration(pathlib.Path(args.calibration))
    aligner = LogoAligner(preset=preset, calibration=calib)
    cam = None
    static_frame = None
    if args.image:
        img_path = pathlib.Path(args.image).expanduser()
        static_frame = cv2.imread(str(img_path))
        if static_frame is None:
            raise FileNotFoundError(f"No se pudo leer la imagen fija: {img_path}")
        print(f"[INFO] Ejecutando en modo imagen fija: {img_path}")
    else:
        cam = Camera(index=args.camera, resolution=res)

    print(f"[INFO] mm/px: {calib.mm_per_px:.5f} (metodo: {calib.method})")

    target_pose = Pose2D(center=preset.target_center_px, angle_deg=preset.target_angle_deg, size=preset.target_size_px)
    frame_idx = 0

    try:
        while True:
            frame = static_frame.copy() if static_frame is not None else cam.read()
            analysis = aligner.process_frame(frame, timestamp=time.time(), frame_id=f"live_{frame_idx:06d}")
            det = analysis.detection.pose

            # Overlay ROI
            x,y,w,h = preset.roi
            cv2.rectangle(frame, (x,y), (x+w, y+h), (80,80,80), 1)

            # Ghost target
            draw_ghost_rect(frame, target_pose.center, target_pose.size, target_pose.angle_deg, color=(0,255,0), thickness=1)

            status_text = "Buscando..."
            status_color = (0,255,255)

            if det is not None and analysis.evaluation.metrics is not None:
                draw_detected_rect(frame, det.center, det.size, det.angle_deg, color=(0,0,255), thickness=2)
                metrics = analysis.evaluation.metrics
                dx_mm = metrics.dx_mm
                dy_mm = metrics.dy_mm
                dtheta = metrics.dtheta_deg
                # flechas
                draw_arrows(frame, target_pose.center, det.center, color=(255,255,255))
                # HUD
                txt = f"dx={dx_mm:+.2f} mm, dy={dy_mm:+.2f} mm, dθ={dtheta:+.2f}°"
                put_hud(frame, txt, org=(10,30), color=(255,255,255))
                # estado
                if analysis.evaluation.within_tolerance:
                    status_text = "OK"
                    status_color = (0,200,0)
                else:
                    status_text = "Ajustar"
                    status_color = (0,0,255)
            else:
                put_hud(frame, "No detectado", org=(10,30), color=(0,0,255))

            put_hud(frame, f"{status_text}", org=(10,60), color=status_color)

            cv2.imshow("AlignPress Pro - Fase 1", frame)
            wait_delay = 0 if static_frame is not None else 1
            key = cv2.waitKey(wait_delay) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                ts = int(time.time())
                cv2.imwrite(f"frame_{ts}.png", frame)
                print(f"[INFO] frame guardado frame_{ts}.png")
            elif static_frame is not None and key != 255:
                # En modo imagen, cualquier otra tecla sale para evitar bucles infinitos
                break
            frame_idx += 1

    finally:
        if cam is not None:
            cam.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
