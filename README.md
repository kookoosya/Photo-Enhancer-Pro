# Photo Enhancer Pro

**Production-ready offline desktop application for automatic photo enhancement in iPhone Pro style.**

Photo Enhancer Pro automatically processes folders or ZIP archives of photos, applying a natural enhancement pipeline inspired by iPhone 15 Pro / iPhone 16 Pro photography. No manual editing. No cloud. No AI hallucination.

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![Offline](https://img.shields.io/badge/Offline-Yes-success)

---

## Features

- **Batch processing** — folders or ZIP archives with 1000+ photos
- **iPhone Pro style** — natural look, no HDR oversaturation, no fake AI look
- **20-step pipeline** — exposure, shadows, tone mapping, dehaze, regional enhancements
- **Smart segmentation** — sky, water, grass, skin protection via color heuristics + optional YOLO
- **EXIF preservation** — orientation, metadata kept when possible
- **7 presets** — iPhone Pro, DSLR, Landscape, Portrait, Nature, Instagram, Cinematic
- **Quality tools** — duplicate detection, blur detection, best photo ranking
- **Modern Gradio UI** — dark theme, drag & drop, live preview, progress bar, ETA
- **CLI mode** — full headless batch processing
- **GPU support** — CUDA when available, CPU fallback
- **Cross-platform** — Windows 11 first, Linux and macOS supported

---

## Screenshots

```
┌─────────────────────────────────────────────────────────────┐
│              Photo Enhancer Pro                             │
│   Automatic iPhone Pro style enhancement — offline          │
├──────────────────┬──────────────────────────────────────────┤
│  Input Folder    │  Progress ████████████░░░░  75%          │
│  Input ZIP       │  ETA: 2m 15s                             │
│  Output Folder   │  ┌─────────┐  ┌─────────┐                │
│  Preset: iPhone  │  │ Before  │  │ After   │                │
│  [Start]         │  └─────────┘  └─────────┘                │
└──────────────────┴──────────────────────────────────────────┘
```

---

## Quick Start

### Requirements

- Python 3.12 or higher
- 4 GB RAM minimum (8 GB recommended for large batches)
- Optional: NVIDIA GPU with CUDA for acceleration

### Installation

```bash
git clone https://github.com/gmxreply/Photo-Enhancer-Pro.git
cd Photo-Enhancer-Pro
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### Run GUI

```bash
python main.py
```

Opens Gradio UI at `http://127.0.0.1:7860`

### Run CLI

```bash
python main.py --cli "C:\Photos\Vacation" -p iphone_pro -o "C:\Photos\Output"
```

```bash
python cli.py "C:\Photos\Vacation.zip" --preset nature --no-zip
```

---

## Usage

### Input

Drop a **folder** or **ZIP archive** containing:

| Format | Support |
|--------|---------|
| JPG / JPEG | ✅ |
| PNG | ✅ |
| WEBP | ✅ |
| HEIC | ✅ |
| TIFF | ✅ |

### Output

```
Vacation/
  IMG_0001.jpg
  IMG_0002.jpg

→ Vacation_Enhanced/
    IMG_0001.jpg
    IMG_0002.jpg
  + Vacation_Enhanced.zip
```

Original resolution, filenames, and EXIF preserved.

---

## Enhancement Pipeline

Every image passes through 20 steps:

1. Read EXIF
2. Auto orientation
3. Lens distortion correction
4. Auto white balance
5. Auto exposure
6. Highlight recovery
7. Shadow lifting
8. Tone mapping
9. Local contrast enhancement
10. Micro contrast
11. Texture enhancement
12. Dehaze
13. Color balancing
14. Skin tone protection
15. Sky protection & enhancement
16. Grass color protection
17. Blue water enhancement
18. Noise reduction
19. Smart sharpening
20. JPEG optimization

**Principle:** Never generate new pixels. Never hallucinate. Only improve the original.

---

## Presets

| Preset | Description |
|--------|-------------|
| **iPhone Pro** (default) | Natural iPhone 15/16 Pro look |
| DSLR | Higher contrast, professional |
| Landscape | Enhanced skies and terrain |
| Portrait | Skin-protected, soft tones |
| Nature | Rich greens and blues |
| Instagram | Vibrant social media style |
| Cinematic | Moody, film-like |

### iPhone Pro Values

| Parameter | Value |
|-----------|-------|
| Exposure | +0.20 |
| Contrast | +10 |
| Highlights | -35 |
| Shadows | +40 |
| Texture | +10 |
| Clarity | +5 |
| Dehaze | +5 |
| Vibrance | +15 |
| Saturation | +3 |
| Sharpen | 35 |
| Noise Reduction | 10 |

---

## Project Structure

```
photo-enhancer-pro/
├── main.py              # Entry point
├── gui.py               # Gradio UI
├── cli.py               # CLI interface
├── config.py            # Configuration
├── config.json          # JSON settings
├── pipeline.py          # Batch processing
├── enhancer.py          # Core enhancement engine
├── styles/              # Enhancement presets
├── segmentation/        # Scene detection
├── noise/               # Noise reduction
├── upscale/             # Optional upscaling
├── utils/               # File, EXIF, quality tools
├── models/              # Optional AI weights
├── tests/               # Test suite
├── logs/                # Application logs
└── .github/workflows/   # CI/CD
```

---

## Configuration

Edit `config.json`:

```json
{
  "default_preset": "iphone_pro",
  "processing": {
    "max_workers": 4,
    "use_gpu": true,
    "jpeg_quality": 95
  },
  "features": {
    "keep_exif": true,
    "create_zip": true,
    "duplicate_detection": true
  }
}
```

---

## Optional AI Models

The app works fully offline without AI models. For enhanced detection, place weights in `models/`:

| Model | File | Purpose |
|-------|------|---------|
| YOLO11 | `yolo11n.pt` | People, boats, animals |
| Real-ESRGAN | `RealESRGAN_x4plus.pth` | AI upscaling |

Enable in `config.json`:

```json
{
  "segmentation": { "use_yolo": true },
  "upscale": { "enabled": true }
}
```

---

## Development

```bash
pip install pytest ruff
ruff check .
pytest tests/ -v
```

---

## Roadmap

- [x] Core 20-step enhancement pipeline
- [x] Gradio dark UI with live preview
- [x] CLI batch processing
- [x] 7 enhancement presets
- [x] EXIF preservation
- [x] ZIP input/output
- [x] Duplicate & blur detection
- [x] GitHub Actions CI
- [x] Windows executable build
- [ ] Full SAM2 integration
- [ ] Real-ESRGAN native upscaling
- [ ] OpenImageDenoise integration
- [ ] Before/After slider in UI
- [ ] macOS .app bundle
- [ ] Linux AppImage

---

## FAQ

**Does this work offline?**  
Yes. 100% offline. No internet required after installation.

**Does it use generative AI?**  
No. It uses traditional computer vision — OpenCV, color science, and optional detection models. It never redraws or hallucinates pixels.

**Will it look like fake AI enhancement?**  
No. The iPhone Pro preset is tuned for natural results — no oversaturation, no HDR look, no cartoon effect.

**How many photos can it process?**  
1000+ photos in batch mode with multiprocessing.

**Does it support HEIC?**  
Yes, via `pillow-heif`.

**GPU required?**  
No. CPU works. GPU accelerates optional AI features when CUDA is available.

---

## License

MIT License — see [LICENSE](LICENSE).

---

## Author

Photo Enhancer Pro Team
