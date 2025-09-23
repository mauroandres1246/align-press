import argparse, pathlib, json, time
import cv2
import numpy as np
from alignpress.core.camera import Camera
from alignpress.core.calibration import Calibration, chessboard_mm_per_px, aruco_mm_per_px
from alignpress.core.geometry import Pose2D, diff_pose
from alignpress.core.presets import load_preset
from alignpress.gui.overlay import draw_ghost_rect, draw_detected_rect, draw_arrows, put_hud
from alignpress.detection.contour_detector import detect_logo_contour
from alignpress.detection.aruco_detector import detect_logo_aruco

def load_calibration(path: pathlib.Path) -> Calibration:
    cfg = json.loads(path.read_text())
    if cfg.get("mode") == "constant":
        return Calibration(mm_per_px=float(cfg["mm_per_px"]), method="constant", meta=cfg)
    else:
        # modo offline con imagen
        img_path = pathlib.Path(cfg["image"])
        img = cv2.imread(str(img_path))
        if img is None:
            raise FileNotFoundError(f"No se pudo leer imagen de calibración: {img_path}")
        if cfg["mode"] == "chessboard":
            cal = chessboard_mm_per_px(img, tuple(cfg["pattern_size"]), float(cfg["square_size_mm"]))
        elif cfg["mode"] == "aruco":
            cal = aruco_mm_per_px(img, float(cfg["marker_length_mm"]), cfg.get("dictionary","DICT_5X5_50"))
        else:
            raise ValueError("Modo de calibración no reconocido")
        if cal is None:
            raise RuntimeError("Fallo la calibración en la imagen provista")
        return cal

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", type=int, default=0)
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
    cam = Camera(index=args.camera, resolution=res)

    print(f"[INFO] mm/px: {calib.mm_per_px:.5f} (metodo: {calib.method})")

    target_pose = Pose2D(center=preset.target_center_px, angle_deg=preset.target_angle_deg, size=preset.target_size_px)

    try:
        while True:
            frame = cam.read()
            # Detección
            if preset.detection_mode == "aruco":
                det = detect_logo_aruco(frame, preset.roi, preset.params)
                if det is None:
                    det = detect_logo_contour(frame, preset.roi, preset.params)
            else:
                det = detect_logo_contour(frame, preset.roi, preset.params)
                if det is None:
                    det = detect_logo_aruco(frame, preset.roi, preset.params)

            # Overlay ROI
            x,y,w,h = preset.roi
            cv2.rectangle(frame, (x,y), (x+w, y+h), (80,80,80), 1)

            # Ghost target
            draw_ghost_rect(frame, target_pose.center, target_pose.size, target_pose.angle_deg, color=(0,255,0), thickness=1)

            status_text = "Buscando..."
            status_color = (0,255,255)

            if det is not None:
                draw_detected_rect(frame, det.center, det.size, det.angle_deg, color=(0,0,255), thickness=2)
                dx_mm, dy_mm, dtheta = diff_pose(det, target_pose, calib.mm_per_px)
                # flechas
                draw_arrows(frame, target_pose.center, det.center, color=(255,255,255))
                # HUD
                txt = f"dx={dx_mm:+.2f} mm, dy={dy_mm:+.2f} mm, dθ={dtheta:+.2f}°"
                put_hud(frame, txt, org=(10,30), color=(255,255,255))
                # estado
                if abs(dx_mm) <= preset.tolerance_mm and abs(dy_mm) <= preset.tolerance_mm and abs(dtheta) <= preset.tolerance_deg:
                    status_text = "OK"
                    status_color = (0,200,0)
                else:
                    status_text = "Ajustar"
                    status_color = (0,0,255)
            else:
                put_hud(frame, "No detectado", org=(10,30), color=(0,0,255))

            put_hud(frame, f"{status_text}", org=(10,60), color=status_color)

            cv2.imshow("AlignPress Pro - Fase 1", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                ts = int(time.time())
                cv2.imwrite(f"frame_{ts}.png", frame)
                print(f"[INFO] frame guardado frame_{ts}.png")

    finally:
        cam.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
