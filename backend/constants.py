"""
Shared constants for PDF generation and OMR detection.
These ensure coordinate synchronization between pdf_gen.py and omr.py.
"""

# Bubble positioning (in millimeters, from PDF standard)
BUBBLE_START_X_MM = 30
BUBBLE_START_Y_FROM_TOP_MM = 50
ROW_GAP_MM = 9
COL_GAP_MM = 12
BUBBLE_RADIUS_MM = 3.2

# ArUco marker positioning and sizing (in millimeters)
ARUCO_MARKER_SIZE_MM = 20
ARUCO_MARGIN_MM = 10

# Confidence threshold for answer detection (ratio between top 2 scores)
# Increased from 1.12 to 1.8 to reduce false positives from eraser marks
CONFIDENCE_THRESHOLD = 1.8

# PDF warping dimensions (pixels)
# These should match the expected output dimensions from perspective transform
WARP_WIDTH_PX = 1240
WARP_HEIGHT_PX = 1754

# Conversion factor from millimeters to pixels
# Based on A4 height: 297mm -> 1754px
MM_TO_PX = WARP_HEIGHT_PX / 297.0  # ~5.906

# Derived pixel coordinates (calculated from mm values + MM_TO_PX)
BUBBLE_START_X_PX = int(BUBBLE_START_X_MM * MM_TO_PX)
BUBBLE_START_Y_PX = int(BUBBLE_START_Y_FROM_TOP_MM * MM_TO_PX)
ROW_GAP_PX = int(ROW_GAP_MM * MM_TO_PX)
COL_GAP_PX = int(COL_GAP_MM * MM_TO_PX)
BUBBLE_RADIUS_PX = int(BUBBLE_RADIUS_MM * MM_TO_PX)
