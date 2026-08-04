"""Prep a photo for ASCII conversion.

Pipeline: isolate the subject, boost local contrast (CLAHE), composite onto
pure white so the background maps to blank space in the ASCII ramp.

Subject isolation strategy:
  1. If `rembg` is installed, use it (best for busy backgrounds).
  2. Otherwise chroma-key against the background color sampled from the
     image corners (works great for flat studio-style backgrounds).

Usage:
    python scripts/prep_photo.py <photo> [out.png]

Output: grayscale PNG (default: source-prepped.png) ready for make_ascii_svg.py.
Only needed when the source photo changes — the daily workflow never runs this.
"""
import sys

import cv2
import numpy as np


def remove_bg_rembg(bgr):
    from rembg import remove  # optional dependency

    rgba = remove(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGBA))
    return rgba[:, :, 3]  # alpha mask


def remove_bg_chroma(bgr, tol=32.0):
    """Mask = pixels far (in Lab) from the corner-sampled background color."""
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    h, w = lab.shape[:2]
    ps = max(4, min(h, w) // 40)
    corners = np.vstack(
        [
            lab[:ps, :ps].reshape(-1, 3),
            lab[:ps, -ps:].reshape(-1, 3),
        ]
    )  # top corners only: subjects usually occupy the bottom edge
    bg = np.median(corners, axis=0)
    dist = np.linalg.norm(lab - bg, axis=2)
    mask = (dist > tol).astype(np.uint8) * 255
    # clean speckle and close small holes
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
    # keep only the largest connected component (the subject)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    if n > 1:
        biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        mask = np.where(labels == biggest, 255, 0).astype(np.uint8)
    mask = cv2.GaussianBlur(mask, (5, 5), 0)
    return mask


def autocrop_black(bgr, thresh=20):
    """Trim pure-black letterbox borders if present."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    nz = cv2.findNonZero((gray > thresh).astype(np.uint8))
    x, y, w, h = cv2.boundingRect(nz)
    return bgr[y : y + h, x : x + w]


def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "source-prepped.png"
    bgr = cv2.imread(src)
    if bgr is None:
        sys.exit(f"could not read {src}")
    bgr = autocrop_black(bgr)

    try:
        mask = remove_bg_rembg(bgr)
        how = "rembg"
    except Exception:
        mask = remove_bg_chroma(bgr)
        how = "chroma-key"

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # Compress subject highlights below true white so every subject pixel
    # prints at least a faint glyph — only the background stays blank.
    gray = gray.astype(np.float32) * 0.82

    a = mask.astype(np.float32) / 255.0
    prepped = (gray * a + 255.0 * (1.0 - a)).astype(np.uint8)

    cv2.imwrite(out, prepped)
    print(f"wrote {out} ({prepped.shape[1]}x{prepped.shape[0]}) via {how}")


if __name__ == "__main__":
    main()
