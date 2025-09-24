from alignpress.core.geometry import (
    AlignmentEvaluation,
    AlignmentMetrics,
    Pose2D,
    compute_alignment_metrics,
    diff_pose,
    evaluate_alignment,
)


def test_diff_pose_returns_expected_values():
    target = Pose2D(center=(100.0, 200.0), angle_deg=0.0, size=(50.0, 30.0))
    detected = Pose2D(center=(110.0, 190.0), angle_deg=5.0, size=(48.0, 32.0))
    dx_mm, dy_mm, dtheta = diff_pose(detected, target, mm_per_px=0.2)
    assert dx_mm == 2.0
    assert dy_mm == -2.0
    assert dtheta == 5.0


def test_compute_alignment_metrics_wraps_diff_pose():
    target = Pose2D(center=(0.0, 0.0), angle_deg=10.0, size=(10.0, 10.0))
    detected = Pose2D(center=(5.0, -5.0), angle_deg=370.0, size=(9.0, 9.0))
    metrics = compute_alignment_metrics(detected, target, mm_per_px=0.5)
    assert isinstance(metrics, AlignmentMetrics)
    assert metrics.dx_mm == 2.5
    assert metrics.dy_mm == -2.5
    assert metrics.dtheta_deg == 0.0


def test_evaluate_alignment_classifies_status():
    target = Pose2D(center=(100.0, 200.0), angle_deg=0.0, size=(50.0, 30.0))
    detected = Pose2D(center=(102.0, 198.0), angle_deg=-1.0, size=(49.0, 29.0))
    evaluation = evaluate_alignment(detected, target, mm_per_px=0.5, tolerance_mm=2.0, tolerance_deg=2.0)
    assert isinstance(evaluation, AlignmentEvaluation)
    assert evaluation.status == "ok"
    assert evaluation.within_tolerance is True
    assert evaluation.metrics.dx_mm == 1.0
    assert evaluation.metrics.dy_mm == -1.0
    assert evaluation.metrics.dtheta_deg == -1.0

    evaluation_out = evaluate_alignment(detected, target, mm_per_px=0.5, tolerance_mm=0.5, tolerance_deg=0.5)
    assert evaluation_out.status == "out_of_tolerance"
    assert evaluation_out.within_tolerance is False

    evaluation_none = evaluate_alignment(None, target, mm_per_px=0.5, tolerance_mm=2.0, tolerance_deg=2.0)
    assert evaluation_none.status == "not_found"
    assert evaluation_none.metrics is None
