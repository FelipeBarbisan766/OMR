from __future__ import annotations

import io
from pathlib import Path

from backend.constants import (
    ARUCO_MARGIN_MM,
    ARUCO_MARKER_SIZE_MM,
    BUBBLE_RADIUS_MM,
    BUBBLE_START_X_MM,
    BUBBLE_START_Y_FROM_TOP_MM,
    COL_GAP_MM,
    ROW_GAP_MM,
)


def _aruco_png_bytes(marker_id: int, size_px: int = 300) -> bytes:
    import cv2

    if not hasattr(cv2, "aruco"):
        raise RuntimeError("OpenCV aruco module is required to generate the answer sheet.")

    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    marker = cv2.aruco.generateImageMarker(dictionary, marker_id, size_px)
    ok, encoded = cv2.imencode(".png", marker)
    if not ok:
        raise RuntimeError("Failed to encode ArUco marker image.")
    return encoded.tobytes()


def generate_answer_sheet(
    output_path: str | Path,
    student_id: str,
    num_questions: int = 10,
    choices: int = 5,
) -> str:
    from reportlab.graphics.barcode import qr
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(output), pagesize=A4)
    page_w, page_h = A4

    # Check that grid doesn't overflow page
    max_y_px = BUBBLE_START_Y_FROM_TOP_MM + (num_questions - 1) * ROW_GAP_MM
    if max_y_px > 280:  # Leave 17mm margin at bottom
        raise ValueError(
            f"Grid would overflow page: {num_questions} questions need "
            f"{max_y_px}mm height (max 280mm available)"
        )

    marker_size = ARUCO_MARKER_SIZE_MM * mm
    margin = ARUCO_MARGIN_MM * mm
    marker_positions = [
        (margin, page_h - margin - marker_size),
        (page_w - margin - marker_size, page_h - margin - marker_size),
        (margin, margin),
        (page_w - margin - marker_size, margin),
    ]

    for marker_id, (x, y) in enumerate(marker_positions):
        c.drawImage(ImageReader(io.BytesIO(_aruco_png_bytes(marker_id))), x, y, marker_size, marker_size)

    # Title and student info positioned to avoid ArUco marker at top-left
    # (which occupies x: 10-30mm, y: 267-287mm on A4)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50 * mm, page_h - 20 * mm, "Folha de Respostas OMR")
    c.setFont("Helvetica", 10)
    c.drawString(50 * mm, page_h - 26 * mm, f"Aluno: {student_id}")

    # QR code positioned to avoid marker at top-right
    # (which occupies x: 177-197mm, y: 267-287mm on A4)
    qr_code = qr.QrCodeWidget(student_id)
    bounds = qr_code.getBounds()
    scale = 15 * mm / max(bounds[2] - bounds[0], bounds[3] - bounds[1])
    c.saveState()
    c.translate(page_w - 25 * mm, page_h - 20 * mm)
    c.scale(scale, scale)
    qr_code.drawOn(c, 0, 0)
    c.restoreState()

    bubble_radius = BUBBLE_RADIUS_MM * mm
    start_x = BUBBLE_START_X_MM * mm
    start_y = page_h - BUBBLE_START_Y_FROM_TOP_MM * mm
    row_gap = ROW_GAP_MM * mm
    col_gap = COL_GAP_MM * mm

    # Draw column headers (A, B, C, D, E)
    c.setFont("Helvetica-Bold", 10)
    for i in range(choices):
        x = start_x + i * col_gap
        c.drawString(x - 2 * mm, start_y + 5 * mm, chr(ord("A") + i))

    c.setFont("Helvetica", 9)
    for q in range(num_questions):
        y = start_y - q * row_gap
        c.drawString(15 * mm, y - 1 * mm, f"{q + 1:02d}")
        for i in range(choices):
            x = start_x + i * col_gap
            c.circle(x, y, bubble_radius, stroke=1, fill=0)

    # Footer positioned to avoid marker at bottom-left
    # (which occupies x: 10-30mm, y: 10-30mm on A4)
    c.setFont("Helvetica", 8)
    c.drawString(50 * mm, 12 * mm, "Imprima em fundo branco, sem escalonamento.")

    c.save()
    return str(output)
