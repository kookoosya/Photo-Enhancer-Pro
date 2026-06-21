# Changelog

## [2.0.0] - 2026-06-21

### Added
- Native PySide6 (Qt6) desktop application — no browser, no localhost
- Professional dark UI with splash screen, toolbar, menus, status bar
- Before/After compare slider with zoom and pan
- Drag & drop support for folders, ZIP, single and multiple images
- Modular `ProcessingStage` architecture with configurable pipeline
- Dependency injection via `ServiceContainer`
- `BatchController` and `PipelineWorker` (QThread) for non-blocking UI
- Parallel batch processing with `ThreadPoolExecutor`
- Recent projects history
- GPU/RAM live monitor in status bar
- PyInstaller spec for `Photo Enhancer Pro.exe`
- Inno Setup script for `Photo Enhancer Pro Setup.exe`
- Integration, GUI, stage, and performance tests (23 total)
- `DEVELOPMENT_REPORT.md` with full migration documentation

### Changed
- **BREAKING:** Removed Gradio — application is now native Qt desktop
- Improved sky detection (gradient + morphology)
- Improved highlight/shadow recovery (smooth rolloff curves)
- Edge-aware sharpening with skin protection
- Weighted auto white balance with highlight protection
- Enhanced regional sky/grass/water adjustments

### Removed
- `gui.py` (Gradio UI)
- Gradio dependency from requirements

## [1.0.0] - 2026-06-20

### Added
- Initial release with Gradio UI
- 20-step enhancement pipeline
- 7 presets (iPhone Pro default)
- CLI batch processing
- EXIF preservation, ZIP I/O
- Duplicate/blur detection
