# Monkey Island Bitmap Font Editor

A specialized pixel editor for editing The Secret of Monkey Island bitmap font files. Built with PyQt6 to preserve the original color palette without modification.

## Features

- **Character Grid View**: Displays all character bitmaps with index numbers (starting from 1)
- **Pixel-Level Editing**: Zoom in and edit individual pixels with a grid overlay
- **Palette Preservation**: Maintains the original 2-tone pink color palette from the game
- **Easy Navigation**: Click any character thumbnail to load it for editing
- **Save Functionality**: Overwrites the original BMP files while preserving the palette

## Installation

1. Ensure Python 3.x is installed
2. Install dependencies:
```bash
pip install PyQt6 Pillow
```

Or use the virtual environment already configured in this directory:
```bash
source .venv/bin/activate
```

## Usage

Run the editor from the terminal:
```bash
python monkey_island_font_editor.py
```

Or with the virtual environment:
```bash
.venv/bin/python monkey_island_font_editor.py
```

## How to Edit

1. **Select a Character**: Click on any character thumbnail on the left panel
2. **Adjust Zoom**: Use "Zoom +" and "Zoom -" buttons to change the pixel size
3. **Choose Color**: Click color index buttons (0 or 1) to select the drawing color
4. **Draw Pixels**: Click and drag on the canvas to paint pixels
5. **Save**: Click "Save" button to write changes to the bitmap file

## Technical Details

- Reads 8-bit indexed BMP files
- Preserves original palette data structure
- Each character is displayed with its sequential index number
- Files are named as `char####.bmp` (e.g., char0001.bmp, char0002.bmp)

## Notes

- The editor automatically detects all `char*.bmp` files in the current directory
- Original files are overwritten when saving - make backups if needed
- The color palette is preserved byte-for-byte from the original game files
