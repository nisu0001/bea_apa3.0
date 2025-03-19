# widgets/progress_ring_widget.py

from PyQt5.QtCore import Qt, QRectF, QPointF, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QBrush, QConicalGradient, QLinearGradient, QPainterPath, QFontMetrics
from PyQt5.QtWidgets import QWidget
from config import MODERN_COLORS

class ProgressRingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Basic progress attributes
        self._progress_value = 0.0
        self.log_count = 0
        self.daily_goal = 8
        self.show_text = True
        self.theme = "Dark"  # default theme
        self.countdown_progress = 0.0
        
        # Water droplet effect
        self.droplets = []
        self.droplet_timer = QTimer(self)
        self.droplet_timer.timeout.connect(self.update_droplets)
        self.droplet_timer.start(50)  # Update droplets every 50ms

    def add_droplet(self):
        """Add a new water droplet effect"""
        if len(self.droplets) < 8:  # Limit number of droplets
            self.droplets.append({
                'x': self.width() / 2,
                'y': self.height() / 2,
                'size': 5.0,
                'opacity': 1.0,
                'speed': 2.0
            })

    def update_droplets(self):
        """Animate water droplets"""
        for droplet in self.droplets:
            droplet['size'] += droplet['speed']
            droplet['opacity'] -= 0.01
        
        # Remove expired droplets
        self.droplets = [d for d in self.droplets if d['opacity'] > 0]
        self.update()

    def setProgress(self, progress, log_count, daily_goal, show_text=True, theme="Dark", countdown=0.0):
        """Set progress and other parameters - this is the main public method"""
        # Validate and clamp countdown_progress between 0 and 1
        try:
            self.countdown_progress = float(countdown)
        except (TypeError, ValueError):
            self.countdown_progress = 0.0
        self.countdown_progress = max(0.0, min(self.countdown_progress, 1.0))
        
        # Store current values
        self.log_count = int(log_count)
        self.daily_goal = int(daily_goal)
        self.show_text = bool(show_text)
        self.theme = theme if isinstance(theme, str) else "Dark"
        
        # Set progress value directly (no animation)
        self._progress_value = float(progress) if progress is not None else 0.0
        
        # Add water droplet effect for visual feedback
        if self._progress_value > 0:
            self.add_droplet()
            
        # Trigger a repaint
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        size = min(w, h) - 30  # Slightly smaller for padding
        rect = QRectF((w - size) / 2, (h - size) / 2, size, size)
        center_x, center_y = w / 2, h / 2
        
        # Get theme colors safely with a fallback
        try:
            theme_colors = MODERN_COLORS[self.theme.lower()]
        except KeyError:
            theme_colors = MODERN_COLORS.get("dark v2", {
                "highlight": "#72757E",
                "primary": "#7F5AF0",
                "secondary": "#2CB67D",
                "accent": "#EF4565",
                "text": "#FFFFFE",
                "background": "#16161A"
            })

        # Draw water droplet effects
        for droplet in self.droplets:
            painter.save()
            droplet_color = QColor(30, 144, 255, int(255 * droplet['opacity']))
            painter.setBrush(QBrush(droplet_color))
            painter.setPen(Qt.NoPen)
            droplet_rect = QRectF(
                droplet['x'] - droplet['size'] / 2,
                droplet['y'] - droplet['size'] / 2,
                droplet['size'],
                droplet['size']
            )
            painter.drawEllipse(droplet_rect)
            painter.restore()
            
        # Calculate ring dimensions and positioning
        center = rect.center()
        main_pen_width = max(10, size * 0.05)
        countdown_pen_width = max(4, size * 0.02)
        
        # ===== Background Ring with subtle glow =====
        bg_path = QRectF(rect)
        
        # Create a smooth background gradient
        bg_color = QColor(theme_colors.get('highlight', "#72757E"))
        bg_color.setAlphaF(0.3)  # Subtle transparency
        
        # Draw the background ring
        bg_pen = QPen(bg_color, main_pen_width)
        bg_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(bg_pen)
        painter.drawEllipse(rect)
        
        # ===== Progress Ring with Gradient =====
        if self._progress_value > 0:
            # Calculate arc rectangle
            progress_rect = QRectF(rect)
            
            # Create water-themed gradient
            progress_color = QColor(theme_colors.get('primary', "#1e90ff"))
            progress_pen = QPen(progress_color, main_pen_width)
            progress_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(progress_pen)
            
            # Calculate angles for the arc (counterclockwise from 90°)
            start_angle = 90 * 16  # Convert to 1/16th of a degree units
            span_angle = int(-self._progress_value * 360 * 16)  # Convert to integer
            
            # Draw the progress arc
            painter.drawArc(progress_rect, start_angle, span_angle)
        '''
        # ===== Progress Text with improved typography and glow =====
        if self.show_text:
            # Create glow effect for text
            glow_rect = rect.adjusted(rect.width() * 0.25, rect.height() * 0.25, 
                                    -rect.width() * 0.25, -rect.height() * 0.25)
            
            # Draw count text
            count_font = QFont("Segoe UI", int(size * 0.18), QFont.Bold)
            painter.setFont(count_font)
            
            # Calculate text dimensions for proper layout
            count_text = f"{self.log_count}/{self.daily_goal}"
            
            # Draw subtle glow/shadow
            shadow_color = QColor(0, 0, 0, 50)
            painter.setPen(shadow_color)
            painter.drawText(glow_rect.adjusted(2, 2, 2, 2), Qt.AlignCenter, count_text)
            
            # Draw main text
            painter.setPen(QColor(theme_colors.get('text', "#FFFFFF")))
            painter.drawText(glow_rect, Qt.AlignCenter, count_text)
            
            # Draw "drinks" label
            label_font = QFont("Segoe UI", int(size * 0.08))
            painter.setFont(label_font)
            label_rect = rect.adjusted(0, rect.height() * 0.15, 0, rect.height() * 0.15)
            painter.drawText(label_rect, Qt.AlignCenter, "drinks today")
        ''' 
         
        if self.show_text:
            # Prepare text content
            main_text = f"{self.log_count}"
            goal_text = f"of {self.daily_goal}"
            
            # Set up text colors
            text_color = QColor(theme_colors.get('text', "#FFFFFF"))
            secondary_text_color = QColor(text_color)
            secondary_text_color.setAlphaF(0.7)  # Slightly transparent for secondary text
            
            # Calculate font sizes proportional to widget size
            main_font_size = int(size * 0.22)
            goal_font_size = int(size * 0.11)
            
            # ---- Draw main count ----
            main_font = QFont("Segoe UI", main_font_size, QFont.Bold)
            painter.setFont(main_font)
            
            # Get text dimensions for centering
            metrics = QFontMetrics(main_font)
            main_text_width = metrics.horizontalAdvance(main_text)
            main_text_height = metrics.height()
            
            # Position text in center
            main_text_x = center_x - main_text_width / 2
            main_text_y = center_y - main_text_height / 4
            
            # Draw main count with subtle shadow for depth
            painter.setPen(QColor(0, 0, 0, 50))
            painter.drawText(QPointF(main_text_x + 1, main_text_y + 1), main_text)
            painter.setPen(text_color)
            painter.drawText(QPointF(main_text_x, main_text_y), main_text)
            
            # ---- Draw goal text ----
            goal_font = QFont("Segoe UI", goal_font_size)
            painter.setFont(goal_font)
            
            # Get text dimensions for centering
            metrics = QFontMetrics(goal_font)
            goal_text_width = metrics.horizontalAdvance(goal_text)
            
            # Position below main text
            goal_text_x = center_x - goal_text_width / 2
            goal_text_y = main_text_y + main_text_height * 0.8
            
            painter.setPen(secondary_text_color)
            painter.drawText(QPointF(goal_text_x, goal_text_y), goal_text)
        '''
        if self.show_text:
            # Create a semi-transparent background circle
            center_size = size * 0.55
            center_rect = QRectF(rect.center().x() - center_size/2, 
                              rect.center().y() - center_size/2,
                              center_size, center_size)
            
            
            # Draw text with appropriate sizing
            font_size = int(size * 0.15)
            count_font = QFont("SF Pro Display, -apple-system, Segoe UI", font_size, QFont.DemiBold)
            goal_font = QFont("SF Pro Display, -apple-system, Segoe UI", int(font_size * 0.7), QFont.Normal)
            
            # Draw count
            painter.setFont(count_font)
            painter.setPen(QColor(theme_colors.get('text', "#FFFFFF")))
            count_rect = center_rect.adjusted(0, -center_size * 0.1, 0, 0)
            painter.drawText(count_rect, Qt.AlignHCenter | Qt.AlignBottom, f"{self.log_count}")
            
            # Draw goal
            painter.setFont(goal_font)
            painter.setPen(QColor(theme_colors.get('highlight', "#8E8E93")))
            goal_rect = center_rect.adjusted(0, center_size * 0.1, 0, 0)
            painter.drawText(goal_rect, Qt.AlignHCenter | Qt.AlignTop, f"/ {self.daily_goal}")

        '''  
        # ===== Countdown Progress Indicator =====
        if self.countdown_progress > 0:
            # Draw a more subtle countdown indicator
            countdown_rect = rect.adjusted(
                main_pen_width * 1.5, 
                main_pen_width * 1.5, 
                -main_pen_width * 1.5, 
                -main_pen_width * 1.5
            )
            
            countdown_pen = QPen(QColor(theme_colors.get('accent', "#EF4565")), countdown_pen_width)
            countdown_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(countdown_pen)
            
            countdown_extent = int(self.countdown_progress * 360 * 16)  # Convert to integer
            painter.drawArc(countdown_rect, 90 * 16, -countdown_extent)  # Use correct format