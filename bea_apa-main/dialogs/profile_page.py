# dialogs/profile_page.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QWidget, QGridLayout, QFrame, QProgressBar,
    QStackedWidget, QGraphicsDropShadowEffect, QSizePolicy, QFileDialog, QTextEdit, QLineEdit,
    QCalendarWidget, QTabWidget, QFormLayout
)
from PyQt5.QtCore import (
    Qt, QSize, QPropertyAnimation, QEasingCurve, QTimer, 
    QDate, pyqtSignal, QPoint, QRect, pyqtProperty
)
from PyQt5.QtGui import (
    QPainter, QColor, QLinearGradient, QFont, QBrush, QPen, QPainterPath, 
    QPixmap, QImage, QRadialGradient, QFontMetrics
)

from dialogs.achievement_manager import AchievementManager, Achievement
from datetime import datetime, timedelta, date
import math
import os
import json
import random

class ZodiacSign:
    """Helper class to determine zodiac sign and characteristics based on birth date"""
    @staticmethod
    def get_zodiac_sign(birth_date):
        month = birth_date.month
        day = birth_date.day
        
        if (month == 3 and day >= 21) or (month == 4 and day <= 19):
            return "Aries", "♈"
        elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
            return "Taurus", "♉"
        elif (month == 5 and day >= 21) or (month == 6 and day <= 20):
            return "Gemini", "♊"
        elif (month == 6 and day >= 21) or (month == 7 and day <= 22):
            return "Cancer", "♋"
        elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
            return "Leo", "♌"
        elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
            return "Virgo", "♍"
        elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
            return "Libra", "♎"
        elif (month == 10 and day >= 23) or (month == 11 and day <= 21):
            return "Scorpio", "♏"
        elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
            return "Sagittarius", "♐"
        elif (month == 12 and day >= 22) or (month == 1 and day <= 19):
            return "Capricorn", "♑"
        elif (month == 1 and day >= 20) or (month == 2 and day <= 18):
            return "Aquarius", "♒"
        else:
            return "Pisces", "♓"
    
    @staticmethod
    def get_element(sign_name):
        fire_signs = ["Aries", "Leo", "Sagittarius"]
        earth_signs = ["Taurus", "Virgo", "Capricorn"]
        air_signs = ["Gemini", "Libra", "Aquarius"]
        water_signs = ["Cancer", "Scorpio", "Pisces"]
        
        if sign_name in fire_signs:
            return "Fire", "🔥"
        elif sign_name in earth_signs:
            return "Earth", "🌎"
        elif sign_name in air_signs:
            return "Air", "💨"
        elif sign_name in water_signs:
            return "Water", "💧"
        return "", ""

class CircularProfileImage(QFrame):
    """Custom widget for displaying a circular profile image with animations and effects"""
    clicked = pyqtSignal()
    
    def __init__(self, parent=None, size=100, theme=None):
        super().__init__(parent)
        self.parent = parent
        self.theme = theme if theme else {
            "is_dark": True,
            "primary": "#0A84FF",
            "success": "#30D158"
        }
        self.size = size
        self.setFixedSize(size, size)
        self.pixmap = None
        self.placeholder_emoji = "😀"
        self._halo_opacity = 0  # Store as a regular attribute, not property
        self.halo_color = QColor(self.theme.get("primary", "#0A84FF"))
        
        self.pulse_animation = None
        self.setStyleSheet("background-color: transparent;")
        
    def setupAnimation(self):
        # Set up animation separately from constructor
        if self.pulse_animation is None:
            self.pulse_animation = QPropertyAnimation(self, b"haloOpacity")
            self.pulse_animation.setStartValue(0)
            self.pulse_animation.setEndValue(70)
            self.pulse_animation.setDuration(1500)
            self.pulse_animation.setEasingCurve(QEasingCurve.InOutQuad)
            self.pulse_animation.setLoopCount(-1)
    
    def set_image(self, image_path=None):
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            self.pixmap = pixmap.scaled(self.size, self.size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        else:
            self.pixmap = None
        self.update()
    
    def set_emoji(self, emoji):
        self.placeholder_emoji = emoji
        self.update()
    
    def start_pulse(self):
        self.setupAnimation()
        if self.pulse_animation:
            self.pulse_animation.start()
    
    def stop_pulse(self):
        if self.pulse_animation:
            self.pulse_animation.stop()
            self.set_halo_opacity(0)
            self.update()
    
    def set_halo_opacity(self, value):
        self._halo_opacity = value
        self.update()
    
    def get_halo_opacity(self):
        return self._halo_opacity
    
    # Use pyqtProperty instead of direct property to avoid recursion
    haloOpacity = pyqtProperty(int, get_halo_opacity, set_halo_opacity)
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        
        center = self.rect().center()
        radius = self.size / 2
        
        # Draw pulsing halo if active
        if self._halo_opacity > 0:
            painter.save()
            # Set opacity for the halo
            halo_color = QColor(self.halo_color)
            halo_color.setAlpha(self._halo_opacity)
            painter.setBrush(QBrush(halo_color))
            painter.setPen(Qt.NoPen)
            # Draw halo slightly larger than the profile picture
            halo_radius = radius + 8  # Adjust for desired halo size
            painter.drawEllipse(center, halo_radius, halo_radius)
            painter.restore()
        
        # Draw the circular clipping path
        path = QPainterPath()
        path.addEllipse(center, radius - 2, radius - 2)  # Slightly smaller to avoid edge artifacts
        painter.setClipPath(path)
        
        # Draw either the image or a colored background with emoji
        if self.pixmap:
            # Calculate position to center the image in the clipped area
            x = (self.width() - self.pixmap.width()) / 2
            y = (self.height() - self.pixmap.height()) / 2
            painter.drawPixmap(int(x), int(y), self.pixmap)
        else:
            # Background gradient
            gradient = QRadialGradient(center, radius)
            gradient.setColorAt(0, QColor("#6d6dff"))
            gradient.setColorAt(1, QColor("#3a3aff"))
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(center, radius - 2, radius - 2)
            
            # Draw the emoji placeholder
            painter.setPen(QColor(255, 255, 255))
            font = painter.font()
            font.setPointSize(int(self.size / 3))
            painter.setFont(font)
            fontMetrics = QFontMetrics(font)
            text_width = fontMetrics.horizontalAdvance(self.placeholder_emoji)
            text_height = fontMetrics.height()
            
            # Convert float coordinates to integers for drawText
            x_pos = int((self.width() - text_width) / 2)
            y_pos = int((self.height() + text_height / 2) / 2)
            painter.drawText(x_pos, y_pos, self.placeholder_emoji)
        
        # Draw border
        painter.setClipping(False)
        pen = QPen(QColor(self.theme.get("primary", "#0A84FF")), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center, radius - 1, radius - 1)

class EmojiPicker(QDialog):
    """Dialog for selecting an emoji for profile picture"""
    emoji_selected = pyqtSignal(str)
    
    def __init__(self, parent=None, theme=None):
        super().__init__(parent)
        self.theme = theme if theme else {
            "is_dark": True,
            "background": "#1E1E1E",
            "surface": "#262626",
            "text": "#FFFFFF",
            "border": "#383838"
        }
        self.setWindowTitle("Choose an Emoji")
        self.setModal(True)
        self.setMinimumSize(400, 300)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Simple grid layout without tabs
        emoji_grid = QGridLayout()
        emoji_grid.setContentsMargins(10, 10, 10, 10)
        emoji_grid.setSpacing(10)
        
        # Combined emoji list
        emojis = [
            "😀", "😃", "😄", "😁", "😆", "😅", "🤣", "😂", "🙂", "🙃",
            "😉", "😊", "😇", "🥰", "😍", "🤩", "😘", "😗", "😚", "😙",
            "😋", "😛", "😜", "🤪", "😝", "🤑", "🤗", "🤭", "🤫", "🤔",
            "🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯"
        ]
        
        row, col = 0, 0
        for emoji in emojis:
            btn = QPushButton(emoji)
            btn.setObjectName("emojiButton")
            btn.setFixedSize(40, 40)
            # Use lambda with default argument to avoid closure issues
            btn.clicked.connect(lambda checked=False, e=emoji: self.select_emoji(e))
            emoji_grid.addWidget(btn, row, col)
            col += 1
            if col > 7:  # 8 emojis per row
                col = 0
                row += 1
        
        layout.addLayout(emoji_grid)
        
        # Button to cancel
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn, 0, Qt.AlignCenter)
        
        self.apply_styles()
        
    def select_emoji(self, emoji):
        self.emoji_selected.emit(emoji)
        self.accept()
        
    def apply_styles(self):
        is_dark = self.theme.get("is_dark", True)
        background = self.theme.get("background", "#1E1E1E" if is_dark else "#F5F5F7")
        surface = self.theme.get("surface", "#262626" if is_dark else "#FFFFFF")
        text = self.theme.get("text", "#FFFFFF" if is_dark else "#000000")
        border = self.theme.get("border", "#383838" if is_dark else "#D1D1D6")
        primary = self.theme.get("primary", "#0A84FF")
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {background};
            }}
            QPushButton#emojiButton {{
                background-color: transparent;
                border: 1px solid {border};
                border-radius: 6px;
                font-size: 18px;
            }}
            QPushButton#emojiButton:hover {{
                background-color: {primary}20;
                border: 1px solid {primary};
            }}
            QPushButton#cancelButton {{
                background-color: transparent;
                color: {text};
                border: 1px solid {border};
                border-radius: 15px;
                padding: 8px 16px;
            }}
            QPushButton#cancelButton:hover {{
                background-color: {primary}20;
                border: 1px solid {primary};
            }}
            """)
        
class AchievementCard(QFrame):
    """Widget to display a single achievement with Apple-inspired design"""
    def __init__(self, achievement, parent=None, theme=None):
        super().__init__(parent)
        self.achievement = achievement
        self.theme = theme if theme else {
            "is_dark": True,
            "background": "#1E1E1E",
            "surface": "#262626",
            "text": "#FFFFFF",
            "text_secondary": "#BBBBBB",
            "primary": "#0A84FF",
            "secondary": "#52A8FF",
            "success": "#30D158"
        }
        self.is_dark = self.theme.get("is_dark", True)
        
        # Set up card appearance
        self.setObjectName("achievementCard")
        self.setFixedHeight(110)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Apply shadow but with reduced blur to avoid performance issues
        shadow = QGraphicsDropShadowEffect(self)
        shadow_color = QColor(0, 0, 0, 40)
        shadow.setColor(shadow_color)
        shadow.setBlurRadius(6)
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Icon container - simplified
        icon_container = QFrame()
        icon_container.setObjectName("achievementIcon")
        icon_container.setFixedSize(60, 60)
        
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setSpacing(0)
        icon_layout.setAlignment(Qt.AlignCenter)
        
        # Simple icon mapping
        icon_map = {
            "water": "💧",
            "target": "🎯",
            "calendar": "📆",
            "trophy": "🏆",
            "badge": "🏅",
            "clock": "⏰",
            "star": "⭐",
            "fire": "🔥"
        }
        
        icon_text = icon_map.get(self.achievement.icon, "🏆")
        icon_label = QLabel(icon_text)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("background-color: transparent;")
        icon_font = QFont()
        icon_font.setPointSize(24)
        icon_label.setFont(icon_font)
        icon_layout.addWidget(icon_label)
        
        # Text content
        text_container = QWidget()
        text_container.setStyleSheet("background: transparent;")
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)
        
        # Simple header layout
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        name_label = QLabel(self.achievement.name)
        name_label.setObjectName("achievementName")
        name_label.setStyleSheet("background-color: transparent;")
        header_layout.addWidget(name_label, 1)
        
        # Show a badge for unlocked achievements
        if self.achievement.unlocked:
            unlocked_badge = QLabel("✓")
            unlocked_badge.setObjectName("unlockedBadge")
            unlocked_badge.setAlignment(Qt.AlignCenter)
            unlocked_badge.setFixedSize(20, 20)
            header_layout.addWidget(unlocked_badge, 0)
        
        text_layout.addLayout(header_layout)
        
        desc_label = QLabel(self.achievement.description)
        desc_label.setObjectName("achievementDescription")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("background-color: transparent;")
        text_layout.addWidget(desc_label)
        
        # Add progress or date info
        if self.achievement.unlocked:
            date_str = "Unlocked: " + self.format_date(self.achievement.unlock_date)
            date_label = QLabel(date_str)
            date_label.setObjectName("achievementDate")
            date_label.setStyleSheet("background-color: transparent;")
            text_layout.addWidget(date_label)
        elif hasattr(self.achievement, 'progress_max') and self.achievement.progress_max > 0:
            progress_container = QWidget()
            progress_container.setStyleSheet("background: transparent;")
            progress_layout = QHBoxLayout(progress_container)
            progress_layout.setContentsMargins(0, 4, 0, 0)
            progress_layout.setSpacing(8)
            
            # Simple progress bar
            progress_bar = QProgressBar()
            progress_bar.setObjectName("achievementProgress")
            progress_bar.setRange(0, self.achievement.progress_max)
            progress_bar.setValue(self.achievement.progress)
            progress_bar.setTextVisible(False)
            progress_bar.setFixedHeight(6)
            
            progress_text = QLabel(f"{self.achievement.progress}/{self.achievement.progress_max}")
            progress_text.setObjectName("progressText")
            progress_text.setStyleSheet("background-color: transparent;")
            
            progress_layout.addWidget(progress_bar, 1)
            progress_layout.addWidget(progress_text, 0)
            text_layout.addWidget(progress_container)
        
        layout.addWidget(icon_container)
        layout.addWidget(text_container, 1)
        
        self.apply_styles()
    
    def format_date(self, date):
        if not date:
            return "Unknown"
        now = datetime.now()
        delta = now - date
        if delta < timedelta(hours=24):
            return "Today"
        elif delta < timedelta(days=2):
            return "Yesterday"
        elif delta < timedelta(days=7):
            return date.strftime("%A")
        else:
            return date.strftime("%b %d, %Y")
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Only add subtle styling, avoid complex effects
        if self.achievement.unlocked:
            # Simple colored border for unlocked achievements
            pen = QPen(QColor(self.theme.get("success", "#30D158")))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)
    
    def apply_styles(self):
        background = self.theme.get("surface", "#262626" if self.is_dark else "#FFFFFF")
        border = self.theme.get("border", "#383838" if self.is_dark else "#D1D1D6")
        text = self.theme.get("text", "#FFFFFF" if self.is_dark else "#000000")
        text_secondary = self.theme.get("text_secondary", "#BBBBBB" if self.is_dark else "#6E6E6E")
        success = self.theme.get("success", "#30D158")
        primary = self.theme.get("primary", "#0A84FF")
        
        if self.achievement.unlocked:
            card_bg = success + "10"
            icon_bg = success + "cc"
        else:
            card_bg = background
            icon_bg = primary + "90"
        
        self.setStyleSheet(f"""
            QFrame#achievementCard {{
                background-color: {card_bg};
                border-radius: 12px;
                border: 1px solid {border};
            }}
            QFrame#achievementIcon {{
                background-color: {icon_bg};
                border-radius: 30px;
                color: white;
            }}
            QLabel#achievementName {{
                color: {text};
                font-size: 16px;
                font-weight: bold;
                background: transparent;
            }}
            QLabel#achievementDescription {{
                color: {text_secondary};
                font-size: 13px;
                background: transparent;
            }}
            QLabel#achievementDate {{
                color: {success if self.achievement.unlocked else text_secondary};
                font-size: 12px;
                font-style: italic;
                background: transparent;
            }}
            QLabel#progressText {{
                color: {text_secondary};
                font-size: 12px;
                background: transparent;
            }}
            QLabel#unlockedBadge {{
                color: white;
                background-color: {success};
                border-radius: 10px;
                font-size: 10px;
                font-weight: bold;
            }}
            QProgressBar#achievementProgress {{
                background-color: {border};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar#achievementProgress::chunk {{
                background-color: {primary};
                border-radius: 3px;
            }}
        """)

class EditProfileDialog(QDialog):
    """Dialog for editing profile information"""
    def __init__(self, parent=None, profile_data=None, theme=None):
        super().__init__(parent)
        self.theme = theme if theme else {
            "is_dark": True,
            "background": "#1E1E1E",
            "surface": "#262626",
            "text": "#FFFFFF",
            "text_secondary": "#BBBBBB",
            "primary": "#0A84FF",
            "secondary": "#52A8FF",
            "border": "#383838"
        }
        self.is_dark = self.theme.get("is_dark", True)
        self.profile_data = profile_data.copy() if profile_data else {}
        self.current_emoji = "😀"
        
        self.setWindowTitle("Edit Your Profile")
        self.setMinimumSize(500, 600)
        self.init_ui()
        self.load_profile_data()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # Header with title
        header_label = QLabel("Edit Your Profile")
        header_label.setObjectName("dialogHeader")
        header_label.setStyleSheet("background-color: transparent;")
        header_font = QFont()
        header_font.setPointSize(22)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_label)
        
        # Content layout
        content_layout = QVBoxLayout()
        content_layout.setSpacing(24)
        
        # Profile Picture Section
        pic_section = QFrame()
        pic_section.setObjectName("sectionFrame")
        pic_layout = QVBoxLayout(pic_section)
        pic_layout.setContentsMargins(16, 16, 16, 16)
        pic_layout.setSpacing(12)
        
        pic_title = QLabel("Profile Picture")
        pic_title.setObjectName("sectionTitle")
        pic_title.setStyleSheet("background-color: transparent;")
        pic_layout.addWidget(pic_title)
        
        # Profile picture with options
        pic_content = QWidget()
        pic_content.setStyleSheet("background-color: transparent;")
        pic_content_layout = QHBoxLayout(pic_content)
        pic_content_layout.setContentsMargins(0, 0, 0, 0)
        pic_content_layout.setSpacing(20)
        
        # Profile picture preview
        self.pic_preview = CircularProfileImage(size=100, theme=self.theme)
        pic_content_layout.addWidget(self.pic_preview, 0, Qt.AlignCenter)
        
        # Picture options
        pic_options = QWidget()
        pic_options.setStyleSheet("background-color: transparent;")
        pic_options_layout = QVBoxLayout(pic_options)
        pic_options_layout.setContentsMargins(0, 0, 0, 0)
        pic_options_layout.setSpacing(8)
        
        self.upload_pic_btn = QPushButton("Upload Picture")
        self.upload_pic_btn.setObjectName("uploadButton")
        self.upload_pic_btn.clicked.connect(self.upload_picture)
        
        self.emoji_pic_btn = QPushButton("Choose Emoji")
        self.emoji_pic_btn.setObjectName("emojiButton")
        self.emoji_pic_btn.clicked.connect(self.choose_emoji)
        
        pic_options_layout.addWidget(self.upload_pic_btn)
        pic_options_layout.addWidget(self.emoji_pic_btn)
        pic_options_layout.addStretch()
        
        pic_content_layout.addWidget(pic_options)
        pic_layout.addWidget(pic_content)
        
        content_layout.addWidget(pic_section)
        
        # Basic Info Section
        basic_section = QFrame()
        basic_section.setObjectName("sectionFrame")
        basic_layout = QVBoxLayout(basic_section)
        basic_layout.setContentsMargins(16, 16, 16, 16)
        basic_layout.setSpacing(12)
        
        basic_title = QLabel("Basic Information")
        basic_title.setObjectName("sectionTitle")
        basic_title.setStyleSheet("background-color: transparent;")
        basic_layout.addWidget(basic_title)
        
        # Form layout
        form = QWidget()
        form.setStyleSheet("background-color: transparent;")
        form_layout = QFormLayout(form)
        form_layout.setContentsMargins(0, 8, 0, 0)
        form_layout.setSpacing(16)
        
        name_label = QLabel("Name:")
        name_label.setStyleSheet("background-color: transparent;")
        self.name_edit = QLineEdit()
        self.name_edit.setObjectName("inputField")
        self.name_edit.setPlaceholderText("Your full name")
        
        username_label = QLabel("Username:")
        username_label.setStyleSheet("background-color: transparent;")
        self.username_edit = QLineEdit()
        self.username_edit.setObjectName("inputField")
        self.username_edit.setPlaceholderText("Choose a username (no spaces)")
        self.username_edit.textChanged.connect(self.validate_username)
        
        bio_label = QLabel("Bio:")
        bio_label.setStyleSheet("background-color: transparent;")
        self.bio_edit = QTextEdit()
        self.bio_edit.setObjectName("bioField")
        self.bio_edit.setPlaceholderText("Tell the world about yourself")
        self.bio_edit.setMaximumHeight(100)
        
        location_label = QLabel("Location:")
        location_label.setStyleSheet("background-color: transparent;")
        self.location_edit = QLineEdit()
        self.location_edit.setObjectName("inputField")
        self.location_edit.setPlaceholderText("City, Country (optional)")
        
        form_layout.addRow(name_label, self.name_edit)
        form_layout.addRow(username_label, self.username_edit)
        form_layout.addRow(bio_label, self.bio_edit)
        form_layout.addRow(location_label, self.location_edit)
        
        basic_layout.addWidget(form)
        content_layout.addWidget(basic_section)
        
        # Personal Info Section
        personal_section = QFrame()
        personal_section.setObjectName("sectionFrame")
        personal_layout = QVBoxLayout(personal_section)
        personal_layout.setContentsMargins(16, 16, 16, 16)
        personal_layout.setSpacing(12)
        
        personal_title = QLabel("Personal Details")
        personal_title.setObjectName("sectionTitle")
        personal_title.setStyleSheet("background-color: transparent;")
        personal_layout.addWidget(personal_title)
        
        # Personal details form
        personal_form = QWidget()
        personal_form.setStyleSheet("background-color: transparent;")
        personal_form_layout = QFormLayout(personal_form)
        personal_form_layout.setContentsMargins(0, 8, 0, 0)
        personal_form_layout.setSpacing(16)
        
        # Birthday calendar
        birthday_label = QLabel("Birthday:")
        birthday_label.setStyleSheet("background-color: transparent;")
        self.birthday_calendar = QCalendarWidget()
        self.birthday_calendar.setObjectName("calendarWidget")
        self.birthday_calendar.setGridVisible(False)
        self.birthday_calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.birthday_calendar.setMinimumDate(QDate(1900, 1, 1))
        self.birthday_calendar.setMaximumDate(QDate.currentDate())
        
        personal_form_layout.addRow(birthday_label, self.birthday_calendar)
        
        personal_layout.addWidget(personal_form)
        content_layout.addWidget(personal_section)
        
        main_layout.addLayout(content_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(16)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Save Changes")
        save_btn.setObjectName("saveButton")
        save_btn.clicked.connect(self.save_profile)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        main_layout.addLayout(button_layout)
        
        self.apply_styles()
    
    def validate_username(self, text):
        """Ensure username only contains valid characters"""
        valid_text = ''.join(c for c in text if c.isalnum() or c == '_')
        if valid_text != text:
            cursor_pos = self.username_edit.cursorPosition()
            self.username_edit.setText(valid_text)
            self.username_edit.setCursorPosition(max(0, cursor_pos - (len(text) - len(valid_text))))
    
    def load_profile_data(self):
        """Load current profile data into form fields"""
        if not self.profile_data:
            return
        
        # Basic info
        self.name_edit.setText(self.profile_data.get("name", ""))
        self.username_edit.setText(self.profile_data.get("username", ""))
        self.bio_edit.setText(self.profile_data.get("bio", ""))
        self.location_edit.setText(self.profile_data.get("location", ""))
        
        # Personal details
        birth_date = self.profile_data.get("birth_date", QDate.currentDate().addYears(-25))
        self.birthday_calendar.setSelectedDate(birth_date)
        
        # Profile picture
        if self.profile_data.get("profile_pic"):
            self.pic_preview.set_image(self.profile_data["profile_pic"])
        else:
            # Use name initial for emoji
            name = self.profile_data.get("name", "")
            if name:
                initial = name[0].upper()
                # Map initial to an emoji
                emoji_map = {
                    'A': '😀', 'B': '😊', 'C': '🙂', 'D': '😎', 'E': '🤓',
                    'F': '😄', 'G': '😃', 'H': '😁', 'I': '😉', 'J': '😍',
                    'K': '🥰', 'L': '😇', 'M': '🤩', 'N': '🥳', 'O': '😌',
                    'P': '😏', 'Q': '😺', 'R': '🤠', 'S': '🧐', 'T': '🤔',
                    'U': '😜', 'V': '😝', 'W': '😛', 'X': '🤪', 'Y': '😋',
                    'Z': '😚'
                }
                emoji = emoji_map.get(initial, '😀')
                self.current_emoji = emoji
                self.pic_preview.set_emoji(emoji)
    
    def upload_picture(self):
        """Open file dialog to select a profile picture"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Profile Picture", "", "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.pic_preview.set_image(file_path)
            self.profile_data["profile_pic"] = file_path
    
    def choose_emoji(self):
        """Open emoji picker dialog"""
        emoji_picker = EmojiPicker(self, theme=self.theme)
        emoji_picker.emoji_selected.connect(self.set_emoji)
        emoji_picker.exec_()
    
    def set_emoji(self, emoji):
        """Set the selected emoji as profile picture"""
        self.current_emoji = emoji
        self.pic_preview.set_emoji(emoji)
        # Clear any existing profile picture
        self.profile_data["profile_pic"] = None
    
    def save_profile(self):
        """Save profile changes and return data"""
        # Validate required fields
        if not self.name_edit.text() or not self.username_edit.text():
            return
        
        # Update profile data
        self.profile_data["name"] = self.name_edit.text()
        self.profile_data["username"] = self.username_edit.text()
        self.profile_data["bio"] = self.bio_edit.toPlainText()
        self.profile_data["location"] = self.location_edit.text()
        self.profile_data["birth_date"] = self.birthday_calendar.selectedDate()
        
        # Accept dialog
        self.accept()
    
    def get_profile_data(self):
        """Return the updated profile data"""
        return self.profile_data
    
    def apply_styles(self):
        is_dark = self.theme.get("is_dark", True)
        background = self.theme.get("background", "#1E1E1E" if is_dark else "#F5F5F7")
        surface = self.theme.get("surface", "#262626" if is_dark else "#FFFFFF")
        text = self.theme.get("text", "#FFFFFF" if is_dark else "#000000")
        text_secondary = self.theme.get("text_secondary", "#BBBBBB" if is_dark else "#6E6E6E")
        primary = self.theme.get("primary", "#0A84FF")
        border = self.theme.get("border", "#383838" if is_dark else "#D1D1D6")
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {background};
            }}
            QLabel#dialogHeader {{
                color: {text};
                font-size: 22px;
                font-weight: bold;
                padding-bottom: 8px;
                background-color: transparent;
            }}
            QFrame#sectionFrame {{
                background-color: {surface};
                border-radius: 16px;
                border: 1px solid {border};
            }}
            QLabel#sectionTitle {{
                color: {text};
                font-size: 18px;
                font-weight: bold;
                background-color: transparent;
            }}
            QLineEdit#inputField, QTextEdit#bioField {{
                background-color: {surface};
                color: {text};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
            }}
            QLineEdit#inputField:focus, QTextEdit#bioField:focus {{
                border: 1px solid {primary};
            }}
            QCalendarWidget#calendarWidget {{
                background-color: {surface};
                color: {text};
                selection-background-color: {primary};
                selection-color: white;
            }}
            QPushButton#uploadButton, QPushButton#emojiButton {{
                background-color: {primary};
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 16px;
                font-size: 14px;
            }}
            QPushButton#saveButton {{
                background-color: {primary};
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 16px;
                font-size: 14px;
            }}
            QPushButton#cancelButton {{
                background-color: transparent;
                color: {text};
                border: 1px solid {border};
                border-radius: 15px;
                padding: 8px 16px;
                font-size: 14px;
            }}
        """)

class StatsWidget(QFrame):
    """Widget to display user hydration statistics"""
    def __init__(self, parent=None, theme=None):
        super().__init__(parent)
        self.theme = theme if theme else {
            "is_dark": True,
            "background": "#1E1E1E",
            "surface": "#262626", 
            "text": "#FFFFFF",
            "text_secondary": "#BBBBBB",
            "primary": "#0A84FF",
            "secondary": "#52A8FF",
            "success": "#30D158"
        }
        self.is_dark = self.theme.get("is_dark", True)
        self.setObjectName("statsWidget")
        self.setMinimumHeight(200)
        
        # Simple shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow_color = QColor(0, 0, 0, 40)
        shadow.setColor(shadow_color)
        shadow.setBlurRadius(6)  # Reduced blur radius
        shadow.setOffset(0, 2)  # Smaller offset
        self.setGraphicsEffect(shadow)
        
        self.init_ui()
        self.stats = {
            "total_drinks": 0,
            "days_tracked": 0,
            "current_streak": 0,
            "best_streak": 0,
            "avg_per_day": 0,
            "completion_rate": 0,
            "best_day": "N/A",
            "weekly_total": 0
        }
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header with title
        title = QLabel("Hydration Statistics")
        title.setObjectName("statsTitle")
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("background-color: transparent;")
        layout.addWidget(title)
        
        # Stats grid - simplified
        stats_grid = QGridLayout()
        stats_grid.setHorizontalSpacing(20)
        stats_grid.setVerticalSpacing(20)
        
        # Main stats with icons - using simpler method to create stats
        stats_data = [
            ("Total Drinks", "total_drinks", "🥤", 0, 0),
            ("Days Tracked", "days_tracked", "📆", 0, 1),
            ("Current Streak", "current_streak", "🔥", 0, 2),
            ("Best Streak", "best_streak", "🏆", 1, 0),
            ("Daily Average", "avg_per_day", "📊", 1, 1),
            ("Completion Rate", "completion_rate", "✅", 1, 2, True)
        ]
        
        for stat_info in stats_data:
            if len(stat_info) == 6:
                label_text, stat_key, icon, row, col, show_percent = stat_info
            else:
                label_text, stat_key, icon, row, col = stat_info
                show_percent = False
                
            self.create_stat_item(stats_grid, label_text, stat_key, row, col, icon, show_percent)
        
        layout.addLayout(stats_grid)
        
        # Additional stats section - simplified
        additional_layout = QHBoxLayout()
        additional_layout.setSpacing(20)
        
        # Best day info
        best_day_frame = QFrame()
        best_day_frame.setObjectName("miniStatCard")
        best_day_layout = QHBoxLayout(best_day_frame)
        best_day_layout.setSpacing(12)
        
        best_day_icon = QLabel("🌞")
        best_day_icon.setObjectName("miniStatIcon")
        best_day_icon.setAlignment(Qt.AlignCenter)
        best_day_icon.setStyleSheet("background-color: transparent;")
        
        best_day_info = QVBoxLayout()
        best_day_info.setSpacing(2)
        
        best_day_label = QLabel("Best Day")
        best_day_label.setObjectName("miniStatLabel")
        best_day_label.setStyleSheet("background-color: transparent;")
        
        self.best_day_value = QLabel("N/A")
        self.best_day_value.setObjectName("miniStatValue")
        self.best_day_value.setStyleSheet("background-color: transparent;")
        
        best_day_info.addWidget(best_day_label)
        best_day_info.addWidget(self.best_day_value)
        
        best_day_layout.addWidget(best_day_icon)
        best_day_layout.addLayout(best_day_info)
        
        # Weekly total info
        weekly_frame = QFrame()
        weekly_frame.setObjectName("miniStatCard")
        weekly_layout = QHBoxLayout(weekly_frame)
        weekly_layout.setSpacing(12)
        
        weekly_icon = QLabel("📅")
        weekly_icon.setObjectName("miniStatIcon")
        weekly_icon.setAlignment(Qt.AlignCenter)
        weekly_icon.setStyleSheet("background-color: transparent;")
        
        weekly_info = QVBoxLayout()
        weekly_info.setSpacing(2)
        
        weekly_label = QLabel("This Week")
        weekly_label.setObjectName("miniStatLabel")
        weekly_label.setStyleSheet("background-color: transparent;")
        
        self.weekly_value = QLabel("0 drinks")
        self.weekly_value.setObjectName("miniStatValue")
        self.weekly_value.setStyleSheet("background-color: transparent;")
        
        weekly_info.addWidget(weekly_label)
        weekly_info.addWidget(self.weekly_value)
        
        weekly_layout.addWidget(weekly_icon)
        weekly_layout.addLayout(weekly_info)
        
        additional_layout.addWidget(best_day_frame)
        additional_layout.addWidget(weekly_frame)
        
        layout.addLayout(additional_layout)
        
        self.apply_styles()
    
    def create_stat_item(self, grid, label_text, stat_key, row, col, icon=None, show_percent=False):
        """Create a stat display item - simplified implementation"""
        container = QFrame()
        container.setObjectName("statCard")
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(16, 16, 16, 16)
        container_layout.setSpacing(8)
        
        # Header with icon and label
        header = QWidget()
        header.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        if icon:
            icon_label = QLabel(icon)
            icon_label.setObjectName("statIcon")
            icon_label.setStyleSheet("background-color: transparent;")
            header_layout.addWidget(icon_label)
        
        desc_label = QLabel(label_text)
        desc_label.setObjectName("statLabel")
        desc_label.setStyleSheet("background-color: transparent;")
        header_layout.addWidget(desc_label, 1)
        
        container_layout.addWidget(header)
        
        # Value display
        value_label = QLabel("0")
        if show_percent:
            value_label.setText("0%")
        value_label.setObjectName(f"stat_{stat_key}")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("background-color: transparent;")
        
        # Use a regular font instead of setting size to avoid potential recursion
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        value_label.setFont(font)
        
        container_layout.addWidget(value_label)
        
        grid.addWidget(container, row, col)
        setattr(self, f"label_{stat_key}", value_label)
    
    def update_stats(self, stats):
        """Update stats - simple implementation without animations"""
        self.stats = stats
        
        # Update the main stats
        for key, value in stats.items():
            label = getattr(self, f"label_{key}", None)
            if label:
                if key == "completion_rate":
                    label.setText(f"{int(value)}%")
                elif key == "avg_per_day":
                    label.setText(f"{value:.1f}")
                else:
                    label.setText(str(int(value)))
        
        # Update additional stats
        if "best_day" in stats:
            self.best_day_value.setText(stats["best_day"])
        
        if "weekly_total" in stats:
            self.weekly_value.setText(f"{stats['weekly_total']} drinks")
    
    def apply_styles(self):
        """Apply simplified styling"""
        background = self.theme.get("surface", "#262626" if self.is_dark else "#FFFFFF")
        text = self.theme.get("text", "#FFFFFF" if self.is_dark else "#000000")
        text_secondary = self.theme.get("text_secondary", "#BBBBBB" if self.is_dark else "#6E6E6E")
        primary = self.theme.get("primary", "#0A84FF")
        border = self.theme.get("border", "#383838" if self.is_dark else "#D1D1D6")
        card_bg = self.theme.get("card_bg", "#323232" if self.is_dark else "#F5F5F7")
        
        self.setStyleSheet(f"""
            QFrame#statsWidget {{
                background-color: {background};
                border-radius: 16px;
                border: 1px solid {border};
            }}
            QLabel#statsTitle {{
                color: {text};
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }}
            QFrame#statCard {{
                background-color: {card_bg};
                border-radius: 12px;
                border: 1px solid {border};
            }}
            QLabel#statIcon {{
                font-size: 16px;
                background: transparent;
            }}
            QLabel#statLabel {{
                color: {text_secondary};
                font-size: 14px;
                background: transparent;
            }}
            QLabel[objectName^="stat_"] {{
                color: {primary};
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }}
            QFrame#miniStatCard {{
                background-color: {card_bg};
                border-radius: 12px;
                border: 1px solid {border};
            }}
            QLabel#miniStatIcon {{
                font-size: 18px;
                background: transparent;
            }}
            QLabel#miniStatLabel {{
                color: {text_secondary};
                font-size: 12px;
                background: transparent;
            }}
            QLabel#miniStatValue {{
                color: {text};
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }}
        """)
class ProfilePage(QDialog):
    """Enhanced dialog to display user profile - simplified and more compact"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.setWindowTitle("My Profile")
        self.setMinimumSize(800, 600)  # Reduced size
        
        # Get theme from parent or use default
        self.theme = {}
        if hasattr(parent, 'get_theme'):
            self.theme = parent.get_theme()
        else:
            # Default theme
            self.theme = {
                "is_dark": True,
                "background": "#1E1E1E",
                "surface": "#262626",
                "text": "#FFFFFF",
                "text_secondary": "#BBBBBB",
                "primary": "#0A84FF",
                "secondary": "#52A8FF",
                "success": "#30D158",
                "border": "#383838",
                "card_bg": "#323232"
            }
        
        # Initialize achievement manager
        if hasattr(parent, 'settings_manager'):
            self.achievement_manager = AchievementManager(parent.settings_manager)
        else:
            self.achievement_manager = AchievementManager()
        
        # Set window flags for a more modern look
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """Initialize the UI with a simplified layout to avoid recursion"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create a tab widget with reduced features
        self.tabs = QTabWidget()
        self.tabs.setObjectName("profileTabs")
        
        # Create the tabs
        self.profile_tab = QWidget()
        self.achievements_tab = QWidget()
        
        # Set up each tab's content
        self.setup_profile_tab()
        self.setup_achievements_tab()
        
        # Add tabs to the tab widget
        self.tabs.addTab(self.profile_tab, "Profile")
        self.tabs.addTab(self.achievements_tab, "Achievements")
        
        # Add the tabs to the main layout
        self.main_layout.addWidget(self.tabs)
        
        self.apply_styles()
    
    def setup_profile_tab(self):
        """Set up the profile information tab - simplified"""
        layout = QVBoxLayout(self.profile_tab)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)
        
        # Create profile info widget
        self.profile_info = ProfileInfoWidget(theme=self.theme)
        layout.addWidget(self.profile_info)
        
        # Stats widget
        self.stats_widget = StatsWidget(theme=self.theme)
        layout.addWidget(self.stats_widget)
        
        layout.addStretch()
    
    def setup_achievements_tab(self):
        """Set up the achievements tab - simplified"""
        layout = QVBoxLayout(self.achievements_tab)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)
        
        # Simple header
        title = QLabel("Achievements")
        title.setObjectName("pageTitle")
        title.setStyleSheet("background-color: transparent;")
        layout.addWidget(title)
        
        self.achievement_summary = QLabel("You've unlocked 0/0 achievements")
        self.achievement_summary.setObjectName("pageSummary")
        self.achievement_summary.setStyleSheet("background-color: transparent;")
        layout.addWidget(self.achievement_summary)
        
        # Filter buttons
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(8)
        
        self.all_btn = QPushButton("All")
        self.all_btn.setObjectName("viewButton")
        self.all_btn.setCheckable(True)
        self.all_btn.setChecked(True)
        self.all_btn.clicked.connect(lambda: self.switch_view("all"))
        
        self.unlocked_btn = QPushButton("Unlocked")
        self.unlocked_btn.setObjectName("viewButton")
        self.unlocked_btn.setCheckable(True)
        self.unlocked_btn.clicked.connect(lambda: self.switch_view("unlocked"))
        
        self.locked_btn = QPushButton("Locked")
        self.locked_btn.setObjectName("viewButton")
        self.locked_btn.setCheckable(True)
        self.locked_btn.clicked.connect(lambda: self.switch_view("locked"))
        
        filter_layout.addWidget(self.all_btn)
        filter_layout.addWidget(self.unlocked_btn)
        filter_layout.addWidget(self.locked_btn)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Achievements stacked view
        self.achievements_stack = QStackedWidget()
        
        # Create scroll areas for each view
        self.all_view = QScrollArea()
        self.all_view.setWidgetResizable(True)
        self.all_view.setFrameShape(QFrame.NoFrame)
        self.all_view.setWidget(QWidget())
        self.all_view.widget().setLayout(QVBoxLayout())
        self.all_view.widget().layout().setContentsMargins(0, 0, 0, 0)
        self.all_view.widget().layout().setSpacing(12)
        self.all_view.widget().layout().setAlignment(Qt.AlignTop)
        
        self.unlocked_view = QScrollArea()
        self.unlocked_view.setWidgetResizable(True)
        self.unlocked_view.setFrameShape(QFrame.NoFrame)
        self.unlocked_view.setWidget(QWidget())
        self.unlocked_view.widget().setLayout(QVBoxLayout())
        self.unlocked_view.widget().layout().setContentsMargins(0, 0, 0, 0)
        self.unlocked_view.widget().layout().setSpacing(12)
        self.unlocked_view.widget().layout().setAlignment(Qt.AlignTop)
        
        self.locked_view = QScrollArea()
        self.locked_view.setWidgetResizable(True)
        self.locked_view.setFrameShape(QFrame.NoFrame)
        self.locked_view.setWidget(QWidget())
        self.locked_view.widget().setLayout(QVBoxLayout())
        self.locked_view.widget().layout().setContentsMargins(0, 0, 0, 0)
        self.locked_view.widget().layout().setSpacing(12)
        self.locked_view.widget().layout().setAlignment(Qt.AlignTop)
        
        self.achievements_stack.addWidget(self.all_view)
        self.achievements_stack.addWidget(self.unlocked_view)
        self.achievements_stack.addWidget(self.locked_view)
        
        layout.addWidget(self.achievements_stack)
    
    def switch_view(self, view_type):
        """Switch between achievement views"""
        self.all_btn.setChecked(view_type == "all")
        self.unlocked_btn.setChecked(view_type == "unlocked")
        self.locked_btn.setChecked(view_type == "locked")
        
        if view_type == "all":
            self.achievements_stack.setCurrentIndex(0)
        elif view_type == "unlocked":
            self.achievements_stack.setCurrentIndex(1)
        elif view_type == "locked":
            self.achievements_stack.setCurrentIndex(2)
    
    def load_data(self):
        """Load profile data and achievements"""
        # Read settings from settings.json if possible
        profile_data = {
            "name": "Alex Hydration",
            "username": "hydrohomie",
            "bio": "Staying hydrated and healthy one sip at a time!",
            "birth_date": QDate(1990, 6, 15),
            "join_date": datetime.now() - timedelta(days=random.randint(30, 365)),
            "location": "San Francisco, CA",
        }
        
        # Try to load from settings.json
        try:
            if hasattr(self.parent_app, 'settings_manager') and self.parent_app.settings_manager:
                user_data = self.parent_app.settings_manager.get("user_profile")
                if user_data:
                    if "name" in user_data:
                        profile_data["name"] = user_data["name"]
                    if "username" in user_data:
                        profile_data["username"] = user_data["username"]
                    if "bio" in user_data:
                        profile_data["bio"] = user_data["bio"]
                    if "location" in user_data:
                        profile_data["location"] = user_data["location"]
                    if "birth_date" in user_data:
                        try:
                            birth_date = QDate.fromString(user_data["birth_date"], "yyyy-MM-dd")
                            if birth_date.isValid():
                                profile_data["birth_date"] = birth_date
                        except:
                            pass
                    if "join_date" in user_data:
                        try:
                            join_date = datetime.fromisoformat(user_data["join_date"])
                            profile_data["join_date"] = join_date
                        except:
                            pass
        except Exception as e:
            print(f"Error loading user profile: {e}")
            
        # Set profile data
        self.profile_info.set_profile_data(profile_data)
        
        # Display achievements
        self.display_achievements()
        
        # Update stats from settings.json
        self.update_stats()
    
    def calculate_stats(self):
        """Calculate hydration statistics from settings.json"""
        stats = {
            "total_drinks": 0,
            "days_tracked": 0,
            "current_streak": 0,
            "best_streak": 0,
            "avg_per_day": 0,
            "completion_rate": 0,
            "best_day": "N/A",
            "weekly_total": 0
        }
        
        # Get data from settings.json
        history = {}
        daily_goal = 8
        current_count = 0
        today = datetime.now().date()
        
        try:
            # Try to get data from settings manager
            if hasattr(self.parent_app, 'settings_manager') and self.parent_app.settings_manager:
                # Get history
                history_data = self.parent_app.settings_manager.get("history")
                if history_data and isinstance(history_data, dict):
                    history = history_data
                
                # Get daily goal
                daily_goal_value = self.parent_app.settings_manager.get("daily_goal")
                if daily_goal_value and isinstance(daily_goal_value, (int, float)):
                    daily_goal = int(daily_goal_value)
                
                # Get current day's count
                current_count_value = self.parent_app.settings_manager.get("log_count")
                if current_count_value and isinstance(current_count_value, (int, float)):
                    current_count = int(current_count_value)
        except Exception as e:
            print(f"Error reading settings: {e}")
        
        # If no history data found, create sample data
        if not history:
            # For testing/demo purposes, generate some sample data
            for i in range(30):
                date_key = (today - timedelta(days=i)).isoformat()
                # Random count, more likely to meet goal than not
                count = random.randint(daily_goal - 3, daily_goal + 3)
                if count < 0:
                    count = 0
                history[date_key] = count
            
            current_count = random.randint(0, daily_goal)
        
        if history:
            # Calculate total drinks
            total_past = sum(history.values())
            total_drinks = total_past + current_count
            days_tracked = len(history) + 1  # +1 for today
            
            # Calculate average per day
            avg_per_day = total_drinks / days_tracked if days_tracked > 0 else 0
            
            # Calculate completion rate
            goals_met = sum(1 for count in history.values() if count >= daily_goal)
            completion_rate = int((goals_met / len(history)) * 100) if history else 0
            
            # Calculate streaks
            dates = sorted([datetime.fromisoformat(date_str).date() for date_str in history.keys()])
            
            # Simple streak calculation
            current_streak = 1  # Start with today
            streak_count = 1
            best_streak = 1
            
            # Find best streak
            for i in range(len(dates) - 1):
                if (dates[i] - dates[i+1]).days == 1:  # Consecutive days
                    streak_count += 1
                else:
                    streak_count = 1
                
                if streak_count > best_streak:
                    best_streak = streak_count
            
            # Find best day
            if history:
                best_day_key = max(history.items(), key=lambda x: x[1])[0]
                best_day_date = datetime.fromisoformat(best_day_key).date()
                day_diff = (today - best_day_date).days
                
                if day_diff == 0:
                    best_day = "Today"
                elif day_diff == 1:
                    best_day = "Yesterday"
                elif day_diff < 7:
                    best_day = best_day_date.strftime("%A")
                else:
                    best_day = best_day_date.strftime("%b %d")
                
                best_day += f" ({history[best_day_key]} drinks)"
            else:
                best_day = "N/A"
            
            # Calculate weekly total
            week_start = today - timedelta(days=today.weekday())
            weekly_total = sum(count for date_str, count in history.items() 
                             if datetime.fromisoformat(date_str).date() >= week_start)
            weekly_total += current_count  # Add today's count
            
            stats.update({
                "total_drinks": total_drinks,
                "days_tracked": days_tracked,
                "current_streak": current_streak,
                "best_streak": best_streak,
                "avg_per_day": avg_per_day,
                "completion_rate": completion_rate,
                "best_day": best_day,
                "weekly_total": weekly_total
            })
        
        return stats
    
    def update_stats(self):
        """Update statistics display using data from settings.json"""
        stats = self.calculate_stats()
        self.stats_widget.update_stats(stats)
    
    def display_achievements(self):
        """Display achievements in the appropriate views - simplified"""
        # Clear existing achievements from each view
        for view in [self.all_view, self.unlocked_view, self.locked_view]:
            layout = view.widget().layout()
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        
        # Get achievements from manager
        all_achievements = self.achievement_manager.achievements
        unlocked_achievements = [a for a in all_achievements if getattr(a, 'unlocked', False)]
        locked_achievements = [a for a in all_achievements if not getattr(a, 'unlocked', False)]
        
        # Create achievement cards for each view
        self.create_achievement_cards(all_achievements, self.all_view.widget().layout())
        self.create_achievement_cards(unlocked_achievements, self.unlocked_view.widget().layout())
        self.create_achievement_cards(locked_achievements, self.locked_view.widget().layout())
        
        # Update achievement summary
        total = len(all_achievements)
        unlocked = len(unlocked_achievements)
        self.achievement_summary.setText(f"You've unlocked {unlocked}/{total} achievements")
    
    def create_achievement_cards(self, achievements, layout):
        """Create and add achievement cards to the specified layout - simplified"""
        if not achievements:
            empty_label = QLabel("No achievements to display")
            empty_label.setObjectName("emptyLabel")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("background-color: transparent;")
            layout.addWidget(empty_label)
            return
        
        # Add achievements directly without complex categorization
        for achievement in achievements:
            card = AchievementCard(achievement, theme=self.theme)
            layout.addWidget(card)
        
        layout.addStretch()
    
    def apply_styles(self):
        """Apply simplified styles to avoid recursion issues"""
        is_dark = self.theme.get("is_dark", True)
        background = self.theme.get("background", "#1E1E1E" if is_dark else "#F5F5F7")
        surface = self.theme.get("surface", "#262626" if is_dark else "#FFFFFF")
        text = self.theme.get("text", "#FFFFFF" if is_dark else "#000000")
        text_secondary = self.theme.get("text_secondary", "#BBBBBB" if is_dark else "#6E6E6E")
        primary = self.theme.get("primary", "#0A84FF")
        border = self.theme.get("border", "#383838" if is_dark else "#D1D1D6")
        success = self.theme.get("success", "#30D158")
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {background};
            }}
            QTabWidget#profileTabs {{
                background-color: {background};
            }}
            QTabWidget::pane {{
                border: none;
                background: {background};
            }}
            QTabBar::tab {{
                background: {surface}80;
                color: {text};
                min-width: 100px;
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
            QTabBar::tab:selected {{
                background: {primary};
                color: white;
            }}
            QLabel#pageTitle {{
                color: {text};
                font-size: 24px;
                font-weight: bold;
            }}
            QLabel#pageSummary {{
                color: {text_secondary};
                font-size: 16px;
            }}
            QPushButton#viewButton {{
                background-color: transparent;
                color: {text};
                border: 1px solid {border};
                border-radius: 15px;
                padding: 8px 20px;
                font-size: 14px;
            }}
            QPushButton#viewButton:checked {{
                background-color: {primary};
                color: white;
                border: none;
            }}
            QPushButton#viewButton:hover:!checked {{
                background-color: {surface};
            }}
            QLabel#emptyLabel {{
                color: {text_secondary};
                font-size: 16px;
                font-style: italic;
                padding: 40px;
            }}
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {border};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
class ProfileInfoWidget(QWidget):
    """Widget that displays user profile information in a compact layout"""
    def __init__(self, parent=None, theme=None):
        super().__init__(parent)
        self.theme = theme if theme else {
            "is_dark": True,
            "background": "#1E1E1E",
            "surface": "#262626",
            "text": "#FFFFFF",
            "text_secondary": "#BBBBBB",
            "primary": "#0A84FF",
            "secondary": "#52A8FF",
            "success": "#30D158",
            "border": "#383838"
        }
        self.is_dark = self.theme.get("is_dark", True)
        
        # Default profile data
        self.profile_data = {
            "name": "Your Name",
            "username": "username",
            "bio": "Your bio appears here. Tell the world about yourself!",
            "birth_date": QDate.currentDate().addYears(-25),
            "join_date": datetime.now() - timedelta(days=random.randint(30, 365)),
            "location": "",
        }
        
        self.init_ui()
        self.update_zodiac_info()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)
        
        # Top section with picture and name
        top_section = QWidget()
        top_section.setStyleSheet("background-color: transparent;")
        top_layout = QHBoxLayout(top_section)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(20)
        
        # Profile picture
        self.profile_pic = CircularProfileImage(size=110, theme=self.theme)
        self.profile_pic.clicked.connect(self.edit_profile)
        top_layout.addWidget(self.profile_pic, 0, Qt.AlignTop)
        
        # Name, username, and bio
        name_section = QWidget()
        name_section.setStyleSheet("background-color: transparent;")
        name_layout = QVBoxLayout(name_section)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(4)
        
        self.name_label = QLabel(self.profile_data["name"])
        self.name_label.setObjectName("profileName")
        name_font = QFont()
        name_font.setPointSize(24)
        name_font.setBold(True)
        self.name_label.setFont(name_font)
        
        self.username_label = QLabel(f"@{self.profile_data['username']}")
        self.username_label.setObjectName("profileUsername")
        
        self.bio_label = QLabel(self.profile_data["bio"])
        self.bio_label.setObjectName("profileBio")
        self.bio_label.setWordWrap(True)
        
        name_layout.addWidget(self.name_label)
        name_layout.addWidget(self.username_label)
        name_layout.addWidget(self.bio_label)
        name_layout.addStretch()
        
        top_layout.addWidget(name_section, 1)
        
        # Edit button
        self.edit_button = QPushButton("Edit Profile")
        self.edit_button.setObjectName("editProfileButton")
        self.edit_button.clicked.connect(self.edit_profile)
        top_layout.addWidget(self.edit_button, 0, Qt.AlignTop)
        
        # Add top section to main layout
        main_layout.addWidget(top_section)
        
        # Side-by-side layout for personal info and zodiac
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(16)
        
        # Personal Info Card
        personal_card = QFrame()
        personal_card.setObjectName("infoCard")
        personal_layout = QVBoxLayout(personal_card)
        personal_layout.setContentsMargins(16, 16, 16, 16)
        personal_layout.setSpacing(12)
        
        personal_title = QLabel("Personal Info")
        personal_title.setObjectName("cardTitle")
        personal_title.setStyleSheet("background-color: transparent;")
        personal_layout.addWidget(personal_title)
        
        form_layout = QFormLayout()
        form_layout.setContentsMargins(8, 8, 8, 8)
        form_layout.setSpacing(10)
        
        self.birthday_label = QLabel()
        self.birthday_label.setObjectName("infoValue")
        self.birthday_label.setStyleSheet("background-color: transparent;")
        
        self.age_label = QLabel()
        self.age_label.setObjectName("infoValue")
        self.age_label.setStyleSheet("background-color: transparent;")
        
        self.joined_label = QLabel()
        self.joined_label.setObjectName("infoValue")
        self.joined_label.setStyleSheet("background-color: transparent;")
        
        self.location_label = QLabel(self.profile_data.get("location", "Not specified"))
        self.location_label.setObjectName("infoValue")
        self.location_label.setStyleSheet("background-color: transparent;")
        
        birthday_title = QLabel("Birthday:")
        birthday_title.setStyleSheet("background-color: transparent;")
        age_title = QLabel("Age:")
        age_title.setStyleSheet("background-color: transparent;")
        joined_title = QLabel("Joined:")
        joined_title.setStyleSheet("background-color: transparent;")
        location_title = QLabel("Location:")
        location_title.setStyleSheet("background-color: transparent;")
        
        form_layout.addRow(birthday_title, self.birthday_label)
        form_layout.addRow(age_title, self.age_label)
        form_layout.addRow(joined_title, self.joined_label)
        form_layout.addRow(location_title, self.location_label)
        
        personal_layout.addLayout(form_layout)
        personal_layout.addStretch()
        
        # Zodiac Card
        zodiac_card = QFrame()
        zodiac_card.setObjectName("infoCard")
        zodiac_layout = QVBoxLayout(zodiac_card)
        zodiac_layout.setContentsMargins(16, 16, 16, 16)
        zodiac_layout.setSpacing(12)
        
        zodiac_title = QLabel("Zodiac & Elements")
        zodiac_title.setObjectName("cardTitle")
        zodiac_title.setStyleSheet("background-color: transparent;")
        zodiac_layout.addWidget(zodiac_title)
        
        # Zodiac content
        zodiac_content = QWidget()
        zodiac_content.setStyleSheet("background-color: transparent;")
        zodiac_content_layout = QVBoxLayout(zodiac_content)
        zodiac_content_layout.setContentsMargins(8, 8, 8, 8)
        zodiac_content_layout.setSpacing(16)
        
        # Sign and element in horizontal layout
        zodiac_info = QHBoxLayout()
        zodiac_info.setSpacing(16)
        
        # Sign widget
        sign_widget = QFrame()
        sign_widget.setObjectName("signWidget")
        sign_layout = QVBoxLayout(sign_widget)
        sign_layout.setContentsMargins(12, 12, 12, 12)
        sign_layout.setAlignment(Qt.AlignCenter)
        
        self.sign_symbol = QLabel()
        self.sign_symbol.setObjectName("zodiacSymbol")
        self.sign_symbol.setAlignment(Qt.AlignCenter)
        self.sign_symbol.setStyleSheet("background-color: transparent;")
        
        self.sign_name = QLabel()
        self.sign_name.setObjectName("zodiacName")
        self.sign_name.setAlignment(Qt.AlignCenter)
        self.sign_name.setStyleSheet("background-color: transparent;")
        
        sign_layout.addWidget(self.sign_symbol)
        sign_layout.addWidget(self.sign_name)
        
        # Element widget
        element_widget = QFrame()
        element_widget.setObjectName("elementWidget")
        element_layout = QVBoxLayout(element_widget)
        element_layout.setContentsMargins(12, 12, 12, 12)
        element_layout.setAlignment(Qt.AlignCenter)
        
        self.element_symbol = QLabel()
        self.element_symbol.setObjectName("elementSymbol")
        self.element_symbol.setAlignment(Qt.AlignCenter)
        self.element_symbol.setStyleSheet("background-color: transparent;")
        
        self.element_name = QLabel()
        self.element_name.setObjectName("elementName")
        self.element_name.setAlignment(Qt.AlignCenter)
        self.element_name.setStyleSheet("background-color: transparent;")
        
        element_layout.addWidget(self.element_symbol)
        element_layout.addWidget(self.element_name)
        
        zodiac_info.addWidget(sign_widget)
        zodiac_info.addWidget(element_widget)
        
        zodiac_content_layout.addLayout(zodiac_info)
        
        # Traits section
        traits_widget = QFrame()
        traits_widget.setObjectName("traitsWidget")
        traits_layout = QVBoxLayout(traits_widget)
        traits_layout.setContentsMargins(16, 16, 16, 16)
        
        traits_title = QLabel("Common Traits")
        traits_title.setObjectName("traitsTitle")
        traits_title.setStyleSheet("background-color: transparent;")
        
        self.traits_label = QLabel()
        self.traits_label.setObjectName("traitsLabel")
        self.traits_label.setWordWrap(True)
        self.traits_label.setStyleSheet("background-color: transparent;")
        
        traits_layout.addWidget(traits_title)
        traits_layout.addWidget(self.traits_label)
        
        zodiac_content_layout.addWidget(traits_widget)
        zodiac_layout.addWidget(zodiac_content)
        
        # Add cards to the info layout
        info_layout.addWidget(personal_card)
        info_layout.addWidget(zodiac_card)
        
        main_layout.addLayout(info_layout)
        main_layout.addStretch()
        self.apply_styles()
    
    def update_profile_display(self):
        """Update all displayed profile information"""
        # Basic info
        self.name_label.setText(self.profile_data["name"])
        self.username_label.setText(f"@{self.profile_data['username']}")
        self.bio_label.setText(self.profile_data["bio"])
        
        # Profile picture
        if self.profile_data.get("profile_pic"):
            self.profile_pic.set_image(self.profile_data["profile_pic"])
        else:
            # Use name initials for emoji selection
            name = self.profile_data["name"]
            if name:
                initial = name[0].upper()
                # Map initial to an emoji face
                emoji_map = {
                    'A': '😀', 'B': '😊', 'C': '🙂', 'D': '😎', 'E': '🤓',
                    'F': '😄', 'G': '😃', 'H': '😁', 'I': '😉', 'J': '😍',
                    'K': '🥰', 'L': '😇', 'M': '🤩', 'N': '🥳', 'O': '😌',
                    'P': '😏', 'Q': '😺', 'R': '🤠', 'S': '🧐', 'T': '🤔',
                    'U': '😜', 'V': '😝', 'W': '😛', 'X': '🤪', 'Y': '😋',
                    'Z': '😚'
                }
                emoji = emoji_map.get(initial, '😀')
                self.profile_pic.set_emoji(emoji)
        
        # Personal info
        birth_date = self.profile_data["birth_date"].toPyDate()
        self.birthday_label.setText(birth_date.strftime("%B %d, %Y"))
        
        # Calculate age
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        self.age_label.setText(f"{age} years")
        
        # Join date
        join_date = self.profile_data["join_date"]
        days_since = (datetime.now() - join_date).days
        if days_since < 30:
            joined_text = f"{days_since} days ago"
        elif days_since < 365:
            months = days_since // 30
            joined_text = f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = days_since // 365
            joined_text = f"{years} year{'s' if years > 1 else ''} ago"
        self.joined_label.setText(f"{join_date.strftime('%B %d, %Y')} ({joined_text})")
        
        # Location
        self.location_label.setText(self.profile_data.get("location") or "Not specified")
        
        # Update zodiac info
        self.update_zodiac_info()
    
    def update_zodiac_info(self):
        """Update the zodiac sign and element information"""
        birth_date = self.profile_data["birth_date"].toPyDate()
        sign_name, sign_symbol = ZodiacSign.get_zodiac_sign(birth_date)
        element_name, element_symbol = ZodiacSign.get_element(sign_name)
        
        self.sign_symbol.setText(sign_symbol)
        self.sign_name.setText(sign_name)
        self.element_symbol.setText(element_symbol)
        self.element_name.setText(element_name)
        
        # Sample traits based on zodiac sign
        traits_map = {
            "Aries": "Energetic, confident, impulsive, and passionate",
            "Taurus": "Reliable, patient, practical, and determined",
            "Gemini": "Adaptable, outgoing, curious, and versatile",
            "Cancer": "Emotional, intuitive, protective, and sympathetic",
            "Leo": "Creative, passionate, generous, and warm-hearted",
            "Virgo": "Analytical, practical, diligent, and perfectionistic",
            "Libra": "Diplomatic, fair-minded, social, and cooperative",
            "Scorpio": "Resourceful, brave, passionate, and persistent",
            "Sagittarius": "Optimistic, freedom-loving, honest, and adventurous",
            "Capricorn": "Responsible, disciplined, ambitious, and persistent",
            "Aquarius": "Progressive, original, independent, and humanitarian",
            "Pisces": "Compassionate, artistic, intuitive, and gentle"
        }
        
        self.traits_label.setText(traits_map.get(sign_name, ""))
    
    def set_profile_data(self, data):
        """Update the profile data dictionary"""
        self.profile_data.update(data)
        self.update_profile_display()
    
    def edit_profile(self):
        """Open dialog to edit profile information"""
        dialog = EditProfileDialog(self, self.profile_data, theme=self.theme)
        if dialog.exec_() == QDialog.Accepted:
            # Update profile with new data
            self.set_profile_data(dialog.get_profile_data())
    
    def apply_styles(self):
        is_dark = self.theme.get("is_dark", True)
        text = self.theme.get("text", "#FFFFFF" if is_dark else "#000000")
        text_secondary = self.theme.get("text_secondary", "#BBBBBB" if is_dark else "#6E6E6E")
        primary = self.theme.get("primary", "#0A84FF")
        secondary = self.theme.get("secondary", "#52A8FF")
        surface = self.theme.get("surface", "#262626" if is_dark else "#FFFFFF")
        border = self.theme.get("border", "#383838" if is_dark else "#D1D1D6")
        
        self.setStyleSheet(f"""
            QLabel#profileName {{
                color: {text};
                font-size: 24px;
                font-weight: bold;
                background-color: transparent;
            }}
            QLabel#profileUsername {{
                color: {text_secondary};
                font-size: 16px;
                background-color: transparent;
            }}
            QLabel#profileBio {{
                color: {text};
                font-size: 14px;
                margin-top: 8px;
                background-color: transparent;
            }}
            QPushButton#editProfileButton {{
                background-color: {primary};
                color: white;
                border: none;
                border-radius: 18px;
                padding: 8px 16px;
                font-size: 14px;
            }}
            QPushButton#editProfileButton:hover {{
                background-color: {primary}cc;
            }}
            QFrame#infoCard {{
                background-color: {surface};
                border-radius: 16px;
                border: 1px solid {border};
            }}
            QLabel#cardTitle {{
                color: {text};
                font-size: 18px;
                font-weight: bold;
                background-color: transparent;
            }}
            QLabel#infoValue {{
                color: {text};
                font-size: 14px;
                background-color: transparent;
            }}
            QFrame#signWidget, QFrame#elementWidget {{
                background-color: {primary}20;
                border-radius: 8px;
            }}
            QLabel#zodiacSymbol, QLabel#elementSymbol {{
                color: {primary};
                font-size: 36px;
                background-color: transparent;
            }}
            QLabel#zodiacName, QLabel#elementName {{
                color: {text};
                font-size: 16px;
                font-weight: bold;
                background-color: transparent;
            }}
            QFrame#traitsWidget {{
                background-color: {surface};
                border-radius: 12px;
            }}
            QLabel#traitsTitle {{
                color: {text};
                font-size: 16px;
                font-weight: bold;
                background-color: transparent;
            }}
            QLabel#traitsLabel {{
                color: {text_secondary};
                font-size: 14px;
                line-height: 150%;
                background-color: transparent;
            }}
        """)

