
import math
import sys
import datetime
import time
import random
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF, QEasingCurve, QPropertyAnimation, QPoint
from PyQt5.QtGui import QPainter, QColor, QLinearGradient, QFont, QFontMetrics, QPainterPath, QPen
from PyQt5.QtWidgets import QLabel, QApplication, QMenu, QGraphicsOpacityEffect

class LoveTimer(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

        # --- Date Configuration ---
        self.start_time = datetime.datetime(2024, 7, 25, 22, 36, 0)

        # --- Theme Colors ---
        self.bg_color = QColor(30, 30, 35, 180)  # Dark with transparency
        self.text_color = QColor(255, 255, 255)  # White text
        self.accent_color = QColor(236, 100, 130)  # Soft pink accent

        # --- Layout Settings ---
        self.margin = 15
        self.corner_radius = 12
        self.num_particles = 5  # Subtle particle effect instead of hearts

        # --- Font Setup ---
        self.font = QFont("Segoe UI", 14)  # Modern, clean font
        self.day_font = QFont("Segoe UI", 22)  # Larger font for days
        self.day_font.setWeight(QFont.DemiBold)
        self.setFont(self.font)

        # Compute widget size based on a sample text layout
        metrics = QFontMetrics(self.day_font)
        day_text_height = metrics.height()
        metrics = QFontMetrics(self.font)
        time_text_height = metrics.height()
        
        sample_text = "000 days"
        text_width = max(metrics.horizontalAdvance(sample_text), metrics.horizontalAdvance("00:00:00"))
        
        width = text_width + 50  # add horizontal padding
        height = day_text_height + time_text_height + 40  # add vertical padding
        self.setFixedSize(width, height)

        # --- Window Setup ---
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.95)
        self.setAlignment(Qt.AlignCenter)
        self.setToolTip("Right-click for menu. Double-click to hide.")

        # --- Particle Animation Setup ---
        self.particles = []
        self.initialize_particles()

        # --- Timers ---
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(500)
        self.update_time()

        self.last_update_time = time.time()
        self.particle_timer = QTimer(self)
        self.particle_timer.timeout.connect(self.animate_particles)
        self.particle_timer.start(30)

        # --- Fade-in Animation ---
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim.setDuration(800)
        self.opacity_anim.setStartValue(0)
        self.opacity_anim.setEndValue(1)
        self.opacity_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        # Position widget and start animations
        self.move_to_corner()
        self.opacity_anim.start()

        # --- Dragging Variables ---
        self.dragging = False
        self.offset = QPoint()
        
        # --- Track if widget is active ---
        self.is_active = True

        # Initialize widget values
        self.days = 0
        self.hours = 0
        self.minutes = 0
        self.seconds = 0

    def initialize_particles(self):
        """Initialize subtle floating particles"""
        self.particles = []  # Clear any existing particles
        for _ in range(self.num_particles):
            particle = {
                'pos': QPointF(random.uniform(0, self.width()), random.uniform(0, self.height())),
                'size': random.uniform(2, 5),
                'opacity': random.uniform(0.2, 0.6),
                'speed': random.uniform(5, 20),
                'direction': random.uniform(0, 2 * 3.14159)
            }
            self.particles.append(particle)

    def move_to_corner(self):
        """Place the widget in the top-right corner with some padding"""
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.x() + screen.width() - self.width() - 20  # 20px padding from edge
        y = screen.y() + 20  # 20px padding from top
        self.move(x, y)

    def animate_particles(self):
        """Update particle positions with smooth movement"""
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time

        for particle in self.particles:
            # Calculate movement vector
            dx = dt * particle['speed'] * math.cos(particle['direction'])
            dy = dt * particle['speed'] * math.sin(particle['direction'])
            
            # Update position
            new_x = particle['pos'].x() + dx
            new_y = particle['pos'].y() + dy
            
            # Bounce off edges
            if new_x < 0 or new_x > self.width():
                particle['direction'] = 3.14159 - particle['direction']
                new_x = max(0, min(new_x, self.width()))
            
            if new_y < 0 or new_y > self.height():
                particle['direction'] = -particle['direction']
                new_y = max(0, min(new_y, self.height()))
            
            # Occasionally change direction slightly for more natural movement
            if random.random() < 0.02:
                particle['direction'] += random.uniform(-0.2, 0.2)
                
            # Apply new position
            particle['pos'] = QPointF(new_x, new_y)
            
            # Slowly change opacity for subtle fading effect
            particle['opacity'] += random.uniform(-0.01, 0.01)
            particle['opacity'] = max(0.1, min(0.7, particle['opacity']))

        self.update()

    def update_time(self):
        """Update the display with the elapsed time since start_time"""
        now = datetime.datetime.now()
        diff = now - self.start_time
        days = diff.days
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # We'll use paintEvent to render this more beautifully
        self.days = abs(days)
        self.hours = abs(hours)
        self.minutes = abs(minutes)
        self.seconds = abs(seconds)
        self.update()

    def mouseDoubleClickEvent(self, event):
        # Modified to hide instead of close
        self.start_fade_out()

    def hide_widget(self):
        """Hide the widget without destroying it"""
        self.is_active = False
        self.hide()
        # Stopping timers when hidden to save resources
        self.time_timer.stop()
        self.particle_timer.stop()
        
        # Signal that the fade-out has completed (for parent window tracking)
        if hasattr(self, 'fade_out_finished') and callable(self.fade_out_finished):
            self.fade_out_finished()

    def show_widget(self):
        """Show the widget and restart necessary timers"""
        print("LoveTimer show_widget called")
        
        # Stop any ongoing animations first
        if self.opacity_anim.state() == QPropertyAnimation.Running:
            self.opacity_anim.stop()
        
        # Disconnect any existing connections to prevent unwanted callbacks
        try:
            self.opacity_anim.finished.disconnect()
        except:
            pass
        
        # Reset the opacity for fade-in
        self.opacity_effect.setOpacity(0)
        
        # Make widget visible first (before animation)
        self.show()
        
        # Restart timers
        self.last_update_time = time.time()
        self.time_timer.start(500)
        self.particle_timer.start(30)
        
        # Update time immediately
        self.update_time()
        
        # Reinitialize particles in case they're in a bad state
        self.initialize_particles()
        
        # Start fade-in animation
        self.opacity_anim.setDirection(QPropertyAnimation.Forward)
        self.opacity_anim.start()
        
        self.is_active = True
        
        # Ensure the widget is brought to front
        self.raise_()
        self.activateWindow()

    # 2. Make sure the fade_out_finished callback isn't being triggered incorrectly:

    def hide_widget(self):
        """Hide the widget without destroying it"""
        print("LoveTimer hide_widget called")
        
        # Only proceed if we're actually visible
        if not self.isVisible():
            print("Widget already hidden, ignoring hide_widget call")
            return
            
        self.is_active = False
        self.hide()
        
        # Stopping timers when hidden to save resources
        self.time_timer.stop()
        self.particle_timer.stop()
        
        # Signal that the fade-out has completed (for parent window tracking)
        if hasattr(self, 'fade_out_finished') and callable(self.fade_out_finished):
            self.fade_out_finished()

    # 3. Fix the start_fade_out method to be more robust:

    def start_fade_out(self):
        """Start the fade-out animation and connect to hide_widget"""
        print("LoveTimer starting fade out")
        
        # Don't do anything if we're already hidden or fading out
        if not self.isVisible() or (self.opacity_anim.direction() == QPropertyAnimation.Backward and 
                                    self.opacity_anim.state() == QPropertyAnimation.Running):
            print("Widget already hidden or fading out, ignoring start_fade_out call")
            return
        
        # Disconnect any previous connections to avoid multiple connections
        try:
            self.opacity_anim.finished.disconnect()
        except:
            pass
            
        self.opacity_anim.setDirection(QPropertyAnimation.Backward)
        self.opacity_anim.finished.connect(self.hide_widget)
        self.opacity_anim.start()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1E1E23;
                border: 1px solid #333;
                border-radius: 4px;
                color: white;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #EC6482;
            }
        """)
        
        hideAction = menu.addAction("Hide Timer")
        action = menu.exec_(event.globalPos())
        
        if action == hideAction:
            self.start_fade_out()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.LeftButton:
            self.move(self.mapToGlobal(event.pos() - self.offset))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw background with subtle rounded corners
        rect = QRectF(0, 0, self.width(), self.height())
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.bg_color)
        painter.drawRoundedRect(rect, self.corner_radius, self.corner_radius)
        
        # Draw subtle border
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), self.corner_radius, self.corner_radius)

        # Draw animated particles
        for particle in self.particles:
            painter.save()
            color = QColor(self.accent_color)
            color.setAlphaF(particle['opacity'])
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(particle['pos'], particle['size'], particle['size'])
            painter.restore()

        # Draw days counter with emphasis
        day_text = f"{self.days}"
        day_unit = "days" if self.days != 1 else "day"
        
        # Days count
        painter.setFont(self.day_font)
        painter.setPen(self.accent_color)
        
        day_metrics = QFontMetrics(self.day_font)
        day_rect = day_metrics.boundingRect(day_text)
        day_x = (self.width() - day_metrics.horizontalAdvance(day_text) - 
                 day_metrics.horizontalAdvance(" " + day_unit)) // 2
        day_y = self.height() // 2 - 5
        
        painter.drawText(day_x, day_y, day_text)
        
        # "days" text
        painter.setFont(self.font)
        unit_x = day_x + day_metrics.horizontalAdvance(day_text) + 3
        painter.drawText(unit_x, day_y, day_unit)
        
        # Time counter below
        time_text = f"{self.hours:02}:{self.minutes:02}:{self.seconds:02}"
        painter.setPen(self.text_color)
        time_metrics = QFontMetrics(self.font)
        time_width = time_metrics.horizontalAdvance(time_text)
        painter.drawText((self.width() - time_width) // 2, day_y + day_metrics.height() + 5, time_text)

    def closeEvent(self, event):
        # This is called when the widget is being explicitly closed (e.g., by system close)
        print("LoveTimer closeEvent triggered")
        self.start_fade_out()
        event.ignore()  # Prevent the widget from being destroyed

# Example of a main window that can show/hide the timer
class MainApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        
        self.love_timer = LoveTimer()
        self.love_timer.show()
        
    def toggle_timer(self):
        """Show or hide the timer based on current state"""
        if self.love_timer.is_active:
            self.love_timer.start_fade_out()
        else:
            self.love_timer.show_widget()

