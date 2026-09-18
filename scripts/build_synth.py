#!/usr/bin/env python3
"""Build synthetic white-paper staged training images (healthy bulbs only).

Gap: the detector has never seen the deployment domain (bulbs on bright paper)
so it reads white-background skin as rot. These images teach exactly that:
clean bulb on bright paper == class `onion`.

 TRUTHFULNESS RULES baked in:
 - Cutouts come from TRAIN-split GT boxes only (never val, never holdout).
 - Only class-0 (healthy) boxes, area 2-60%, GrabCut fill in [0.25, 0.95].
 - Backgrounds are GENERATED paper (gradient + grain + soft shadows).
   Zero real pixels -> zero leakage risk vs the real holdout.
 - Output goes to TRAIN only. Val and ml/holdout_staged are untouched.
 - No defect classes are synthesized (shoot/rot fragments segment unreliably
   and training GT contains box-level label noise we must not amplify).

Usage:
    python scripts/build_synth.py --n 1500 --out ml/dataset_synth --seed 7
"""
import argparse
import random
from pathlib import Path

import cv2
import numpy as np


def paper_bg(rng, size=960):
    """Generated white-paper background: warm/cool tint, gradient, grain."""
    base = rng.integers(205, 245)
    tint = rng.integers(-8, 9, size=3)
    img = np.ones((size, size, 3), np.float32) * (base + tint)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    grad = ((xx / size - 0.5) * rng.uniform(-18, 18)
            + (yy / size - 0.5) * rng.uniform(-18, 18))
    img += grad[..., None]
    img += rng.normal(0, rng.uniform(1.5, 4.0), (size, size, 1))
    # a few soft shadow blotches
    for _ in range(rng.integers(0, 3)):
        cx, cy = rng.integers(0, size, 2)
        rad = rng.integers(120, 420)
        dark = rng.uniform(6, 22)
        d2 = ((xx - cx) ** 2 + (yy - cy) ** 2) / rad ** 2
        img -= dark * np.exp(-d2)[..., None]
    return np.clip(img, 0, 255).astype(np.uint8)


def red_bulb_ok(crop_bgr):
    """Deployment domain is RED onions. Reject white blobs (invisible on
    white paper), magenta skin fragments and tan skins by colour."""
    h, w = crop_bgr.shape[:2]
    c = crop_bgr[h // 4:3 * h // 4, w // 4:3 * w // 4]  # centre, avoid edges
    b, g, r = c[..., 0].mean(), c[..., 1].mean(), c[..., 2].mean()
    mx, mn = max(b, g, r), min(b, g, r)
    sat = (mx - mn) / (mx + 1e-6)
    return (r - g) > 22 and (r - b) > 12 and sat > 0.12 and r > 90


def extract_cutouts(train_img, train_lbl, rng, per_box_tries=1):
    """GrabCut bulb cutouts from healthy GT boxes. Returns [(rgba, cls)]."""
    im = cv2.imread(str(train_img))
    if im is None:
        return []
    H, W = im.shape[:2]
    out = []
    for ln in open(train_lbl):
        p = ln.split()
        if int(p[0]) != 0:
            continue
        _, xc, yc, w, h = map(float, p)
        if not (0.03 <= w * h <= 0.6):
            continue
        x1, y1 = max(0, int((xc - w / 2) * W)), max(0, int((yc - h / 2) * H))
        x2, y2 = min(W, int((xc + w / 2) * W)), min(H, int((yc + h / 2) * H))
        if x2 - x1 < 30 or y2 - y1 < 30:
            continue
        if not red_bulb_ok(im[y1:y2, x1:x2]):
            continue
        rect = (x1 + 4, y1 + 4, max(1, x2 - x1 - 8), max(1, y2 - y1 - 8))
        mask = np.zeros((H, W), np.uint8)
        bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
        try:
            cv2.grabCut(im, mask, rect, bgd, fgd, 4, cv2.GC_INIT_WITH_RECT)
        except Exception:
            continue
        m = np.where((mask == 2) | (mask == 0), 0, 1).astype(np.uint8)
        fill = m[y1:y2, x1:x2].mean()
        if not (0.30 <= fill <= 0.92):
            continue
        crop = im[y1:y2, x1:x2].copy()
        alpha = (m[y1:y2, x1:x2] * 255).astype(np.uint8)
        rgba = cv2.merge([*cv2.split(crop), alpha])
        out.append(rgba)
    return out


def paste_with_shadow(canvas, rgba, cx, cy, scale, angle, rng):
    """Paste cutout; returns tight bbox or None if fully out of frame."""
    h, w = rgba.shape[:2]
    nw, nh = max(8, int(w * scale)), max(8, int(h * scale))
    small = cv2.resize(rgba, (nw, nh), interpolation=cv2.INTER_AREA)
    M = cv2.getRotationMatrix2D((nw / 2, nh / 2), angle, 1.0)
    cos_a, sin_a = abs(M[0, 0]), abs(M[0, 1])
    bw, bh = int(nh * sin_a + nw * cos_a), int(nh * cos_a + nw * sin_a)
    M[0, 2] += bw / 2 - nw / 2
    M[1, 2] += bh / 2 - nh / 2
    rot = cv2.warpAffine(small, M, (bw, bh), flags=cv2.INTER_AREA,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    H, W = canvas.shape[:2]
    x0, y0 = int(cx - bw / 2), int(cy - bh / 2)
    # soft drop shadow
    sh = np.zeros((H, W), np.float32)
    sx0, sy0 = x0 + 10, y0 + 14
    cv2.ellipse(sh, (sx0 + bw // 2, sy0 + bh // 2),
                (bw // 2, bh // 3), 0, 0, 360, 0.35, -1)
    sh = cv2.GaussianBlur(sh, (31, 31), 0)
    for c in range(3):
        canvas[:, :, c] = canvas[:, :, c].astype(np.float32) * (1 - sh) + \
            (canvas[:, :, c].astype(np.float32) - 25 * sh)
    canvas[:] = np.clip(canvas, 0, 255)
    # composite
    x1c, y1c = max(0, x0), max(0, y0)
    x2c, y2c = min(W, x0 + bw), min(H, y0 + bh)
    if x2c <= x1c or y2c <= y1c:
        return None
    roi = rot[y1c - y0:y2c - y0, x1c - x0:x2c - x0]
    a = (roi[:, :, 3:4].astype(np.float32) / 255.0)
    canvas[y1c:y2c, x1c:x2c] = (
        roi[:, :, :3].astype(np.float32) * a
        + canvas[y1c:y2c, x1c:x2c].astype(np.float32) * (1 - a))
    # tight bbox of visible mask
    ys, xs = np.where(roi[:, :, 3] > 20)
    if len(xs) == 0:
        return None
    return (x1c + xs.min()) / W, (y1c + ys.min()) / H, \
        (x1c + xs.max()) / W, (y1c + ys.max()) / H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=1500)
    ap.add_argument('--out', type=Path, default=Path('ml/dataset_synth'))
    ap.add_argument('--seed', type=int, default=7)
    ap.add_argument('--from-pool', type=Path, default=None,
                    help='reuse cached cutouts instead of re-extracting')
    ap.add_argument('--drop', type=str, default='',
                    help='comma-separated cutout stems to blacklist, e.g. 00020,00021')
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    pyrng = random.Random(args.seed)

    print('[1/3] extracting healthy cutouts from TRAIN split...')
    pool = []
    lbs = sorted(Path('ml/dataset_v2/labels/train').glob('*.txt'))
    pyrng.shuffle(lbs)
    for lb in lbs:
        imgp = Path('ml/dataset_v2/images/train') / (lb.stem + '.jpg')
        if imgp.exists():
            pool.extend(extract_cutouts(imgp, lb, rng))
        if len(pool) >= 2400:
            break
    print(f'  cutouts kept: {len(pool)}')
    if len(pool) < 200:
        raise SystemExit('too few cutouts -- aborting')
    pooldir = args.out / 'cutouts'
    if args.from_pool:
        bad = {t.strip().lstrip('cut_') for t in args.drop.split(',') if t.strip()}
        pool = []
        for f in sorted(Path(args.from_pool).glob('*.png')):
            num = f.stem.split('_')[-1]
            if num in bad:
                continue
            rgba = cv2.imread(str(f), cv2.IMREAD_UNCHANGED)
            if rgba is not None:
                pool.append(rgba)
        print(f'  pool loaded from {args.from_pool}: {len(pool)}')
        pooldir = Path(args.from_pool)
    else:
        pooldir.mkdir(parents=True, exist_ok=True)
        for i, rgba in enumerate(pool):
            cv2.imwrite(str(pooldir / f'cut_{i:05d}.png'), rgba)
        print(f'  pool cached -> {pooldir}')

    print('[2/3] compositing staged images...')
    imgdir = args.out / 'images' / 'train'
    lbldir = args.out / 'labels' / 'train'
    imgdir.mkdir(parents=True, exist_ok=True)
    lbldir.mkdir(parents=True, exist_ok=True)
    for i in range(args.n):
        canvas = paper_bg(rng).astype(np.float32)
        k = int(pyrng.choice([1, 2, 2, 3, 3, 4, 5]))
        boxes = []
        for _ in range(k):
            rgba = pool[pyrng.randrange(len(pool))]
            frac = pyrng.choice([0.28, 0.35, 0.42, 0.5, 0.58])
            scale = frac * 960 / max(rgba.shape[:2])
            scale *= rng.uniform(0.9, 1.1)
            bb = paste_with_shadow(
                canvas, rgba,
                rng.uniform(80, 880), rng.uniform(80, 880),
                scale, rng.uniform(0, 360), rng)
            if bb is None:
                continue
            x1, y1, x2, y2 = bb
            if x2 - x1 < 0.03 or y2 - y1 < 0.03:
                continue
            boxes.append((x1, y1, x2, y2))
        if not boxes:
            continue
        cv2.imwrite(str(imgdir / f'synth_{i:05d}.jpg'), np.clip(canvas, 0, 255).astype(np.uint8))
        with open(lbldir / f'synth_{i:05d}.txt', 'w') as f:
            for x1, y1, x2, y2 in boxes:
                f.write(f'0 {(x1+x2)/2:.4f} {(y1+y2)/2:.4f} {x2-x1:.4f} {y2-y1:.4f}\n')
        if (i + 1) % 300 == 0:
            print(f'  {i+1}/{args.n}')
    print('[3/3] done ->', args.out)


if __name__ == '__main__':
    main()
