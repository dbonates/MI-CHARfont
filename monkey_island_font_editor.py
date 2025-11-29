#!/usr/bin/env python3
"""
Monkey Island Bitmap Font Editor
A specialized pixel editor for editing The Secret of Monkey Island bitmap font files.
Preserves the original color palette (2 tones of pink) without modification.
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QLabel, QPushButton, QFileDialog, QMessageBox, QGridLayout,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, QRect, pyqtSignal
from PyQt6.QtGui import (
    QImage, QPixmap, QPainter, QColor, QPen, QMouseEvent, QPaintEvent
)
from PIL import Image
import struct


class PixelEditorCanvas(QWidget):
    """Canvas widget for pixel-level editing with zoom and grid."""
    
    pixelChanged = pyqtSignal(int, int, int)  # x, y, color_index
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        self.original_palette = None
        self.zoom_level = 20  # pixels per pixel
        self.grid_enabled = True
        self.current_color_index = 1
        self.drawing = False
        self.char_height = 8  # Standard 8-pixel tall characters
        self.show_char_indices = True
        self.hover_y = -1
        
        self.setMinimumSize(200, 200)
        self.setMouseTracking(True)
        
    def load_image(self, image_path):
        """Load bitmap image and extract palette."""
        # Load with PIL to preserve palette
        pil_image = Image.open(image_path)
        
        # Store original palette
        if pil_image.mode == 'P':
            self.original_palette = pil_image.getpalette()
        
        # Convert to indexed color for Qt
        if pil_image.mode != 'P':
            pil_image = pil_image.convert('P')
        
        # Convert to QImage while preserving palette
        width, height = pil_image.size
        
        # Auto-detect character height based on bitmap height
        if height == 2048:  # 256 chars * 8
            self.char_height = 8
        elif height == 2259:  # 256 chars * 9
            self.char_height = 9
        elif height == 3390:  # 256 chars * 15
            self.char_height = 15
        elif height == 3584:  # 256 chars * 14
            self.char_height = 14
        else:
            # Calculate by dividing by 256 (extended ASCII)
            self.char_height = height // 256
            if self.char_height < 1:
                self.char_height = 8  # fallback
        
        self.image = QImage(width, height, QImage.Format.Format_Indexed8)
        
        # Set palette
        if self.original_palette:
            palette = self.original_palette[:768]  # RGB triplets
            for i in range(256):
                r = palette[i * 3] if i * 3 < len(palette) else 0
                g = palette[i * 3 + 1] if i * 3 + 1 < len(palette) else 0
                b = palette[i * 3 + 2] if i * 3 + 2 < len(palette) else 0
                self.image.setColor(i, QColor(r, g, b).rgb())
        
        # Copy pixel data
        pixel_data = pil_image.tobytes()
        for y in range(height):
            for x in range(width):
                idx = y * width + x
                if idx < len(pixel_data):
                    self.image.setPixel(x, y, pixel_data[idx])
        
        self.update_size()
        self.update()
        
    def update_size(self):
        """Update widget size based on image and zoom."""
        if self.image:
            new_size = QSize(
                self.image.width() * self.zoom_level,
                self.image.height() * self.zoom_level
            )
            self.setFixedSize(new_size)
            
    def paintEvent(self, event: QPaintEvent):
        """Draw the zoomed pixel grid."""
        if not self.image:
            return
            
        painter = QPainter(self)
        
        # Draw pixels
        for y in range(self.image.height()):
            for x in range(self.image.width()):
                color_idx = self.image.pixelIndex(x, y)
                color = QColor.fromRgb(self.image.color(color_idx))
                
                rect = QRect(
                    x * self.zoom_level,
                    y * self.zoom_level,
                    self.zoom_level,
                    self.zoom_level
                )
                painter.fillRect(rect, color)
        
        # Draw grid
        if self.grid_enabled:
            painter.setPen(QPen(QColor(100, 100, 100, 100), 1))
            for x in range(self.image.width() + 1):
                painter.drawLine(
                    x * self.zoom_level, 0,
                    x * self.zoom_level, self.image.height() * self.zoom_level
                )
            for y in range(self.image.height() + 1):
                painter.drawLine(
                    0, y * self.zoom_level,
                    self.image.width() * self.zoom_level, y * self.zoom_level
                )
        
        # Draw character index overlays
        if self.show_char_indices and self.char_height > 0:
            num_chars = self.image.height() // self.char_height
            for char_idx in range(num_chars):
                y_start = char_idx * self.char_height * self.zoom_level
                y_end = (char_idx + 1) * self.char_height * self.zoom_level
                
                # Highlight on hover
                is_hovered = (self.hover_y >= char_idx * self.char_height and 
                             self.hover_y < (char_idx + 1) * self.char_height)
                
                # Draw character boundary
                if char_idx > 0:
                    painter.setPen(QPen(QColor(255, 0, 0, 150) if is_hovered else QColor(0, 255, 0, 80), 2))
                    painter.drawLine(0, y_start, self.image.width() * self.zoom_level, y_start)
                
                # Draw character index label
                ascii_val = char_idx
                char_repr = chr(ascii_val) if 32 <= ascii_val < 127 else '·'
                label_text = f"#{char_idx} (ASCII {ascii_val}: '{char_repr}')"
                
                # Background for text
                painter.setPen(Qt.PenStyle.NoPen)
                if is_hovered:
                    painter.setBrush(QColor(255, 255, 0, 200))
                else:
                    painter.setBrush(QColor(0, 0, 0, 180))
                text_rect = QRect(5, y_start + 2, 300, 16)
                painter.drawRect(text_rect)
                
                # Text
                painter.setPen(QColor(255, 255, 255) if not is_hovered else QColor(0, 0, 0))
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label_text)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Start drawing."""
        if event.button() == Qt.MouseButton.LeftButton and self.image:
            self.drawing = True
            self.draw_pixel(event.pos())
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Continue drawing and track hover for character highlighting."""
        if self.image:
            # Update hover position
            old_hover = self.hover_y
            self.hover_y = event.pos().y() // self.zoom_level
            if old_hover != self.hover_y:
                self.update()
            
            # Draw if mouse is pressed
            if self.drawing:
                self.draw_pixel(event.pos())
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Stop drawing."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False
    
    def draw_pixel(self, pos):
        """Draw a pixel at the given position."""
        if not self.image:
            return
            
        x = pos.x() // self.zoom_level
        y = pos.y() // self.zoom_level
        
        if 0 <= x < self.image.width() and 0 <= y < self.image.height():
            self.image.setPixel(x, y, self.current_color_index)
            self.update()
            self.pixelChanged.emit(x, y, self.current_color_index)
    
    def set_zoom(self, zoom_level):
        """Set zoom level."""
        self.zoom_level = zoom_level
        self.update_size()
        self.update()
    
    def set_color(self, color_index):
        """Set current drawing color by palette index."""
        self.current_color_index = color_index
    
    def set_char_height(self, height):
        """Set the height of each character in pixels."""
        self.char_height = height
        self.update()
    
    def save_image(self, output_path):
        """Save image with original palette preserved."""
        if not self.image or not self.original_palette:
            return False
        
        # Convert QImage back to PIL
        width = self.image.width()
        height = self.image.height()
        
        # Create PIL image with palette
        pil_image = Image.new('P', (width, height))
        pil_image.putpalette(self.original_palette)
        
        # Copy pixel data
        pixels = []
        for y in range(height):
            for x in range(width):
                pixels.append(self.image.pixelIndex(x, y))
        
        pil_image.putdata(pixels)
        pil_image.save(output_path, 'BMP')
        return True


class CharacterThumbnail(QFrame):
    """Thumbnail widget displaying a character with its index number."""
    
    clicked = pyqtSignal(str, int)  # filepath, index
    
    def __init__(self, filepath, index, parent=None):
        super().__init__(parent)
        self.filepath = filepath
        self.index = index
        
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Index label
        index_label = QLabel(f"#{index}")
        index_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        index_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        
        # Image preview
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_preview()
        
        layout.addWidget(index_label)
        layout.addWidget(self.image_label)
        self.setLayout(layout)
        
    def load_preview(self):
        """Load and display thumbnail preview."""
        try:
            image = QImage(self.filepath)
            if not image.isNull():
                # Scale to reasonable size
                scaled = image.scaled(
                    50, 50,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.FastTransformation
                )
                self.image_label.setPixmap(QPixmap.fromImage(scaled))
        except Exception as e:
            self.image_label.setText("Error")
    
    def mousePressEvent(self, event: QMouseEvent):
        """Emit clicked signal."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.filepath, self.index)
        super().mousePressEvent(event)


class MonkeyIslandFontEditor(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.current_index = None
        self.workspace_dir = None
        
        self.setWindowTitle("Monkey Island Bitmap Font Editor")
        self.setGeometry(100, 100, 1200, 800)
        
        self.setup_ui()
        self.load_workspace()
        
    def setup_ui(self):
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Left panel: Character thumbnails
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(400)
        
        left_label = QLabel("Characters")
        left_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        left_layout.addWidget(left_label)
        
        # Scrollable grid of thumbnails
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.thumbnail_container = QWidget()
        self.thumbnail_layout = QGridLayout()
        self.thumbnail_layout.setSpacing(10)
        self.thumbnail_container.setLayout(self.thumbnail_layout)
        scroll.setWidget(self.thumbnail_container)
        left_layout.addWidget(scroll)
        
        # Right panel: Editor
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # Info label
        self.info_label = QLabel("Select a character to edit")
        self.info_label.setStyleSheet("font-size: 14px; padding: 10px;")
        right_layout.addWidget(self.info_label)
        
        # Canvas scroll area
        canvas_scroll = QScrollArea()
        canvas_scroll.setWidgetResizable(False)
        self.canvas = PixelEditorCanvas()
        canvas_scroll.setWidget(self.canvas)
        right_layout.addWidget(canvas_scroll)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Zoom controls
        zoom_out_btn = QPushButton("Zoom -")
        zoom_out_btn.clicked.connect(lambda: self.adjust_zoom(-5))
        controls_layout.addWidget(zoom_out_btn)
        
        zoom_in_btn = QPushButton("Zoom +")
        zoom_in_btn.clicked.connect(lambda: self.adjust_zoom(5))
        controls_layout.addWidget(zoom_in_btn)
        
        controls_layout.addStretch()
        
        # Color picker (palette indices)
        color_label = QLabel("Color Index:")
        controls_layout.addWidget(color_label)
        
        self.color0_btn = QPushButton("0")
        self.color0_btn.setFixedSize(40, 30)
        self.color0_btn.clicked.connect(lambda: self.set_color(0))
        controls_layout.addWidget(self.color0_btn)
        
        self.color1_btn = QPushButton("1")
        self.color1_btn.setFixedSize(40, 30)
        self.color1_btn.clicked.connect(lambda: self.set_color(1))
        controls_layout.addWidget(self.color1_btn)
        
        controls_layout.addStretch()
        
        # Save button
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_current)
        save_btn.setStyleSheet("font-weight: bold; padding: 5px 20px;")
        controls_layout.addWidget(save_btn)
        
        right_layout.addLayout(controls_layout)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, stretch=1)
        
    def load_workspace(self):
        """Load all character bitmaps from workspace directory."""
        # Get workspace directory
        self.workspace_dir = Path(__file__).parent
        
        # Find all char*.bmp files
        char_files = sorted(self.workspace_dir.glob("char*.bmp"))
        
        if not char_files:
            QMessageBox.warning(
                self,
                "No Files Found",
                "No character bitmap files (char*.bmp) found in workspace."
            )
            return
        
        # Create thumbnails
        cols = 3
        for i, filepath in enumerate(char_files):
            # Extract index from filename (char0001.bmp -> 1)
            filename = filepath.stem
            try:
                index = int(filename.replace("char", ""))
            except ValueError:
                index = i + 1
            
            thumbnail = CharacterThumbnail(str(filepath), index)
            thumbnail.clicked.connect(self.load_character)
            
            row = i // cols
            col = i % cols
            self.thumbnail_layout.addWidget(thumbnail, row, col)
    
    def load_character(self, filepath, index):
        """Load a character for editing."""
        self.current_file = filepath
        self.current_index = index
        
        try:
            self.canvas.load_image(filepath)
            # Calculate number of characters in this bitmap strip
            if self.canvas.image:
                num_chars = self.canvas.image.height() // self.canvas.char_height
                self.info_label.setText(
                    f"Editing: {Path(filepath).name} | "
                    f"Char Height: {self.canvas.char_height}px | "
                    f"Contains {num_chars} characters (ASCII 0-{num_chars-1}) | "
                    f"Hover over canvas to see character indices"
                )
            else:
                self.info_label.setText(f"Editing: Character #{index} - {Path(filepath).name}")
            self.update_color_buttons()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load character: {str(e)}"
            )
    
    def update_color_buttons(self):
        """Update color button appearances with actual palette colors."""
        if not self.canvas.image:
            return
        
        # Get colors from palette
        for i, btn in enumerate([self.color0_btn, self.color1_btn]):
            if i < self.canvas.image.colorCount():
                color = QColor.fromRgb(self.canvas.image.color(i))
                btn.setStyleSheet(
                    f"background-color: rgb({color.red()}, {color.green()}, {color.blue()});"
                )
    
    def set_color(self, color_index):
        """Set the current drawing color."""
        self.canvas.set_color(color_index)
    
    def adjust_zoom(self, delta):
        """Adjust zoom level."""
        new_zoom = max(5, min(50, self.canvas.zoom_level + delta))
        self.canvas.set_zoom(new_zoom)
    
    def save_current(self):
        """Save the currently edited character."""
        if not self.current_file:
            QMessageBox.warning(self, "No File", "No character is currently loaded.")
            return
        
        try:
            if self.canvas.save_image(self.current_file):
                QMessageBox.information(
                    self,
                    "Saved",
                    f"Character #{self.current_index} saved successfully!"
                )
                # Refresh thumbnail
                self.load_workspace()
            else:
                raise Exception("Save failed")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save character: {str(e)}"
            )


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern cross-platform style
    
    window = MonkeyIslandFontEditor()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
