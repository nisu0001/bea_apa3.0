# dialogs/settings_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QSpinBox, QCheckBox, QComboBox, QPushButton, QMessageBox, QLabel,
    QSlider, QTabWidget, QWidget, QScrollArea, QFrame, QSizePolicy, QGridLayout, QApplication,
    QListWidget, QListWidgetItem, QStackedWidget, QLineEdit
)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QTimer, QMargins, QRectF, QEvent, pyqtSignal, pyqtProperty
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, pyqtSignal
from PyQt5.QtGui import QIcon, QColor, QFont, QPixmap, QPainter, QPainterPath, QBrush, QPen
from config import MODERN_COLORS, SOUND_OPTIONS
from utils import resource_path

class MacOSSlider(QWidget):
    """macOS-style slider with value display and visual enhancements"""
    valueChanged = pyqtSignal(int)
    
    def __init__(self, min_value, max_value, current_value, parent=None, slider_height=22):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(12)
        
        # Create slider component
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(min_value, max_value)
        self.slider.setValue(current_value)
        self.slider.setFixedHeight(slider_height)  # Customizable height
        
        # Install event filter to handle mouse events
        self.slider.installEventFilter(self)
        
        # Create value display component
        self.value_display = QLineEdit()
        self.value_display.setText(str(current_value))
        self.value_display.setFixedWidth(50)
        self.value_display.setAlignment(Qt.AlignCenter)
        self.value_display.setObjectName("valueInput")
        
        # Validators
        # Only allow numbers in range
        self.value_display.textChanged.connect(self._validate_input)
        
        # Connect components
        self.slider.valueChanged.connect(self._update_text_value)
        self.value_display.editingFinished.connect(self._update_slider_value)
        self.slider.valueChanged.connect(self.valueChanged.emit)
        
        # Add components to layout
        self.layout.addWidget(self.slider, 1)
        self.layout.addWidget(self.value_display, 0)
    
    def _validate_input(self):
        """Validate text input to ensure it's a valid number"""
        text = self.value_display.text()
        try:
            value = int(text)
            if value < self.slider.minimum() or value > self.slider.maximum():
                # Out of range - revert to current slider value
                self.value_display.setText(str(self.slider.value()))
        except ValueError:
            # Not a number - revert to current slider value
            self.value_display.setText(str(self.slider.value()))
    
    def _update_text_value(self, value):
        """Update text field when slider changes"""
        self.value_display.setText(str(value))
    
    def _update_slider_value(self):
        """Update slider when text field changes"""
        try:
            value = int(self.value_display.text())
            self.slider.setValue(value)
        except ValueError:
            # Reset to current slider value if text isn't a valid number
            self.value_display.setText(str(self.slider.value()))
    
    def value(self):
        """Get current slider value"""
        return self.slider.value()
    
    def setValue(self, value):
        """Set slider value"""
        self.slider.setValue(value)
        
    def eventFilter(self, obj, event):
        """Handle slider events for better interactivity"""
        if obj is self.slider:
            # Change cursor when hovering over the slider
            if event.type() == event.Enter:
                self.setCursor(Qt.PointingHandCursor)
                return True
            elif event.type() == event.Leave:
                self.setCursor(Qt.ArrowCursor)
                return True
                
        # Standard event processing
        return super().eventFilter(obj, event)


class MacOSToggle(QCheckBox):
    """macOS-style toggle switch with minimal drawing code for maximum performance"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 24)
        
        # No animation - animations were causing lag
        self._animation_active = False
        self._last_click_time = 0
        
        # Set style
        self.setCursor(Qt.PointingHandCursor)
        
        # Directly handle paint event without complex animations
    
    def paintEvent(self, event):
        """Simple painting for the toggle without complex animations"""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        # Simple colors - no gradients or complex effects
        if self.isEnabled():
            track_color = QColor("#DDDDDD") if not self.isChecked() else QColor("#34C759")
            thumb_color = QColor("#FFFFFF")
        else:
            track_color = QColor("#E9E9E9") if not self.isChecked() else QColor("#98D4A9")
            thumb_color = QColor("#F5F5F5")
        
        # Fixed track dimensions
        track_height = 14
        track_width = self.width() - 4
        track_radius = track_height / 2
        
        # Draw track with simple drawing
        track_rect = QRectF(2, (self.height() - track_height) // 2, track_width, track_height)
        p.setPen(Qt.NoPen)
        p.setBrush(track_color)
        p.drawRoundedRect(track_rect, track_radius, track_radius)
        
        # Thumb position - direct calculation, no animation
        thumb_radius = 10
        thumb_x = self.width() - thumb_radius * 2 - 4 if self.isChecked() else 4
        thumb_y = (self.height() - thumb_radius * 2) // 2
        
        # Draw thumb without any effects
        thumb_rect = QRectF(thumb_x, thumb_y, thumb_radius * 2, thumb_radius * 2)
        p.setBrush(thumb_color)
        p.drawEllipse(thumb_rect)
        
        p.end()
    
    def mousePressEvent(self, event):
        """Handle mouse press with our own implementation"""
        if event.button() == Qt.LeftButton:
            # Toggle state manually
            self.setChecked(not self.isChecked())
            # Emit clicked signal
            self.clicked.emit(self.isChecked())
            # Emit toggled signal
            self.toggled.emit(self.isChecked())
            # Update immediately
            self.update()
            event.accept()


class CustomTitleBar(QWidget):
    """macOS-style custom title bar with traffic light controls"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_dialog = parent
        self.setFixedHeight(38)  # Standard macOS title bar height
        self.setObjectName("titleBar")
        
        # Ensure the widget is not transparent and has a solid background
        self.setAutoFillBackground(True)  # This helps ensure the background is painted
        
        # Mouse tracking for window dragging
        self.pressing = False
        self.start_point = None
        self.setMouseTracking(True)
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        
        # Window title - moved to the left side
        self.title_label = QLabel("Settings")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setObjectName("windowTitle")
        
        # Window controls (traffic lights) - Moved to the right
        control_container = QWidget()
        control_container.setObjectName("controlContainer")
        control_container.setFixedWidth(70)  # Fixed width for control area
        
        controls_layout = QHBoxLayout(control_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)
        
        self.btn_close = QPushButton()
        self.btn_minimize = QPushButton()
        self.btn_maximize = QPushButton()
        
        for btn in [self.btn_close, self.btn_minimize, self.btn_maximize]:
            btn.setFixedSize(12, 12)
            btn.setObjectName("windowButton")
        
        self.btn_maximize.setObjectName("maximizeButton")
        self.btn_minimize.setObjectName("minimizeButton")
        self.btn_close.setObjectName("closeButton")
        
        self.btn_close.clicked.connect(self.parent_dialog.close)
        self.btn_minimize.clicked.connect(self.parent_dialog.showMinimized)
        self.btn_maximize.clicked.connect(self.toggle_maximize)
        
        # Add buttons to layout
        controls_layout.addWidget(self.btn_minimize)
        controls_layout.addWidget(self.btn_maximize)
        controls_layout.addWidget(self.btn_close)
        
        # Add to layout - reversed order for right alignment
        layout.addWidget(self.title_label, 1)  # Title in center 
        layout.addStretch(1)  # Push controls to the right
        layout.addWidget(control_container)  # Controls on right
    
    def toggle_maximize(self):
        """Toggle between maximized and normal window state"""
        if self.parent_dialog.isMaximized():
            self.parent_dialog.showNormal()
        else:
            self.parent_dialog.showMaximized()
    
    def mousePressEvent(self, event):
        """Begin tracking for window movement"""
        if event.button() == Qt.LeftButton:
            self.pressing = True
            self.start_point = event.globalPos() - self.parent_dialog.frameGeometry().topLeft()
    
    def mouseReleaseEvent(self, event):
        """End tracking for window movement"""
        self.pressing = False
        self.setCursor(Qt.ArrowCursor)
    
    def mouseMoveEvent(self, event):
        """Move window when dragging title bar"""
        if self.pressing and not self.parent_dialog.isMaximized():
            self.parent_dialog.move(event.globalPos() - self.start_point)
            self.setCursor(Qt.ClosedHandCursor)

class ThemePreview(QWidget):
    """Widget to preview theme appearance"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("themePreview")
        self.setMinimumHeight(200)  # Taller preview
        self.current_theme = "dark"  # Default theme
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(12)
        
        # Title
        self.title = QLabel("Theme Preview")
        self.title.setObjectName("previewTitle")
        self.title.setAlignment(Qt.AlignCenter)
        
        # Components preview section
        self.components = QWidget()
        self.components_layout = QHBoxLayout(self.components)
        self.components_layout.setContentsMargins(0, 0, 0, 0)
        self.components_layout.setSpacing(16)
        
        # Left column - Controls
        self.controls = QWidget()
        self.controls_layout = QVBoxLayout(self.controls)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        self.controls_layout.setSpacing(10)
        
        # Button examples
        self.primary_btn = QPushButton("Primary Button")
        self.primary_btn.setObjectName("primaryButton")
        
        self.secondary_btn = QPushButton("Secondary Button")
        self.secondary_btn.setObjectName("secondaryButton")
        
        # Toggle example
        self.toggle_container = QWidget()
        self.toggle_layout = QHBoxLayout(self.toggle_container)
        self.toggle_layout.setContentsMargins(0, 0, 0, 0)
        self.toggle_layout.setSpacing(8)
        
        self.toggle_label = QLabel("Toggle:")
        self.toggle = MacOSToggle()
        self.toggle.setChecked(True)
        
        self.toggle_layout.addWidget(self.toggle_label)
        self.toggle_layout.addWidget(self.toggle)
        self.toggle_layout.addStretch()
        
        # Slider example
        self.slider_container = QWidget()
        self.slider_layout = QHBoxLayout(self.slider_container)
        self.slider_layout.setContentsMargins(0, 0, 0, 0)
        self.slider_layout.setSpacing(8)
        
        self.slider_label = QLabel("Slider:")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setValue(70)
        
        self.slider_layout.addWidget(self.slider_label)
        self.slider_layout.addWidget(self.slider, 1)
        
        # Add all controls
        self.controls_layout.addWidget(self.primary_btn)
        self.controls_layout.addWidget(self.secondary_btn)
        self.controls_layout.addWidget(self.toggle_container)
        self.controls_layout.addWidget(self.slider_container)
        
        # Right column - Text and color samples
        self.text_samples = QWidget()
        self.text_layout = QVBoxLayout(self.text_samples)
        self.text_layout.setContentsMargins(0, 0, 0, 0)
        self.text_layout.setSpacing(8)
        
        # Text samples
        self.heading = QLabel("Heading Text")
        self.heading.setObjectName("previewHeading")
        
        self.body = QLabel("This is how body text will appear with this theme. It demonstrates the main text color.")
        self.body.setObjectName("previewBody")
        self.body.setWordWrap(True)
        
        self.secondary_text = QLabel("Secondary and helper text will appear like this.")
        self.secondary_text.setObjectName("previewSecondary")
        
        # Color swatches
        self.swatches = QWidget()
        self.swatches_layout = QHBoxLayout(self.swatches)
        self.swatches_layout.setContentsMargins(0, 0, 0, 0)
        self.swatches_layout.setSpacing(8)
        
        # Create color swatches
        self.primary_swatch = QFrame()
        self.primary_swatch.setObjectName("primarySwatch")
        self.primary_swatch.setFixedSize(20, 20)
        
        self.accent_swatch = QFrame()
        self.accent_swatch.setObjectName("accentSwatch")
        self.accent_swatch.setFixedSize(20, 20)
        
        self.warning_swatch = QFrame()
        self.warning_swatch.setObjectName("warningSwatch")
        self.warning_swatch.setFixedSize(20, 20)
        
        self.success_swatch = QFrame()
        self.success_swatch.setObjectName("successSwatch")
        self.success_swatch.setFixedSize(20, 20)
        
        # Add swatches with labels
        self.swatches_layout.addWidget(QLabel("Colors:"))
        self.swatches_layout.addWidget(self.primary_swatch)
        self.swatches_layout.addWidget(self.accent_swatch)
        self.swatches_layout.addWidget(self.warning_swatch)
        self.swatches_layout.addWidget(self.success_swatch)
        self.swatches_layout.addStretch()
        
        # Add all text elements
        self.text_layout.addWidget(self.heading)
        self.text_layout.addWidget(self.body)
        self.text_layout.addWidget(self.secondary_text)
        self.text_layout.addWidget(self.swatches)
        self.text_layout.addStretch()
        
        # Add columns to components layout
        self.components_layout.addWidget(self.controls, 1)
        self.components_layout.addWidget(self.text_samples, 1)
        
        # Add all to main layout
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.components)
    
    def updateStyles(self, theme_name):
        """Update the preview styles based on the theme"""
        # Store the theme name
        self.current_theme = theme_name.lower()
        
        # Get theme colors
        theme = MODERN_COLORS.get(self.current_theme, MODERN_COLORS.get("dark"))
        
        # Apply theme to preview
        self.setStyleSheet(self.generatePreviewStylesheet(theme))
        
        # Force update
        self.update()
    
    def generatePreviewStylesheet(self, theme):
        """Generate stylesheet for the preview based on the theme"""
        background_color = theme.get('background', '#1E1E1E')
        surface_color = theme.get('surface', '#262626')
        text_color = theme.get('text', '#FFFFFF')
        text_secondary_color = theme.get('text_secondary', '#BBBBBB')
        primary_color = theme.get('primary', '#0A84FF')
        accent_color = theme.get('accent', '#FF453A')
        warning_color = theme.get('warning', '#FF9F0A')
        success_color = theme.get('success', '#30D158')
        
        return f"""
            QWidget#themePreview {{
                background-color: {background_color};
                border-radius: 8px;
                border: 1px solid {surface_color};
            }}
            
            QLabel {{
                color: {text_color};
            }}
            
            QLabel#previewTitle {{
                font-size: 16px;
                font-weight: bold;
            }}
            
            QLabel#previewHeading {{
                font-size: 18px;
                font-weight: bold;
            }}
            
            QLabel#previewBody {{
                font-size: 14px;
            }}
            
            QLabel#previewSecondary {{
                color: {text_secondary_color};
                font-size: 12px;
            }}
            
            QPushButton#primaryButton {{
                background-color: {primary_color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            
            QPushButton#secondaryButton {{
                background-color: transparent;
                color: {text_color};
                border: 1px solid {text_secondary_color};
                border-radius: 6px;
                padding: 8px 16px;
            }}
            
            QFrame#primarySwatch {{
                background-color: {primary_color};
                border-radius: 4px;
            }}
            
            QFrame#accentSwatch {{
                background-color: {accent_color};
                border-radius: 4px;
            }}
            
            QFrame#warningSwatch {{
                background-color: {warning_color};
                border-radius: 4px;
            }}
            
            QFrame#successSwatch {{
                background-color: {success_color};
                border-radius: 4px;
            }}
        """


class SettingsNavItem(QWidget):
    """Custom navigation item with icon and text for settings sidebar"""
    def __init__(self, icon_path, text, index, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(16, 10, 16, 10)  # Increased padding for modern look
        self.layout.setSpacing(16)  # More space between icon and text
        
        # Icon
        self.icon_label = QLabel()
        # Use text fallback instead of trying to load pixmap
        if text == "General":
            self.icon_label.setText("⚙️")
        elif text == "Appearance":
            self.icon_label.setText("🎨")
        elif text == "Sound":
            self.icon_label.setText("🔊")
        elif text == "Data":
            self.icon_label.setText("📊")
        else:
            self.icon_label.setText("•")
        
        self.icon_label.setFixedSize(24, 24)  # Larger icons
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setObjectName("navIcon")
        
        # Text
        self.text_label = QLabel(text)
        self.text_label.setObjectName("navItemText")
        
        # Add to layout
        self.layout.addWidget(self.icon_label)
        self.layout.addWidget(self.text_label, 1)
        
        # Set index property for identification
        self.setProperty("index", index)
        
        # Make selectable appearance
        self.setObjectName("navItem")
        
        # Selection indicator - vertical bar on left
        self.indicator = QWidget(self)
        self.indicator.setObjectName("selectionIndicator")
        self.indicator.setFixedWidth(3)  # Thin indicator
        self.indicator.setVisible(False)
        
        # Handle size and position
        self.updateIndicator()
        
        # Install event filter for hover animations
        self.installEventFilter(self)
        
        # Animation for selection indicator
        self.indicator_animation = QPropertyAnimation(self.indicator, b"geometry")
        self.indicator_animation.setDuration(150)  # Quick animation
        self.indicator_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Hover animation properties
        self._hover_opacity = 0
        self._hover_animation = QPropertyAnimation(self, b"hoverOpacity")
        self._hover_animation.setDuration(150)
        
    def updateIndicator(self):
        """Update the position and size of the selection indicator"""
        self.indicator.setFixedHeight(self.height() - 12)  # Slightly shorter than parent
        self.indicator.move(0, 6)  # Center vertically
    
    def resizeEvent(self, event):
        """Handle resize to update indicator position"""
        super().resizeEvent(event)
        self.updateIndicator()
    
    def setSelected(self, selected):
        """Update appearance when selected/deselected with animation"""
        if selected:
            self.setProperty("selected", True)
            self.indicator.setVisible(True)
            
            # Animate indicator appearance
            start_geom = self.indicator.geometry()
            end_geom = start_geom
            self.indicator_animation.setStartValue(QRectF(start_geom.x() - 5, start_geom.y(), 
                                                         start_geom.width(), start_geom.height()))
            self.indicator_animation.setEndValue(QRectF(end_geom))
            self.indicator_animation.start()
        else:
            self.setProperty("selected", False)
            self.indicator.setVisible(False)
        
        # Force style update
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
    
    def getHoverOpacity(self):
        return self._hover_opacity
    
    def setHoverOpacity(self, opacity):
        """Set hover opacity and trigger repaint"""
        self._hover_opacity = opacity
        self.update()
    
    # Define the property for animation
    hoverOpacity = pyqtProperty(float, getHoverOpacity, setHoverOpacity)
    
    def paintEvent(self, event):
        """Override paint to add hover effect"""
        super().paintEvent(event)
        
        if self._hover_opacity > 0 and not self.property("selected"):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Get the current background color
            hover_color = QColor(120, 120, 120, int(40 * self._hover_opacity))
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(hover_color)
            painter.drawRoundedRect(self.rect(), 6, 6)
            painter.end()
    
    def eventFilter(self, obj, event):
        """Handle hover events and animations"""
        if obj is self:
            if event.type() == QEvent.Enter:
                # Start hover animation
                self._hover_animation.setStartValue(self._hover_opacity)
                self._hover_animation.setEndValue(1.0)
                self._hover_animation.start()
                
                # Change cursor to pointing hand
                self.setCursor(Qt.PointingHandCursor)
                return True
            elif event.type() == QEvent.Leave:
                # Fade out hover effect
                self._hover_animation.setStartValue(self._hover_opacity)
                self._hover_animation.setEndValue(0.0)
                self._hover_animation.start()
                
                # Change cursor back to default
                self.setCursor(Qt.ArrowCursor)
                return True
        
        return super().eventFilter(obj, event)


class SettingsNavigationBar(QWidget):
    """Sidebar navigation for settings, replacing tab widget"""
    selectionChanged = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 12, 0, 12)
        self.layout.setSpacing(4)  # Gap between items
        
        self.items = []
        self.selected_index = 0
        
        # Set fixed width (slightly wider for better spacing)
        self.setFixedWidth(200)
        self.setObjectName("navSidebar")
        
        # App icon or logo at the top
        self.header = QLabel("HydrateMinder")
        self.header.setObjectName("sidebarHeader")
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setFixedHeight(40)
        self.layout.addWidget(self.header)
        self.layout.addSpacing(12)  # Space after header
        
        # Container for nav items with margins
        self.nav_container = QWidget()
        self.nav_layout = QVBoxLayout(self.nav_container)
        self.nav_layout.setContentsMargins(8, 0, 8, 0)  # Margins for items
        self.nav_layout.setSpacing(4)  # Gap between items
        
        self.layout.addWidget(self.nav_container, 1)
        self.layout.addStretch()  # Push everything to the top
    
    def addItem(self, icon_path, text):
        """Add a navigation item to the sidebar"""
        index = len(self.items)
        item = SettingsNavItem(icon_path, text, index, self)
        
        # Connect click event
        item.mousePressEvent = lambda event, idx=index: self._handle_item_click(event, idx)
        
        self.nav_layout.addWidget(item)
        self.items.append(item)
        
        # Select first item by default
        if index == 0:
            item.setSelected(True)
        
        return index
    
    def _handle_item_click(self, event, index):
        """Handle item click to change selection"""
        if event.button() == Qt.LeftButton:
            self.setSelectedIndex(index)
    
    def setSelectedIndex(self, index):
        """Set the selected item by index with animation"""
        if 0 <= index < len(self.items) and index != self.selected_index:
            # Deselect current item
            self.items[self.selected_index].setSelected(False)
            
            # Select new item
            self.items[index].setSelected(True)
            self.selected_index = index
            
            # Emit signal
            self.selectionChanged.emit(index)


class SettingsSection(QWidget):
    """A settings section with title, description, and content"""
    def __init__(self, title, description=None, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 24)  # Margin at bottom for spacing between sections
        self.layout.setSpacing(16)
        
        # Add title
        if title:
            self.title_label = QLabel(title)
            self.title_label.setObjectName("sectionTitle")
            self.layout.addWidget(self.title_label)
        
        # Add description
        if description:
            self.description_label = QLabel(description)
            self.description_label.setObjectName("sectionDescription")
            self.description_label.setWordWrap(True)
            self.layout.addWidget(self.description_label)
        
        # Create content area
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(16)
        
        self.layout.addWidget(self.content)
    
    def addRow(self, label_text, widget, tooltip=None):
        """Add a row with label and widget to the section"""
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create label
        label = QLabel(label_text)
        label.setObjectName("settingLabel")
        if tooltip:
            label.setToolTip(tooltip)
        
        row_layout.addWidget(label, 1)  # Label takes up available space
        row_layout.addWidget(widget, 1)  # Widget takes remaining space
        
        self.content_layout.addWidget(row)
        return row
    
    def addWidget(self, widget):
        """Add a widget to the section content"""
        self.content_layout.addWidget(widget)
    
    def addLayout(self, layout):
        """Add a layout to the section content"""
        self.content_layout.addLayout(layout)
    
    def addSpacing(self, height):
        """Add vertical spacing"""
        self.content_layout.addSpacing(height)


class SettingsPage(QWidget):
    """Base class for each settings page"""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(32, 32, 32, 32)
        self.layout.setSpacing(24)
        
        # Header 
        self.header = QLabel(title)
        self.header.setObjectName("pageHeader")
        self.layout.addWidget(self.header)
        
        # Add scroll area for content
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setObjectName("contentScroll")
        
        # Content widget
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 20)
        self.content_layout.setSpacing(32)
        
        self.scroll_area.setWidget(self.content)
        self.layout.addWidget(self.scroll_area)
    
    def addSection(self, title, description=None):
        """Add a new settings section with title and optional description"""
        section = SettingsSection(title, description, self)
        self.content_layout.addWidget(section)
        return section
    
    def addSeparator(self):
        """Add a visual separator between sections"""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setObjectName("sectionSeparator")
        self.content_layout.addWidget(separator)
        return separator


class GeneralPage(SettingsPage):
    """Page for general settings like intervals and goals"""
    def __init__(self, parent_dialog, parent=None, slider_height=22):
        super().__init__("General", parent)
        self.parent_dialog = parent_dialog
        self.slider_height = slider_height
        self.init_ui()
        
    def init_ui(self):
        # Reminder Intervals Section
        intervals_section = self.addSection(
            "Reminder Intervals",
            "Configure how often you'll receive hydration reminders. The app will randomly select a time within your specified range."
        )
        
        # Min interval
        self.min_slider = MacOSSlider(1, 120, self.parent_dialog.main_app.min_hydration_interval, slider_height=self.slider_height)
        intervals_section.addRow("Minimum Minutes:", self.min_slider, 
                               "The shortest time between reminders")
        
        # Max interval
        self.max_slider = MacOSSlider(1, 180, self.parent_dialog.main_app.max_hydration_interval, slider_height=self.slider_height)
        intervals_section.addRow("Maximum Minutes:", self.max_slider,
                               "The longest time between reminders")
        
        # Add validation to ensure min <= max
        def validate_min_max():
            if self.min_slider.value() > self.max_slider.value():
                self.max_slider.setValue(self.min_slider.value())
        
        self.min_slider.valueChanged.connect(validate_min_max)
        
        # Snooze duration
        self.snooze_slider = MacOSSlider(1, 120, self.parent_dialog.main_app.snooze_duration, slider_height=self.slider_height)
        intervals_section.addRow("Snooze Duration:", self.snooze_slider,
                               "How long to wait when you snooze a reminder")
        
        # Hydration Goals Section
        goals_section = self.addSection(
            "Hydration Goals",
            "Set your daily hydration goal. The progress indicator will show how close you are to reaching your target."
        )
        
        # Daily goal
        self.daily_goal_slider = MacOSSlider(1, 60, self.parent_dialog.main_app.daily_hydration_goal, slider_height=self.slider_height)
        goals_section.addRow("Daily Drinks Goal:", self.daily_goal_slider,
                           "Your target number of drinks per day")
        
        # Add recommendation info
        info_label = QLabel("Experts recommend drinking 8-10 glasses of water daily for optimal hydration.")
        info_label.setObjectName("infoText")
        info_label.setWordWrap(True)
        goals_section.addWidget(info_label)
        
        # Behavior Section (new)
        behavior_section = self.addSection(
            "Application Behavior",
            "Configure how the application behaves on your system."
        )
        
        # Create and initialize the Start at Login toggle
        self.start_at_login_toggle = MacOSToggle()
        # Remove the default parameter because SettingsManager.get() only accepts one argument
        self.start_at_login_toggle.setChecked(self.parent_dialog.main_app.settings_manager.get('start_at_login'))
        behavior_section.addRow("Start at Login:", self.start_at_login_toggle,
                                 "Automatically launch the app when you log in")
        
        # Create and initialize the Notification Style combo box
        self.notification_combo = QComboBox()
        self.notification_combo.addItem("Legacy")
        self.notification_combo.addItem("Standard")
        self.notification_combo.addItem("Over the Top")
        current_notification_style = self.parent_dialog.main_app.settings_manager.get('notification_style')
        index = self.notification_combo.findText(current_notification_style)
        if index >= 0:
            self.notification_combo.setCurrentIndex(index)
        behavior_section.addRow("Notification Style:", self.notification_combo,
                                 "Choose how notifications appear (Legacy, Standard, or Over the Top)")




class ColorButton(QPushButton):
    """Color swatch button with preview for theme selection"""
    def __init__(self, color, label=None, parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.label = label
        self.setFixedSize(80, 80)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("colorButton")
    
    def paintEvent(self, event):
        """Custom painting for color preview"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw rounded rect with color
        rect = QRectF(4, 4, self.width() - 8, self.height() - 8)
        painter.setPen(Qt.NoPen)
        
        # Draw shadow if checked
        if self.isChecked():
            shadow_rect = QRectF(2, 2, self.width() - 4, self.height() - 4)
            painter.setBrush(QColor(0, 0, 0, 30))
            painter.drawRoundedRect(shadow_rect, 12, 12)
            
            # Draw highlight border
            painter.setPen(QPen(QColor("#007AFF"), 2))
        
        # Draw color preview
        painter.setBrush(self.color)
        painter.drawRoundedRect(rect, 10, 10)
        
        # Draw label if provided
        if self.label:
            painter.setPen(QColor(255, 255, 255) if self.color.lightness() < 128 else QColor(0, 0, 0))
            painter.drawText(rect, Qt.AlignCenter, self.label)
        
        painter.end()

class AppearancePage(SettingsPage):
    """Page for appearance settings like theme and visual preferences"""
    def __init__(self, parent_dialog, parent=None, slider_height=22):
        super().__init__("Appearance", parent)
        self.parent_dialog = parent_dialog
        self.slider_height = slider_height
        self.init_ui()
        
    def init_ui(self):
        # Theme Section
        theme_section = self.addSection(
            "Theme",
            "Choose a color theme for the application. This affects the overall look and feel."
        )
        
        # Visual theme selection with color previews
        theme_container = QWidget()
        theme_layout = QGridLayout(theme_container)
        theme_layout.setContentsMargins(0, 8, 0, 8)
        theme_layout.setSpacing(20)  # Increased spacing for nicer appearance
        
        # Available themes with color previews
        theme_data = [
            {"name": "Dark", "color": "#1E1E1E", "text": "Dark"},
            {"name": "Light", "color": "#F5F5F7", "text": "Light"},
            {"name": "Ocean", "color": "#0A84FF", "text": "Ocean"},
            {"name": "Forest", "color": "#30D158", "text": "Forest"},
            {"name": "Purple", "color": "#BF5AF2", "text": "Purple"}
        ]
        
        # Current theme
        current_theme = self.parent_dialog.main_app.theme_name
        
        # Create color buttons for each theme
        self.theme_buttons = []
        for i, theme in enumerate(theme_data):
            row, col = divmod(i, 3)  # 3 columns
            color_btn = ColorButton(theme["color"], theme["text"])
            color_btn.setCheckable(True)
            color_btn.setChecked(theme["name"].lower() == current_theme.lower())
            color_btn.setProperty("theme_name", theme["name"])
            
            # Make buttons larger
            color_btn.setFixedSize(90, 90)
            
            # Add label below button
            label = QLabel(theme["name"])
            label.setAlignment(Qt.AlignCenter)
            label.setObjectName("themeLabel")
            
            # Create container for button and label
            item_container = QWidget()
            item_layout = QVBoxLayout(item_container)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(10)  # More space between button and label
            item_layout.addWidget(color_btn, 0, Qt.AlignCenter)
            item_layout.addWidget(label, 0, Qt.AlignCenter)
            
            # Connect to handle exclusive selection
            color_btn.toggled.connect(self.handle_theme_selection)
            color_btn.clicked.connect(lambda checked=True, t=theme["name"]: self.update_theme_preview(t))
            
            theme_layout.addWidget(item_container, row, col)
            self.theme_buttons.append(color_btn)
        
        theme_section.addWidget(theme_container)
        
        # Add theme preview underneath
        self.theme_preview = ThemePreview()
        theme_section.addWidget(self.theme_preview)
        
        # Display Options Section
        display_section = self.addSection(
            "Display Options",
            "Customize how information is displayed in the application."
        )
        
        # Progress text display toggle
        self.show_progress_toggle = MacOSToggle()
        self.show_progress_toggle.setChecked(self.parent_dialog.main_app.show_progress_text)
        display_section.addRow("Show Progress Numbers:", self.show_progress_toggle)
        
        # Animation toggle
        self.enable_animations_toggle = MacOSToggle()
        self.enable_animations_toggle.setChecked(True)  # Default to enabled
        display_section.addRow("Enable Animations:", self.enable_animations_toggle)
        
        # Round corners toggle
        self.round_corners_toggle = MacOSToggle()
        self.round_corners_toggle.setChecked(True)  # Default to enabled
        display_section.addRow("Round Interface Corners:", self.round_corners_toggle)
        
        # Add spacer at bottom
        self.content_layout.addStretch(1)
        
        # Set initial theme preview
        self.update_theme_preview(current_theme)
    
    def handle_theme_selection(self, checked):
        """Handle theme selection to ensure only one is selected"""
        if not checked:
            # Prevent unchecking (one button must always be checked)
            sender = self.sender()
            any_checked = any(btn.isChecked() for btn in self.theme_buttons)
            if not any_checked:
                sender.setChecked(True)
            return
            
        # If checked, uncheck others
        sender = self.sender()
        for button in self.theme_buttons:
            if button != sender and button.isChecked():
                button.setChecked(False)
    
    def update_theme_preview(self, theme_name):
        """Update the theme preview based on selected theme"""
        self.theme_preview.updateStyles(theme_name)
        # Theme is applied globally through stylesheets, so no need to update individual elements


class SoundPage(SettingsPage):
    """Page for sound notification settings"""
    def __init__(self, parent_dialog, parent=None, slider_height=22):
        super().__init__("Sound", parent)
        self.parent_dialog = parent_dialog
        self.slider_height = slider_height
        
        # Create media player for sound previews
        self.player = QMediaPlayer(self)
        self.player.setVolume(60)
        
        self.init_ui()
        
    def init_ui(self):
        # Notification Sounds Section
        sound_section = self.addSection(
            "Notification Sounds",
            "Configure how sound notifications behave when it's time to hydrate."
        )
        
        # Sound toggle
        self.sound_enabled_toggle = MacOSToggle()
        self.sound_enabled_toggle.setChecked(self.parent_dialog.main_app.sound_enabled)
        sound_section.addRow("Enable Sound:", self.sound_enabled_toggle)
        
        # Sound selection with combo and preview
        sound_choice_widget = QWidget()
        sound_choice_layout = QHBoxLayout(sound_choice_widget)
        sound_choice_layout.setContentsMargins(0, 0, 0, 0)
        sound_choice_layout.setSpacing(8)
        
        # Sound combo box
        self.sound_choice_combo = QComboBox()
        self.sound_choice_combo.setObjectName("soundCombo")
        
        # Add sound options
        for sound_name in SOUND_OPTIONS.keys():
            try:
                self.sound_choice_combo.addItem(QIcon(resource_path("assets/icons/sound.svg")), sound_name)
            except:
                self.sound_choice_combo.addItem(sound_name)
        
        # Find and set current sound
        current_sound = None
        for key, value in SOUND_OPTIONS.items():
            if value == self.parent_dialog.main_app.sound_file:
                current_sound = key
                break
                
        if current_sound:
            index = self.sound_choice_combo.findText(current_sound)
            if index >= 0:
                self.sound_choice_combo.setCurrentIndex(index)
        
        # Play button
        self.play_button = QPushButton("Play")
        self.play_button.setObjectName("playButton")
        self.play_button.setFixedWidth(60)
        self.play_button.setToolTip("Preview notification sound")
        self.play_button.clicked.connect(self.play_selected_sound)
        
        sound_choice_layout.addWidget(self.sound_choice_combo, 1)
        sound_choice_layout.addWidget(self.play_button, 0)
        
        sound_section.addRow("Notification Sound:", sound_choice_widget)
        
        # Connect sound toggle to enable/disable sound selection
        self.sound_enabled_toggle.toggled.connect(lambda checked: self.sound_choice_combo.setEnabled(checked))
        self.sound_enabled_toggle.toggled.connect(lambda checked: self.play_button.setEnabled(checked))
        
        # Set initial state of sound controls
        self.sound_choice_combo.setEnabled(self.sound_enabled_toggle.isChecked())
        self.play_button.setEnabled(self.sound_enabled_toggle.isChecked())
        
        # Volume Section
        volume_section = self.addSection(
            "Volume",
            "Control how loud notification sounds play."
        )
        
        # Volume control widget
        volume_widget = QWidget()
        volume_layout = QHBoxLayout(volume_widget)
        volume_layout.setContentsMargins(0, 0, 0, 0)
        volume_layout.setSpacing(12)
        
        # Volume icon low
        volume_low_label = QLabel("🔈")  # Low volume icon
        volume_low_label.setObjectName("volumeIcon")
        
        # Volume slider
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(60)  # Default volume
        self.volume_slider.setFixedHeight(self.slider_height)  # Use consistent height
        self.volume_slider.valueChanged.connect(self.update_volume)
        
        # Volume icon high
        volume_high_label = QLabel("🔊")  # High volume icon
        volume_high_label.setObjectName("volumeIcon")
        
        # Volume value
        self.volume_value = QLabel("60%")
        self.volume_value.setObjectName("volumeValue")
        self.volume_value.setFixedWidth(45)
        self.volume_value.setAlignment(Qt.AlignCenter)
        
        # Connect slider to update label
        self.volume_slider.valueChanged.connect(lambda v: self.volume_value.setText(f"{v}%"))
        
        volume_layout.addWidget(volume_low_label)
        volume_layout.addWidget(self.volume_slider, 1)
        volume_layout.addWidget(volume_high_label)
        volume_layout.addWidget(self.volume_value)
        
        volume_section.addWidget(volume_widget)
        
        # Connect sound toggle to enable/disable volume controls
        self.sound_enabled_toggle.toggled.connect(lambda checked: self.volume_slider.setEnabled(checked))
        self.sound_enabled_toggle.toggled.connect(lambda checked: volume_low_label.setEnabled(checked))
        self.sound_enabled_toggle.toggled.connect(lambda checked: volume_high_label.setEnabled(checked))
        self.sound_enabled_toggle.toggled.connect(lambda checked: self.volume_value.setEnabled(checked))
        
        # Set initial state
        self.volume_slider.setEnabled(self.sound_enabled_toggle.isChecked())
        volume_low_label.setEnabled(self.sound_enabled_toggle.isChecked())
        volume_high_label.setEnabled(self.sound_enabled_toggle.isChecked())
        self.volume_value.setEnabled(self.sound_enabled_toggle.isChecked())
        
        # Sound Effects Section (new)
        effects_section = self.addSection(
            "Sound Effects",
            "Add subtle sound effects for interactions with the app."
        )
        
        # UI sound effects toggle
        self.ui_sounds_toggle = MacOSToggle()
        effects_section.addRow("Interface Sound Effects:", self.ui_sounds_toggle,
                              "Play subtle sounds for UI interactions")
        
        # Success sound effects toggle
        self.success_sounds_toggle = MacOSToggle()
        effects_section.addRow("Goal Achievement Sounds:", self.success_sounds_toggle,
                              "Play a sound when you reach your hydration goal")
        
        # Connect ui sounds toggle to enable success sounds toggle
        self.ui_sounds_toggle.toggled.connect(self.success_sounds_toggle.setEnabled)
        self.success_sounds_toggle.setEnabled(self.ui_sounds_toggle.isChecked())
        
        # Add spacer at bottom
        self.content_layout.addStretch(1)
    
    def update_volume(self, value):
        """Update the player volume when slider changes"""
        self.player.setVolume(value)
    
    def play_selected_sound(self):
        """Play the currently selected notification sound"""
        if not self.sound_enabled_toggle.isChecked():
            # Show a tooltip that sound is disabled
            QMessageBox.information(self, "Sound Disabled", "Enable sound notifications to preview sounds.")
            return
            
        selected_sound = self.sound_choice_combo.currentText()
        relative_sound_path = SOUND_OPTIONS.get(selected_sound)

        if relative_sound_path:
            # Show visual feedback when playing
            old_text = self.play_button.text()
            self.play_button.setText("▶")
            
            # Get absolute path to sound file
            try:
                absolute_sound_path = resource_path(relative_sound_path)
                url = QUrl.fromLocalFile(absolute_sound_path)
                content = QMediaContent(url)
                self.player.setMedia(content)
                self.player.play()
                
                # Reset text after playback
                self.player.stateChanged.connect(lambda state: 
                    self.play_button.setText(old_text) 
                    if state == QMediaPlayer.StoppedState else None)
            except Exception as e:
                self.play_button.setText(old_text)
                QMessageBox.warning(self, "Error", f"Could not play sound: {str(e)}")
        else:
            QMessageBox.warning(self, "Error", "Selected sound file not found!")


class DataPage(SettingsPage):
    """Page for data management settings"""
    def __init__(self, parent_dialog, parent=None):
        super().__init__("Data", parent)
        self.parent_dialog = parent_dialog
        self.init_ui()
        
    def init_ui(self):
        # Data Management Section
        data_section = self.addSection(
            "Data Management",
            "Manage your hydration history and app data. Use these options to reset or export your data."
        )
        
        # Action buttons in a grid
        button_grid = QGridLayout()
        button_grid.setSpacing(16)
        
        # Clear history button
        self.clear_data_btn = QPushButton("Clear Hydration History")
        self.clear_data_btn.setObjectName("dangerButton")
        try:
            self.clear_data_btn.setIcon(QIcon(resource_path("assets/icons/delete.svg")))
        except:
            pass  # If icon not found, just use text
        self.clear_data_btn.clicked.connect(self.clear_history)
        button_grid.addWidget(self.clear_data_btn, 0, 0)
        
        # Reset today's count button
        self.reset_today_btn = QPushButton("Reset Today's Count")
        self.reset_today_btn.setObjectName("warningButton")
        try:
            self.reset_today_btn.setIcon(QIcon(resource_path("assets/icons/refresh.svg")))
        except:
            pass  # If icon not found, just use text
        self.reset_today_btn.clicked.connect(self.reset_today_count)
        button_grid.addWidget(self.reset_today_btn, 0, 1)
        
        # Export button
        self.export_data_btn = QPushButton("Export Data")
        self.export_data_btn.setObjectName("secondaryButton")
        try:
            self.export_data_btn.setIcon(QIcon(resource_path("assets/icons/export.svg")))
        except:
            pass  # If icon not found, just use text
        self.export_data_btn.setEnabled(False)  # Disabled for future implementation
        button_grid.addWidget(self.export_data_btn, 1, 0)
        
        # Import button
        self.import_data_btn = QPushButton("Import Data")
        self.import_data_btn.setObjectName("secondaryButton")
        try:
            self.import_data_btn.setIcon(QIcon(resource_path("assets/icons/import.svg")))
        except:
            pass  # If icon not found, just use text
        self.import_data_btn.setEnabled(False)  # Disabled for future implementation
        button_grid.addWidget(self.import_data_btn, 1, 1)
        
        data_section.addLayout(button_grid)
        
        # Add tooltip to disabled buttons
        for btn in [self.export_data_btn, self.import_data_btn]:
            btn.setToolTip("This feature will be available in a future update")
        
        # Information text about data storage
        data_info = QLabel("Your hydration data is stored locally on your device. Clearing history cannot be undone.")
        data_info.setObjectName("infoText")
        data_info.setWordWrap(True)
        data_section.addWidget(data_info)
        
        # Stats & Analytics Section
        stats_section = self.addSection(
            "Statistics & Analytics",
            "View your hydration statistics and track your progress."
        )
        
        # View statistics button
        self.view_stats_btn = QPushButton("View Statistics")
        self.view_stats_btn.setObjectName("primaryButton")
        self.view_stats_btn.clicked.connect(self.show_history)
        stats_section.addWidget(self.view_stats_btn)
        
        # Add spacer at bottom
        self.content_layout.addStretch(1)
    
    def clear_history(self):
        """Prompt user to confirm before clearing all history"""
        reply = QMessageBox.question(
            self, "Clear History",
            "Are you sure you want to clear all hydration history?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # Default button
        )
        if reply == QMessageBox.Yes:
            try:
                self.parent_dialog.main_app.settings_manager.set("history", {})
                self.parent_dialog.main_app.save_settings()
                QMessageBox.information(self, "History Cleared", "All history has been cleared.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear history: {str(e)}")
    
    def reset_today_count(self):
        """Prompt user to confirm before resetting today's count"""
        reply = QMessageBox.question(
            self, "Reset Today's Count",
            "Are you sure you want to reset today's hydration count?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # Default button
        )
        if reply == QMessageBox.Yes:
            try:
                self.parent_dialog.main_app.hydration_log_count = 0
                self.parent_dialog.main_app.save_settings()
                QMessageBox.information(self, "Count Reset", "Today's hydration count has been reset.")
                self.parent_dialog.main_app.update_progress_ring()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to reset count: {str(e)}")
    
    def show_history(self):
        """Open history window to view statistics"""
        self.parent_dialog.main_app.show_history()


class SettingsDialog(QDialog):
    """Modern macOS-inspired settings dialog with sidebar navigation and frameless design"""
    def __init__(self, parent):
        super().__init__(parent)
        self.main_app = parent
        self.setWindowTitle("Settings")
        self.setMinimumSize(800, 600)  # Larger minimum size for better appearance
        
        # Remove window frame for custom title bar but keep opaque background
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        
        # Apply theme before building UI
        self.apply_theme(slider_height=20)  # Customize slider height here
        self.init_ui()
        
    def apply_theme(self, slider_height=22):
        """Apply macOS-inspired theme styling to the settings dialog"""
        theme_name = self.main_app.theme_name.lower()
        theme = MODERN_COLORS.get(theme_name, MODERN_COLORS.get("dark"))
        
        # Determine if it's a dark theme
        is_dark = theme.get('is_dark', False)
        
        # Get main colors from theme
        background_color = theme.get('background', '#1E1E1E' if is_dark else '#F5F5F7')
        surface_color = theme.get('surface', '#262626' if is_dark else '#FFFFFF')
        surface_raised = theme.get('surface_raised', '#323232' if is_dark else '#F0F0F0')
        text_color = theme.get('text', '#FFFFFF' if is_dark else '#000000')
        text_secondary_color = theme.get('text_secondary', '#BBBBBB' if is_dark else '#6E6E6E')
        border_color = theme.get('border', '#383838' if is_dark else '#D1D1D6')
        primary_color = theme.get('primary', '#0A84FF')  # iOS blue
        secondary_color = theme.get('secondary', '#52A8FF')  # lighter blue
        accent_color = theme.get('accent', '#FF453A')  # iOS red
        warning_color = theme.get('warning', '#FF9F0A')  # iOS orange
        success_color = theme.get('success', '#30D158')  # iOS green
            
        # Build stylesheet without SVG references
        self.setStyleSheet(f"""
            /* ======================================
            BASE DIALOG AND GENERAL ELEMENTS
            ====================================== */
            
            /* Main Dialog Background */
            QDialog {{
                background-color: {background_color};
                color: {text_color};
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
                border-radius: 10px; /* Rounded dialog corners */
            }}
            
            /* All Labels - No Background */
            QLabel {{
                background-color: transparent;
                color: {text_color};
            }}
            
            /* ======================================
            CUSTOM TITLE BAR
            ====================================== */
            
            /* Title bar background */
            #titleBar {{
                background-color: {surface_color};
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom: 1px solid {border_color};
            }}
            
            /* Window title */
            #windowTitle {{
                color: {text_color};
                font-size: 13px;
                font-weight: 500;
            }}
            
            /* Window control buttons base */
            #windowButton {{
                border-radius: 6px;
                border: none;
            }}
            
            /* Close button */
            #closeButton {{
                background-color: #FF5F57;
                border: none;
            }}
            
            #closeButton:hover {{
                background-color: #FF5F57;
            }}
            
            /* Minimize button */
            #minimizeButton {{
                background-color: #FEBC2E;
                border: none;
            }}
            
            #minimizeButton:hover {{
                background-color: #FEBC2E;
            }}
            
            /* Maximize button */
            #maximizeButton {{
                background-color: #28C840;
                border: none;
            }}
            
            #maximizeButton:hover {{
                background-color: #28C840;
            }}
            
            /* ======================================
            NAVIGATION SIDEBAR STYLING
            ====================================== */
            
            /* Sidebar Background with Border */
            #navSidebar {{
                background-color: {surface_color};
                border-right: 1px solid {border_color};
                border-bottom-left-radius: 10px;
            }}
            
            /* Sidebar header with app name */
            #sidebarHeader {{
                color: {primary_color};
                font-size: 16px;
                font-weight: 600;
                background-color: transparent;
            }}
            
            /* Navigation Item Containers */
            #navItem {{
                border-radius: 8px;
                padding: 8px 10px;
                margin: 2px 0;
                background-color: transparent;
            }}
            
            /* Selected Navigation Item */
            #navItem[selected="true"] {{
                background-color: {primary_color}18; /* 10% opacity primary color */
            }}
            
            /* Selection indicator bar */
            #selectionIndicator {{
                background-color: {primary_color};
                border-radius: 1.5px;
            }}
            
            /* Navigation Item Text */
            #navItemText {{
                color: {text_color};
                font-size: 14px;
            }}
            
            /* Navigation Icons */
            #navIcon {{
                color: {text_color};
                font-size: 16px;
            }}
            
            /* ======================================
            CONTENT AREA AND SCROLLING
            ====================================== */
            
            /* Content Area Background */
            #contentScroll {{
                background-color: transparent;
                border: none;
            }}
            
            /* Page Header Text */
            #pageHeader {{
                color: {text_color};
                font-size: 22px;
                font-weight: 600;
                margin-bottom: 8px;
            }}
            
            /* ======================================
            SECTION HEADERS AND DESCRIPTIONS
            ====================================== */
            
            /* Section Title Text */
            #sectionTitle {{
                color: {text_color};
                font-size: 16px;
                font-weight: 600;
                margin-top: 8px;
            }}
            
            /* Section Description Text */
            #sectionDescription {{
                color: {text_secondary_color};
                font-size: 13px;
                line-height: 1.4;
            }}
            
            /* Settings Label Text */
            #settingLabel {{
                color: {text_color};
                font-size: 14px;
            }}
            
            /* ======================================
            SLIDER CONTROLS
            ====================================== */
            
            /* macOS-style Slider - Base */
            QSlider {{
                height: {slider_height}px; /* Configurable slider height */
            }}
            
            /* Slider Track */
            QSlider::groove:horizontal {{
                background: {border_color};
                height: 4px;
                border-radius: 2px;
            }}
            
            /* Slider Track - Active/Filled Portion */
            QSlider::sub-page:horizontal {{
                background: {primary_color}; /* Color of the filled part */
                height: 4px;
                border-radius: 2px;
            }}
            
            /* Slider Handle */
            QSlider::handle:horizontal {{
                background: {primary_color};
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }}
            
            /* Slider Handle - Hover Effect */
            QSlider::handle:horizontal:hover {{
                background: {secondary_color};
                width: 18px; /* Slightly larger on hover */
                height: 18px;
                margin: -7px 0;
            }}
            
            /* Slider Handle - Pressed Effect */
            QSlider::handle:horizontal:pressed {{
                background: {secondary_color};
                width: 18px;
                height: 18px;
                margin: -7px 0;
            }}
            
            /* ======================================
            FORM INPUT CONTROLS
            ====================================== */
            
            /* Text Input Field */
            #valueInput {{
                background-color: {surface_raised};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 13px;
            }}
            
            /* Text Input Field - Focus */
            #valueInput:focus {{
                border: 1px solid {primary_color};
            }}
            
            /* Combo Box - Dropdown */
            QComboBox {{
                background-color: {surface_raised};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 6px 10px;
                min-height: 24px;
                font-size: 14px;
            }}
            
            /* Combo Box - Hover Effect */
            QComboBox:hover {{
                border-color: {primary_color}80; /* 50% opacity */
            }}
            
            /* Combo Box - Arrow Button */
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
                border: none;
                padding-right: 10px;
            }}
            
            /* Combo Box - Arrow Icon - NO SVG */
            QComboBox::down-arrow {{
                width: 10px;
                height: 10px;
                background-color: {primary_color};
                clip-path: polygon(0% 0%, 100% 0%, 50% 100%);
            }}
            
            /* Combo Box - Dropdown List */
            QComboBox QAbstractItemView {{
                background-color: {surface_raised};
                color: {text_color};
                border: 1px solid {border_color};
                selection-background-color: {primary_color}40; /* 25% opacity */
                selection-color: {text_color};
                border-radius: 6px;
                padding: 4px;
            }}
            
            /* ======================================
            BUTTON STYLES
            ====================================== */
            
            /* Standard Button */
            QPushButton {{
                background-color: {surface_raised};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
            }}
            
            /* Button - Hover Effect */
            QPushButton:hover {{
                background-color: {surface_raised};
                border: 1px solid {primary_color}80; /* 50% opacity */
            }}
            
            /* Button - Pressed Effect */
            QPushButton:pressed {{
                background-color: {surface_color};
            }}
            
            /* Button - Disabled State */
            QPushButton:disabled {{
                color: {text_secondary_color};
                opacity: 0.6;
            }}
            
            /* ======================================
            THEME SELECTOR BUTTONS
            ====================================== */
            
            /* Theme Button Label */
            #themeLabel {{
                color: {text_color};
                font-size: 14px;
                font-weight: 500;
                margin-top: 4px;
            }}
            
            /* Color Button */
            #colorButton {{
                background-color: transparent;
                border: 2px solid transparent;
                border-radius: 10px;
            }}
            
            #colorButton:checked {{
                border: 2px solid {primary_color};
            }}
            
            /* ======================================
            APPEARANCE PREVIEW
            ====================================== */
            
            /* Scale Preview Container */
            #scalePreview {{
                background-color: {surface_raised};
                border-radius: 8px;
                padding: 10px;
            }}
            
            /* Preview Label */
            #previewLabel {{
                font-size: 14px;
                font-weight: 500;
                margin-top: 10px;
            }}
            
            /* Preview Button */
            #previewButton {{
                background-color: {primary_color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 500;
            }}
            
            /* Preview Text */
            #previewText {{
                color: {text_color};
                margin-top: 8px;
                text-align: center;
            }}
            
            /* ======================================
            SPECIALIZED BUTTON VARIANTS
            ====================================== */
            
            /* Primary Action Button */
            #primaryButton {{
                background-color: {primary_color};
                color: white;
                border: none;
            }}
            
            #primaryButton:hover {{
                background-color: {secondary_color};
            }}
            
            /* Danger/Destructive Button */
            #dangerButton {{
                background-color: {accent_color};
                color: white;
                border: none;
            }}
            
            #dangerButton:hover {{
                background-color: {accent_color}DD; /* Slightly transparent */
            }}
            
            /* Warning Button */
            #warningButton {{
                background-color: {warning_color};
                color: white;
                border: none;
            }}
            
            #warningButton:hover {{
                background-color: {warning_color}DD; /* Slightly transparent */
            }}
            
            /* Secondary/Outline Button */
            #secondaryButton {{
                background-color: transparent;
                color: {text_color};
                border: 1px solid {border_color};
            }}
            
            #secondaryButton:hover {{
                background-color: rgba(128, 128, 128, 0.1);
                border-color: {primary_color}80; /* 50% opacity */
            }}
            
            /* Play Button for Sound Preview */
            #playButton {{
                background-color: {primary_color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px;
            }}
            
            #playButton:hover {{
                background-color: {secondary_color};
            }}
            
            /* ======================================
            VOLUME CONTROLS
            ====================================== */
            
            /* Volume Icon */
            #volumeIcon {{
                font-size: 16px;
                color: {text_color};
            }}
            
            /* Volume Value Text */
            #volumeValue {{
                color: {text_color};
                font-size: 14px;
            }}
            
            /* ======================================
            INFORMATIONAL ELEMENTS
            ====================================== */
            
            /* Informational Text */
            #infoText {{
                color: {text_secondary_color};
                font-size: 12px;
                font-style: italic;
                padding: 4px 0;
            }}
            
            /* ======================================
            DIVIDERS AND SEPARATORS
            ====================================== */
            
            /* Section Separator Line */
            #sectionSeparator {{
                background-color: {border_color};
                height: 1px;
            }}
            
            /* ======================================
            SCROLLBAR STYLING
            ====================================== */
            
            /* Vertical Scrollbar Base */
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 0px;
            }}
            
            /* Scrollbar Handle */
            QScrollBar::handle:vertical {{
                background: {border_color}80; /* 50% opacity */
                border-radius: 4px;
                min-height: 30px;
            }}
            
            /* Scrollbar Handle - Hover Effect */
            QScrollBar::handle:vertical:hover {{
                background: {border_color};
            }}
            
            /* Hide Scrollbar Buttons */
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            /* Hide Scrollbar Page Buttons */
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            
            /* ======================================
            BOTTOM BUTTON CONTAINER
            ====================================== */
            
            /* Container for Bottom Action Buttons */
            #buttonContainer {{
                background-color: {surface_color};
                border-top: 1px solid {border_color};
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }}
            
            /* Save Button */
            #saveButton {{
                background-color: {primary_color};
                color: white;
                border: none;
                min-width: 100px;
                font-weight: 600;
            }}
            
            #saveButton:hover {{
                background-color: {secondary_color};
            }}
            
            /* Cancel Button */
            #cancelButton {{
                background-color: transparent;
                color: {text_color};
                border: 1px solid {border_color};
                min-width: 80px;
            }}
            
            #cancelButton:hover {{
                background-color: rgba(128, 128, 128, 0.1);
                border-color: {primary_color}80; /* 50% opacity */
            }}
        """)
        
    def init_ui(self, slider_height=22):
        """Initialize the UI with macOS-inspired layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Add custom title bar
        self.title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)
        
        # Content container
        content_container = QWidget()
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Left sidebar for navigation
        self.navigation = SettingsNavigationBar(self)
        
        # Add items to navigation
        self.navigation.addItem("assets/icons/general.svg", "General")
        self.navigation.addItem("assets/icons/appearance.svg", "Appearance")
        self.navigation.addItem("assets/icons/sound.svg", "Sound")
        self.navigation.addItem("assets/icons/data.svg", "Data")
        
        # Stacked widget for content pages
        self.content_stack = QStackedWidget()
        
        # Create pages
        self.general_page = GeneralPage(self, slider_height=slider_height)
        self.appearance_page = AppearancePage(self, slider_height=slider_height)
        self.sound_page = SoundPage(self, slider_height=slider_height)
        self.data_page = DataPage(self)
        
        # Add pages to stack
        self.content_stack.addWidget(self.general_page)
        self.content_stack.addWidget(self.appearance_page)
        self.content_stack.addWidget(self.sound_page)
        self.content_stack.addWidget(self.data_page)
        
        # Connect navigation to stack
        self.navigation.selectionChanged.connect(self.content_stack.setCurrentIndex)
        
        # Add to content layout
        content_layout.addWidget(self.navigation)
        content_layout.addWidget(self.content_stack, 1)  # Content takes more space
        
        # Add content container to main layout
        main_layout.addWidget(content_container, 1)
        
        # Bottom button container
        self.button_container = QWidget()
        self.button_container.setObjectName("buttonContainer")
        button_layout = QHBoxLayout(self.button_container)
        button_layout.setContentsMargins(32, 16, 32, 16)
        
        # Save/Cancel buttons
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelButton")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("saveButton")
        self.save_btn.clicked.connect(self.save_settings)
        
        # Add buttons to layout
        button_layout.addStretch(1)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        # Add button container to main layout
        main_layout.addWidget(self.button_container)
        
        # Set dialog styles for shadows and corner radius
        #self.setAttribute(Qt.WA_TranslucentBackground)
    
    def save_settings(self):
        """Save all settings from the pages to the application"""
        # Validate settings
        valid_settings = True
        validation_message = ""
        
        # Validate General tab settings
        if self.general_page.min_slider.value() > self.general_page.max_slider.value():
            valid_settings = False
            validation_message = "Minimum interval cannot be greater than maximum interval."
        
        if not valid_settings:
            QMessageBox.warning(self, "Invalid Settings", validation_message)
            return
        
        # Show saving indicator
        self.save_btn.setText("Saving...")
        self.save_btn.setEnabled(False)
        QApplication.processEvents()  # Force UI update
        
        try:
            # General settings
            self.main_app.min_hydration_interval = self.general_page.min_slider.value()
            self.main_app.max_hydration_interval = self.general_page.max_slider.value()
            self.main_app.snooze_duration = self.general_page.snooze_slider.value()
            self.main_app.daily_hydration_goal = self.general_page.daily_goal_slider.value()
            
            # Appearance settings
            # Get the selected theme
            for button in self.appearance_page.theme_buttons:
                if button.isChecked():
                    self.main_app.theme_name = button.property("theme_name")
                    break
            self.main_app.show_progress_text = self.appearance_page.show_progress_toggle.isChecked()
            
            # Sound settings
            self.main_app.sound_enabled = self.sound_page.sound_enabled_toggle.isChecked()
            self.main_app.sound_file = SOUND_OPTIONS.get(
                self.sound_page.sound_choice_combo.currentText(),
                "assets/sounds/normal.wav"
            )
            
            # Behavior settings (referenced from the GeneralPage)
            self.main_app.settings_manager.set('start_at_login', self.general_page.start_at_login_toggle.isChecked())
            self.main_app.settings_manager.set('notification_style', self.general_page.notification_combo.currentText())
            
            # Save to settings manager and update the UI
            self.main_app.save_settings()
            self.main_app.apply_theme()
            
            # Show success message
            self.save_btn.setText("Saved ✓")
            QTimer.singleShot(1000, lambda: self.accept())
            
        except Exception as e:
            # Reset button state on error
            self.save_btn.setText("Save")
            self.save_btn.setEnabled(True)
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
    
    def reject(self):
        """Override reject to show confirmation dialog if changes were made"""
        # Check if any settings were changed
        if self.settings_changed():
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No  # Default button
            )
            if reply == QMessageBox.No:
                return
        
        # Directly close without animation to prevent flickering
        super().reject()
    
    def accept(self):
        """Override accept with direct closing to prevent flickering"""
        # Directly close without animation
        super().accept()
    
    def settings_changed(self):
        """Check if any settings were changed from their original values"""
        # General settings
        if (self.general_page.min_slider.value() != self.main_app.min_hydration_interval or
            self.general_page.max_slider.value() != self.main_app.max_hydration_interval or
            self.general_page.snooze_slider.value() != self.main_app.snooze_duration or
            self.general_page.daily_goal_slider.value() != self.main_app.daily_hydration_goal):
            return True
        
        # Appearance settings
        selected_theme = None
        for button in self.appearance_page.theme_buttons:
            if button.isChecked():
                selected_theme = button.property("theme_name")
                break
        if (selected_theme.lower() != self.main_app.theme_name.lower() or
            self.appearance_page.show_progress_toggle.isChecked() != self.main_app.show_progress_text):
            return True
        
        # Sound settings
        current_sound = None
        for key, value in SOUND_OPTIONS.items():
            if value == self.main_app.sound_file:
                current_sound = key
                break
        if (self.sound_page.sound_enabled_toggle.isChecked() != self.main_app.sound_enabled or
            self.sound_page.sound_choice_combo.currentText() != current_sound):
            return True
        
        # Behavior settings (referenced from the GeneralPage)
        if self.general_page.start_at_login_toggle.isChecked() != self.main_app.settings_manager.get('start_at_login'):
            return True
        if self.general_page.notification_combo.currentText() != self.main_app.settings_manager.get('notification_style'):
            return True
        
        return False
    
    def mousePressEvent(self, event):
        """Enable window dragging from any point"""
        if event.button() == Qt.LeftButton:
            # Allow dragging from the dialog background, but not control areas
            if not self._is_control_area(event.pos()):
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                self.dragging = True
                event.accept()
    
    def mouseMoveEvent(self, event):
        """Move window with mouse drag"""
        if hasattr(self, 'dragging') and self.dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """End window dragging"""
        if hasattr(self, 'dragging'):
            self.dragging = False
    
    def _is_control_area(self, pos):
        """Check if the position is over a control area that shouldn't trigger dragging"""
        # Don't allow dragging from buttons, sliders, etc.
        for control in [self.save_btn, self.cancel_btn]:
            if control.isVisible() and control.geometry().contains(pos):
                return True
                
        # Check if position is within stacked widget
        if self.content_stack.isVisible() and self.content_stack.geometry().contains(pos):
            return True
            
        return False