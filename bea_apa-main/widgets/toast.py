from PyQt5.QtCore import Qt, QRectF, QPropertyAnimation, QPoint, QEasingCurve, QTimer
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QFont, QFontDatabase
from PyQt5.QtWidgets import QLabel, QGraphicsDropShadowEffect

class ToastLabel(QLabel):
    def __init__(self, text, parent=None, theme=None, duration=3000):
        """
        Create an Apple-style toast notification.
        
        :param text: Text to display in the toast
        :param parent: Parent widget
        :param theme: Theme dictionary with color definitions
        :param duration: How long the toast should remain visible (in ms)
        """
        super().__init__(text, parent)
        
        # Store theme information
        self.theme = theme if theme is not None else {
            "is_dark": True,
            "background": "#0A2740",
            "surface": "#123859", 
            "text": "#FFFFFF",
            "shadow": "#051526",
        }
        
        # Set up basic widget properties
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAlignment(Qt.AlignCenter)
        
        # Try to use SF Pro Text (Apple's system font) if available, otherwise fallback
        font_id = QFontDatabase.addApplicationFont(":/fonts/SF-Pro-Text-Regular.otf")
        font_family = "SF Pro Text" if font_id != -1 else "system-ui"
        
        # Create font object with proper weight
        font = QFont(font_family, 14)
        font.setWeight(QFont.Medium)
        self.setFont(font)
        
        # Apply styling
        text_color = self.theme.get("text", "#FFFFFF")
        self.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                padding: 14px 24px;
            }}
        """)
        
        # Apply shadow effect for depth
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setColor(QColor(self.theme.get("shadow", "#000000")))
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        # QGraphicsDropShadowEffect doesn't have setOpacity - fixed
        # Control opacity through the shadow color's alpha value
        shadow_color = QColor(self.theme.get("shadow", "#000000"))
        shadow_color.setAlpha(50)  # 0-255 range, 50 is ~20% opacity
        shadow.setColor(shadow_color)
        self.setGraphicsEffect(shadow)
        
        # Set up animations for elegant appearance
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.setDuration(300)  # Animation duration (ms)
        
        # Store duration for auto-hide
        self.duration = duration
        
        # Flag to control blur effect
        self.is_dark_mode = self.theme.get("is_dark", True)
    
    def showEvent(self, event):
        """Handle appearance animation when toast is shown"""
        super().showEvent(event)
        
        if self.parent():
            # Calculate starting and ending positions
            parent_rect = self.parent().rect()
            target_x = (parent_rect.width() - self.width()) // 2
            target_y = parent_rect.height() - self.height() - 60  # 60px from bottom
            
            # Start from below the visible area
            start_pos = QPoint(target_x, parent_rect.height() + 20)
            end_pos = QPoint(target_x, target_y)
            
            # Set up and start the animation
            self.move(start_pos)
            self.animation.setStartValue(start_pos)
            self.animation.setEndValue(end_pos)
            self.animation.start()
            
            # Schedule hiding after duration
            if self.duration > 0:
                QTimer.singleShot(self.duration, self.hide_toast)
    
    def hide_toast(self):
        """Animate toast hiding"""
        if not self.isVisible():
            return
            
        # Create hide animation
        hide_anim = QPropertyAnimation(self, b"pos")
        hide_anim.setEasingCurve(QEasingCurve.InCubic)
        hide_anim.setDuration(250)  # Faster than show animation
        
        # Calculate end position (below screen)
        current_pos = self.pos()
        if self.parent():
            end_pos = QPoint(current_pos.x(), self.parent().height() + 20)
        else:
            end_pos = QPoint(current_pos.x(), current_pos.y() + 100)
            
        hide_anim.setStartValue(current_pos)
        hide_anim.setEndValue(end_pos)
        
        # Connect the finished signal to actually hide the widget
        hide_anim.finished.connect(self.hide)
        hide_anim.start()
    
    def paintEvent(self, event):
        """Custom paint event to draw the toast background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create rounded rect for the toast
        rect = QRectF(0, 0, self.width(), self.height())
        path = QPainterPath()
        path.addRoundedRect(rect, 14, 14)  # Apple uses more subtle rounding
        
        # Fill with background color based on theme
        # Apple's notifications use blur + semi-transparency
        if self.is_dark_mode:
            # Dark mode: darker, more transparent
            background_color = QColor(20, 20, 25, 235)
        else:
            # Light mode: lighter, less transparent
            background_color = QColor(245, 245, 247, 235)
            
        # For a frosted glass effect, we would use a blur effect
        # But since that's complex in Qt, we simulate with transparency
        painter.fillPath(path, background_color)
        
        # Draw subtle border for definition (Apple uses this in macOS)
        border_color = QColor(255, 255, 255, 30) if self.is_dark_mode else QColor(0, 0, 0, 15)
        painter.setPen(border_color)
        painter.drawPath(path)
        
        # Now let the label draw its text content
        super().paintEvent(event)