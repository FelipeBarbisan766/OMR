from __future__ import annotations

import argparse
from pathlib import Path


def _order_points(pts):
    import numpy as np

    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[s.argmin()]
    rect[2] = pts[s.argmax()]

    diff = pts[:, 0] - pts[:, 1]
    rect[1] = pts[diff.argmin()]
    rect[3] = pts[diff.argmax()]
    return rect


def _warp_from_aruco(image):
    import cv2
    import numpy as np

    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    detector = cv2.aruco.ArucoDetector(dictionary)
    corners, ids, _ = detector.detectMarkers(image)

    if ids is None or len(ids) < 4:
        raise RuntimeError("Não foi possível localizar os 4 marcadores ArUco.")

    points = []
    for marker_corners in corners[:4]:
        points.append(marker_corners[0].mean(axis=0))

    src = _order_points(np.array(points, dtype="float32"))
    width, height = 1240, 1754
    dst = np.array([[0, 0], [width, 0], [width, height], [0, height]], dtype="float32")
    matrix = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(image, matrix, (width, height))


def detect_answers(image_path: str | Path, num_questions: int = 10, choices: int = 5) -> list[str]:
    import cv2
    import numpy as np

    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"Imagem não encontrada: {image_path}")

    if not hasattr(cv2, "aruco"):
        raise RuntimeError("OpenCV com módulo aruco é obrigatório para OMR.")

    warped = _warp_from_aruco(image)
    _, binary = cv2.threshold(warped, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    start_x = 295
    start_y = 1030
    row_gap = 62
    col_gap = 84
    radius = 20

    answers = []
    for q in range(num_questions):
        y = start_y + q * row_gap
        fill_scores = []
        for c in range(choices):
            x = start_x + c * col_gap
            mask = np.zeros(binary.shape, dtype=np.uint8)
            cv2.circle(mask, (x, y), radius, 255, -1)
            score = cv2.countNonZero(cv2.bitwise_and(binary, binary, mask=mask))
            fill_scores.append(score)

        best_idx = int(np.argmax(fill_scores))
        sorted_scores = sorted(fill_scores, reverse=True)
        if len(sorted_scores) > 1 and sorted_scores[0] < sorted_scores[1] * 1.12:
            answers.append("?")
        else:
            answers.append(chr(ord("A") + best_idx))
    return answers


def main() -> None:
    parser = argparse.ArgumentParser(description="Validação local do motor OMR")
    parser.add_argument("image", help="Caminho da foto/scan da folha")
    parser.add_argument("--questions", type=int, default=10)
    parser.add_argument("--choices", type=int, default=5)
    args = parser.parse_args()

    detected = detect_answers(args.image, args.questions, args.choices)
    print("Respostas detectadas:", " ".join(detected))


if __name__ == "__main__":
    main()
