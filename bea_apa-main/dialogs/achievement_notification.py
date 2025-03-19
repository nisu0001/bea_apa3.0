# dialogs/achievement_notification.py
from PyQt5.QtCore import Qt, QRectF, QPropertyAnimation, QPoint, QEasingCurve, QTimer, QSize, QSequentialAnimationGroup
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QFont, QIcon, QRadialGradient, QBrush, QGuiApplication
from PyQt5.QtWidgets import QLabel, QGraphicsDropShadowEffect, QHBoxLayout, QVBoxLayout, QWidget, QFrame, QGraphicsOpacityEffect
import random  # For confetti animation

class AchievementNotification(QWidget):
    def __init__(self, achievement, parent=None, theme=None, duration=5000):
        """
        Create an Apple-style achievement unlocked notification.
        
        Args:
            achievement: Achievement object that was unlocked
            parent: Parent widget
            theme: Theme dictionary with color definitions
            duration: How long the notification should remain visible (in ms)
        """
        super().__init__(parent)
        self.achievement = achievement
        self.theme = theme if theme is not None else {
            "is_dark": True,
            "background": "#0A2740",
            "surface": "#123859", 
            "text": "#FFFFFF",
            "shadow": "#051526",
            "primary": "#0A84FF",
            "success": "#30D158"
        }
        
        # Set up window properties for a floating notification
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(360, 120)

        # Create internal container
        self.container = QFrame(self)
        self.container.setObjectName("container")
        self.container.setGeometry(self.rect())
        
        # Initialize UI components
        self.init_ui(self.container)

        # Apply drop shadow effect
        self.apply_shadow_effect()
        
        # Set up animations
        self.setup_animations()
        
        self.duration = duration
        self.is_dark_mode = self.theme.get("is_dark", True)
        
        # Create confetti overlay
        self.confetti_overlay = None
        
    def apply_shadow_effect(self):
        """Apply drop shadow effect to the notification"""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        self.setGraphicsEffect(shadow)
        
    def setup_animations(self):
        """Set up entry and exit animations"""
        # Entry animation - slide in from right
        self.entry_anim = QPropertyAnimation(self, b"pos")
        self.entry_anim.setDuration(400)
        self.entry_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        # Exit animation - slide out to right
        self.exit_anim = QPropertyAnimation(self, b"pos")
        self.exit_anim.setEasingCurve(QEasingCurve.InCubic)
        self.exit_anim.setDuration(600)
        
        # Opacity animation for fade in
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(200)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.OutCubic)

    def init_ui(self, parent_widget):
        """
        Initialize the UI components inside the container widget
        """
        layout = QHBoxLayout(parent_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Icon container with nice background
        icon_container = QFrame()
        icon_container.setFixedSize(60, 60)
        icon_container.setObjectName("iconContainer")
        icon_container.setStyleSheet("background: transparent;")
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignCenter)
        
        # Icon mapping - SF Symbols style emoji representation
        icon_map = {
            "water": "💧",
            "target": "🎯",
            "calendar": "📆",
            "trophy": "🏆",
            "badge": "🏅",
            "clock": "⏰",
            "sunrise": "🌅",
            "moon": "🌙",
            "star": "⭐",
            "fire": "🔥",
            "streak": "🔥",
            "check": "✅"
        }
        icon_text = icon_map.get(getattr(self.achievement, 'icon', None), "🏆")
        
        # Create icon label with emoji
        icon_label = QLabel(icon_text)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setObjectName("achievementIcon")
        icon_label.setStyleSheet("background: transparent;")
        font = QFont()
        font.setPointSize(30)
        icon_label.setFont(font)
        icon_layout.addWidget(icon_label)
        layout.addWidget(icon_container)
        
        # Text content
        text_layout = QVBoxLayout()
        text_layout.setSpacing(6)
        
        # Header
        header_label = QLabel("Achievement Unlocked!")
        header_label.setObjectName("notificationHeader")
        header_label.setStyleSheet("background: transparent;")
        text_layout.addWidget(header_label)
        
        # Achievement Name
        name_label = QLabel(self.achievement.name)
        name_label.setObjectName("achievementName")
        name_label.setStyleSheet("background: transparent;")
        text_layout.addWidget(name_label)
        
        # Achievement Description
        description_label = QLabel(self.achievement.description)
        description_label.setObjectName("achievementDescription")
        description_label.setWordWrap(True)
        description_label.setStyleSheet("background: transparent;")
        text_layout.addWidget(description_label)
        layout.addLayout(text_layout, 1)
        
        # Apply styling with vibrant colors
        success_color = self.theme.get('success', '#30D158')
        text_color = self.theme.get('text', '#FFFFFF')
        secondary_text = self.theme.get('text_secondary', '#98989E')
        self.container.setStyleSheet(f"""
            QFrame#container {{
                background-color: transparent;
            }}
            #iconContainer {{
                background-color: {success_color};
                border-radius: 30px;
            }}
            #achievementIcon {{
                color: white;
            }}
            #notificationHeader {{
                color: {success_color};
                font-size: 14px;
                font-weight: bold;
            }}
            #achievementName {{
                color: {text_color};
                font-size: 18px;
                font-weight: bold;
            }}
            #achievementDescription {{
                color: {secondary_text};
                font-size: 14px;
            }}
        """)
        
    def showEvent(self, event):
        """Show notification with a slide-in animation and schedule auto-hide"""
        super().showEvent(event)
        from PyQt5.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().availableGeometry()
        
        # Calculate positions for animation
        start_x = screen.width() + 20  # Start off-screen to the right
        target_y = 80  # Distance from top
        target_x = screen.width() - self.width() - 20
        
        # Set initial position and animate entry
        self.move(start_x, target_y)
        self.entry_anim.setStartValue(QPoint(start_x, target_y))
        self.entry_anim.setEndValue(QPoint(target_x, target_y))
        
        # Create animation group to sequence fade-in and slide-in
        animation_group = QSequentialAnimationGroup(self)
        animation_group.addAnimation(self.fade_in)
        animation_group.addAnimation(self.entry_anim)
        animation_group.start()
            
        # Show confetti for significant achievements
        if self.is_significant_achievement():
            self.show_confetti()
        
        # Play sound if needed - let the caller handle this
        # self.play_achievement_sound()
            
        # Set timer for auto-hide
        if self.duration > 0:
            QTimer.singleShot(self.duration, self.hide_notification)
    
    def is_significant_achievement(self):
        """Determine if this is a significant achievement worthy of confetti"""
        # Check if this is a major achievement based on properties
        if hasattr(self.achievement, 'is_major') and self.achievement.is_major:
            return True
            
        # Check progress-based achievements
        if hasattr(self.achievement, 'progress_max') and self.achievement.progress_max >= 10:
            return True
            
        # Check if it's a special achievement type
        special_icons = ['trophy', 'badge', 'star']
        if hasattr(self.achievement, 'icon') and self.achievement.icon in special_icons:
            return True
            
        return False
    
    def hide_notification(self):
        """Animate hiding of the notification with slide-out animation"""
        if not self.isVisible():
            return
            
        from PyQt5.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().availableGeometry()
        
        # Calculate positions for exit animation
        current_pos = self.pos()
        end_pos = QPoint(screen.width() + 20, current_pos.y())
        
        # Set up and start exit animation
        self.exit_anim.setStartValue(current_pos)
        self.exit_anim.setEndValue(end_pos)
        self.exit_anim.finished.connect(self.close)
        self.exit_anim.finished.connect(self.deleteLater)
        self.exit_anim.start()
    
    def paintEvent(self, event):
        """Custom paint event to draw a rounded, semi-transparent background with subtle glow"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background with rounded corners
        rect = QRectF(0, 0, self.width(), self.height())
        path = QPainterPath()
        path.addRoundedRect(rect, 16, 16)
        
        # Background color based on theme with slight transparency
        if self.is_dark_mode:
            background_color = QColor(20, 20, 25, 235)
        else:
            background_color = QColor(245, 245, 247, 235)
        painter.fillPath(path, background_color)
        
        # Subtle border
        if self.is_dark_mode:
            border_color = QColor(255, 255, 255, 50)
        else:
            border_color = QColor(0, 0, 0, 30)
        painter.setPen(border_color)
        painter.drawPath(path)
        
        # Success glow effect for unlocked achievements
        if hasattr(self, 'achievement') and getattr(self.achievement, 'unlocked', True):
            glow_color = QColor(self.theme.get('success', '#30D158'))
            glow_color.setAlpha(20)
            painter.setPen(Qt.NoPen)
            painter.setBrush(glow_color)
            glow_path = QPainterPath()
            glow_path.addRoundedRect(rect.adjusted(-5, -5, 5, 5), 20, 20)
            painter.drawPath(glow_path)

    def show_confetti(self):
        """Show celebratory confetti animation"""
        # Create and show confetti overlay
        self.confetti_overlay = ConfettiOverlay(self.parentWidget())
        self.confetti_overlay.show()


class ConfettiOverlay(QWidget):
    """Animated confetti overlay to celebrate achievements"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set up overlay properties
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(parent.geometry() if parent else QGuiApplication.primaryScreen().availableGeometry())
        
        # Confetti properties
        self.particle_count = 100
        self.colors = ["#FF453A", "#30D158", "#0A84FF", "#FFD60A", "#BF5AF2", "#FF9F0A"]
        self.confetti = []
        self.init_confetti()
        
        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_confetti)
        self.timer.start(16)  # ~60 FPS
        
        # Auto-close timer
        QTimer.singleShot(5000, self.close_animation)
    
    def init_confetti(self):
        """Initialize confetti particles"""
        for _ in range(self.particle_count):
            # Randomize starting position at the top
            x = random.randint(0, self.width())
            y = -random.randint(10, 100)
            
            # Randomize appearance and motion properties
            self.confetti.append({
                "x": x, 
                "y": y,
                "speed_x": random.uniform(-1, 1),  # Horizontal drift
                "speed_y": random.uniform(2, 5),   # Falling speed
                "color": QColor(random.choice(self.colors)),
                "size": random.randint(5, 15),
                "rotation": random.randint(0, 360),
                "rotation_speed": random.uniform(-2, 2),
                "shape": random.randint(0, 2)  # 0=rect, 1=circle, 2=triangle
            })
    
    def update_confetti(self):
        """Update confetti positions and properties for animation"""
        new_confetti = []
        for particle in self.confetti:
            # Update position
            particle["y"] += particle["speed_y"]
            particle["x"] += particle["speed_x"]
            
            # Update rotation
            particle["rotation"] += particle["rotation_speed"]
            
            # Keep particles that are still on screen
            if particle["y"] < self.height():
                new_confetti.append(particle)
        
        self.confetti = new_confetti
        
        # Stop timer when all confetti has fallen
        if not self.confetti:
            self.timer.stop()
            self.close()
            self.deleteLater()
        
        # Refresh display
        self.update()
    
    def paintEvent(self, event):
        """Draw confetti particles"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        for particle in self.confetti:
            painter.save()
            
            # Position and rotate
            painter.translate(particle["x"], particle["y"])
            painter.rotate(particle["rotation"])
            
            # Set color
            painter.setPen(Qt.NoPen)
            painter.setBrush(particle["color"])
            
            # Draw shape based on type
            size = particle["size"]
            if particle["shape"] == 0:  # Rectangle
                painter.drawRect(-size/2, -size/2, size, size/2)
            elif particle["shape"] == 1:  # Circle
                painter.drawEllipse(-size/2, -size/2, size, size)
            else:  # Triangle
                points = [
                    QPoint(0, -size/2),
                    QPoint(-size/2, size/2),
                    QPoint(size/2, size/2)
                ]
                painter.drawPolygon(points)
            
            painter.restore()
    
    def close_animation(self):
        """Gracefully close the animation"""
        # Fade out remaining particles
        for particle in self.confetti:
            particle["speed_y"] *= 1.5  # Speed up falling
        
        # Ensure we close even if some particles are still visible
        QTimer.singleShot(1000, self.close)


def show_achievement_notification(achievement, parent_widget=None, theme=None, play_sound=True):
    """
    Helper function to show an achievement notification
    
    Args:
        achievement: Achievement object with name, description, icon
        parent_widget: Parent widget for the notification
        theme: Theme dictionary with color definitions
        play_sound: Whether to play a sound effect
    """
    # Create and show notification
    notification = AchievementNotification(
        achievement, 
        parent=parent_widget,
        theme=theme
    )
    notification.show()
    
    # Play sound if requested and available
    if play_sound:
        try:
            from PyQt5.QtMultimedia import QSound
            from utils import resource_path
            sound_path = resource_path("assets/sounds/achievement.wav")
            QSound.play(sound_path)
        except:
            # Fallback sound method if QSound fails
            try:
                from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
                from PyQt5.QtCore import QUrl
                player = QMediaPlayer()
                sound_path = resource_path("assets/sounds/achievement.wav")
                player.setMedia(QMediaContent(QUrl.fromLocalFile(sound_path)))
                player.setVolume(60)
                player.play()
            except:
                # Silent fallback if sound fails
                pass
    
    return notification