#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Product image pipeline: square, WebP, predictable size.

Two decisions are baked in because they were made the hard way:

1. WebP at quality 84, method 6. Below 84 artefacts show on fabric texture;
   above 6 the encoder spends seconds for kilobytes.

2. There is deliberately NO mirror-pad option. Reflecting an edge to fill a
   square makes the product look like it has a crease or a doubled seam, and
   buyers inspecting surfaces read that as a manufacturing defect. Use
   cover-crop, or contain-fit on a sampled background colour.

Usage:
    python image_pipeline.py in.jpg out.webp --size 800
    python image_pipeline.py in.jpg out.webp --size 800 --fit contain --bg auto
    python image_pipeline.py --dir ./photos --out-dir ./webp --size 800 --quality 84

Requires Pillow:  pip install Pillow
"""
import argparse
import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install Pillow")

SUPPORTED = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp")


def sample_background(image):
    """Average the four corner pixels, so contain-fit does not sit on white
    when the studio background is warm grey."""
    width, height = image.size
    corners = [
        image.getpixel((0, 0)),
        image.getpixel((width - 1, 0)),
        image.getpixel((0, height - 1)),
        image.getpixel((width - 1, height - 1)),
    ]
    if len(corners[0]) >= 3:
        channels = len(corners[0])
        return tuple(sum(c[i] for c in corners) // len(corners) for i in range(channels))
    return tuple(sum(corners) // len(corners) for _ in range(3))


def fit_cover(image, size):
    """Centre crop to square, then resize. Crops content; use when the subject
    is centred and margin does not matter."""
    width, height = image.size
    edge = min(width, height)
    left = (width - edge) // 2
    top = (height - edge) // 2
    return image.crop((left, top, left + edge, top + edge)).resize((size, size), Image.LANCZOS)


def fit_contain(image, size, background):
    """Scale to fit inside the square, pad the rest with a flat colour.
    Keeps the whole product visible."""
    copy = image.copy()
    copy.thumbnail((size, size), Image.LANCZOS)
    canvas = Image.new(copy.mode, (size, size), background)
    offset = ((size - copy.size[0]) // 2, (size - copy.size[1]) // 2)
    if copy.mode == "RGBA" and canvas.mode != "RGBA":
        canvas = canvas.convert("RGBA")
        canvas.paste(copy, offset, copy)
    else:
        canvas.paste(copy, offset)
    return canvas


def convert(source, target, size, fit, quality, method, background_arg):
    with Image.open(source) as opened:
        image = opened.convert("RGB") if opened.mode not in ("RGB", "RGBA") else opened.copy()

        if background_arg == "auto":
            background = sample_background(image)
        elif background_arg == "white":
            background = (255, 255, 255)
        else:
            background = tuple(int(part) for part in background_arg.split(","))
            if len(background) == 3:
                background = background + (255,)

        if fit == "cover":
            output = fit_cover(image, size)
        else:
            if image.mode == "RGBA":
                background = tuple(background[:3]) + (255,)
            output = fit_contain(image, size, background)

        output.save(target, "WEBP", quality=quality, method=method)
        return output.size, os.path.getsize(target)


def main():
    ap = argparse.ArgumentParser(description="Square product images to WebP.")
    ap.add_argument("source", nargs="?", help="input image")
    ap.add_argument("target", nargs="?", help="output .webp path")
    ap.add_argument("--dir", help="process every image in this directory")
    ap.add_argument("--out-dir", help="output directory when using --dir")
    ap.add_argument("--size", type=int, default=800, help="square edge in pixels (default 800)")
    ap.add_argument("--fit", choices=["cover", "contain"], default="cover")
    ap.add_argument("--bg", default="auto",
                    help="contain-fit background: auto (corner sample), white, or R,G,B")
    ap.add_argument("--quality", type=int, default=84)
    ap.add_argument("--method", type=int, default=6, help="WebP encoder effort 0-6")
    args = ap.parse_args()

    if args.dir:
        out_dir = args.out_dir or args.dir
        os.makedirs(out_dir, exist_ok=True)
        files = sorted(f for f in os.listdir(args.dir) if f.lower().endswith(SUPPORTED))
        if not files:
            sys.exit("no supported images in %s" % args.dir)
        for name in files:
            source = os.path.join(args.dir, name)
            target = os.path.join(out_dir, os.path.splitext(name)[0] + ".webp")
            dims, written = convert(source, target, args.size, args.fit,
                                    args.quality, args.method, args.bg)
            print("%-40s %dx%d  %5.1f KB" % (name, dims[0], dims[1], written / 1024.0))
        return

    if not args.source or not args.target:
        sys.exit("pass source and target, or use --dir")

    dims, written = convert(args.source, args.target, args.size, args.fit,
                            args.quality, args.method, args.bg)
    print("%s -> %s  %dx%d  %.1f KB"
          % (args.source, args.target, dims[0], dims[1], written / 1024.0))
    if written > 150 * 1024:
        print("warning: over 150 KB. try --quality 80 or check the source resolution.")


if __name__ == "__main__":
    main()
