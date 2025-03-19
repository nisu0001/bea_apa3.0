import os, random
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, 
    QHBoxLayout, QGraphicsDropShadowEffect, QSpacerItem, 
    QSizePolicy, QWidget, QStackedLayout, QGridLayout
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont, QColor, QMovie
from utils import resource_path

class ReminderDialog(QDialog):
    def __init__(self, parent=None, width=380, height=180, theme=None):
        """
        :param parent: Parent widget.
        :param width: The desired width of the dialog.
        :param height: The desired height of the dialog.
        :param theme: A dictionary of theme colors. If None, a default dark theme is used.
        """
        super().__init__(parent)
        self.setWindowTitle("Hydration Reminder")
        # Make the dialog frameless and always on top
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # Enable for shadow effect
        self.resize(width, height)
        
        # Use the provided theme or default to iOS-inspired ocean theme
        self.theme = theme if theme is not None else {
            "is_dark": True,
            "background": "#0A2740",
            "surface": "#123859",
            "surface_raised": "#1A4B80",
            "text": "#FFFFFF",
            "text_secondary": "#B0C4DE",
            "border": "#1A4B80",
            "primary": "#0A84FF",
            "secondary": "#52A8FF",
            "accent": "#5AC8FA",
            "accent_dark": "#4AA8D4",
            "highlight": "#407AA7",
            "overlay": "#1F4C7A",
            "shadow": "#051526",
            "warning": "#FF9F0A",
            "info": "#64D2FF",
            "success": "#30D158",
        }
        
        self.init_ui()
        
    def init_ui(self):
        # Main layout for the dialog
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Use a QWidget as a container (instead of QLabel) for content and shadow
        container = QWidget(self)
        container.setObjectName("container")
        
        # Apply shadow effect to container
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setColor(QColor(self.theme.get("shadow", "#000000")))
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)
        
        # Style the container – note the appended "30" sets an alpha if your theme border is in hex
        container.setStyleSheet(f"""
            #container {{
                background-color: {self.theme.get('surface', '#123859')};
                border-radius: 16px;
                border: 1px solid {self.theme.get('border', '#1A4B80')}30;
            }}
        """)
        
        # Layout for container content
        content_layout = QVBoxLayout(container)
        content_layout.setContentsMargins(20, 24, 20, 20)
        content_layout.setSpacing(16)
        
        # Header layout with icon and title
        header_layout = QHBoxLayout()
        water_icon_path = resource_path(os.path.join("assets", "icons", "water_drop.svg"))
        if os.path.exists(water_icon_path):
            water_icon_label = QLabel()
            water_icon_label.setPixmap(QIcon(water_icon_path).pixmap(QSize(24, 24)))
            header_layout.addWidget(water_icon_label)
        
        title_label = QLabel("Hydration Reminder")
        title_label.setStyleSheet(f"""
            color: {self.theme.get('text', '#FFFFFF')};
            font-size: 16px;
            font-weight: 600;
        """)
        title_font = QFont()
        title_font.setWeight(QFont.DemiBold)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        
        # Message label
        message_label = QLabel("Baby!! I Love you 💖💖\nIt's time to drink some water")
        message_label.setStyleSheet(f"""
            color: {self.theme.get('text_secondary', '#B0C4DE')};
            font-size: 15px;
            padding: 8px 0px;
        """)
        message_label.setAlignment(Qt.AlignCenter)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        self.snooze_button = QPushButton("Snooze")
        self.drink_button = QPushButton("Log Drink")
        icon_size = QSize(16, 16)
        icon_plus = QIcon(resource_path(os.path.join("assets", "icons", "plus.svg")))
        icon_snooze = QIcon(resource_path(os.path.join("assets", "icons", "snooze.svg")))
        if not icon_plus.isNull():
            self.drink_button.setIcon(icon_plus)
            self.drink_button.setIconSize(icon_size)
        if not icon_snooze.isNull():
            self.snooze_button.setIcon(icon_snooze)
            self.snooze_button.setIconSize(icon_size)
        
        # Set styles for buttons (iOS style)
        self.snooze_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme.get('surface_raised', '#1A4B80')};
                color: {self.theme.get('text', '#FFFFFF')};
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 500;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {self.theme.get('overlay', '#1F4C7A')};
            }}
            QPushButton:pressed {{
                background-color: {self.theme.get('highlight', '#407AA7')};
            }}
        """)
        self.drink_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme.get('primary', '#0A84FF')};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 600;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {self.theme.get('secondary', '#52A8FF')};
            }}
            QPushButton:pressed {{
                background-color: {self.theme.get('accent', '#5AC8FA')};
            }}
        """)
        self.snooze_button.setFixedHeight(44)
        self.drink_button.setFixedHeight(44)
        button_layout.addWidget(self.snooze_button)
        button_layout.addWidget(self.drink_button)
        
        # Assemble container content
        content_layout.addLayout(header_layout)
        content_layout.addWidget(message_label, 0, Qt.AlignCenter)
        content_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        content_layout.addLayout(button_layout)
        
        # Add container to main layout
        main_layout.addWidget(container)
        self.setLayout(main_layout)
        
    def mousePressEvent(self, event):
        """Allow the dialog to be moved by dragging it"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """Move the dialog when dragged"""
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()


class LegacyReminderDialog(QDialog):
    def __init__(self, parent=None, width=400, height=150, theme=None):
        super().__init__(parent)
        self.setWindowTitle("Hydration Reminder")
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.resize(width, height)
        self.theme = theme if theme is not None else {
            "border": "#555",
            "primary": "#1e90ff",
            "secondary": "#2CB67D",
            "background": "#16161A",
            "text": "#FFFFFE",
            "accent": "#EF4565",
            "highlight": "#72757E",
            "secondary_dark": "#196747",
            "accent_dark": "#e32a4d"
        }
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.theme['background']};
                border: none;
                border-radius: 15px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        message_label = QLabel("Baby!! I Love you💖💖\nIt's time to drink some water")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setStyleSheet(f"color: {self.theme['text']}; font-size: 16px; font-weight: bold;")
        layout.addWidget(message_label)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        self.drink_button = QPushButton("Log Drink")
        self.snooze_button = QPushButton("Snooze")
        icon_plus = QIcon(resource_path(os.path.join("assets", "icons", "plus.svg")))
        icon_snooze = QIcon(resource_path(os.path.join("assets", "icons", "snooze.svg")))
        self.drink_button.setIcon(icon_plus)
        self.snooze_button.setIcon(icon_snooze)
        drink_button_style = f"""
            QPushButton {{
                background-color: {self.theme['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['secondary']};
            }}
        """
        self.drink_button.setStyleSheet(drink_button_style)
        snooze_button_style = f"""
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent_dark']};
            }}
        """
        self.snooze_button.setStyleSheet(snooze_button_style)
        button_layout.addWidget(self.drink_button)
        button_layout.addWidget(self.snooze_button)
        layout.addLayout(button_layout)
        self.setLayout(layout)


class OverTheTopReminderDialog(QDialog):
    def __init__(self, parent=None, width=460, height=240, theme=None):
        super().__init__(parent)
        self.setWindowTitle("Hydration Reminder")
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.resize(width, height)
        # Use defaults if theme is not provided or missing over-the-top keys
        if theme is None or 'gradient_start' not in theme:
            self.theme = {
                "gradient_start": "#FF69B4",  # Hot pink (unused now)
                "gradient_end": "#FFD700",    # Gold (unused now)
                "text": "#FFFFFF",
                "button_primary": "#8A2BE2",  # Blueviolet
                "button_secondary": "#FF4500",  # Orange red
                "button_primary_hover": "#7A1BC2",
                "button_secondary_hover": "#E03F00"
            }
        else:
            self.theme = theme
        self.init_ui()

    def init_ui(self):
        # Create a stacked layout that layers widgets
        stacked_layout = QStackedLayout(self)
        stacked_layout.setStackingMode(QStackedLayout.StackAll)
        self.setLayout(stacked_layout)

        # Background label to display a random GIF
        self.background_label = QLabel(self)
        self.background_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.background_label.setScaledContents(True)
        gif_number = random.randint(1, 1)
        gif_path = resource_path(os.path.join("assets", "gifs", f"gif{gif_number}.gif"))
        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            self.background_label.setMovie(self.movie)
            self.movie.start()
        else:
            print(f"GIF not found: {gif_path}")
            self.background_label.setStyleSheet("background-color: #FF69B4;")
        stacked_layout.addWidget(self.background_label)

        # Content widget that holds the message and buttons
        content_widget = QWidget(self)
        content_widget.setAttribute(Qt.WA_TranslucentBackground, True)
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(25, 25, 25, 25)
        content_layout.setSpacing(20)

        # Message label at the top
        message_label = QLabel("Time to drink water, superstar!\nKeep shining and stay hydrated!")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setStyleSheet(f"color: {self.theme.get('text', '#FFFFFF')}; font-size: 18px; font-weight: bold;")
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        message_label.setFont(font)
        content_layout.addWidget(message_label)

        # Expanding spacer to push buttons to the bottom
        content_layout.addStretch(1)

        # Buttons layout placed at the bottom
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        self.drink_button = QPushButton("Log Drink")
        self.snooze_button = QPushButton("Snooze")
        icon_size = QSize(16, 16)
        icon_plus = QIcon(resource_path(os.path.join("assets", "icons", "plus.svg")))
        icon_snooze = QIcon(resource_path(os.path.join("assets", "icons", "snooze.svg")))
        if not icon_plus.isNull():
            self.drink_button.setIcon(icon_plus)
            self.drink_button.setIconSize(icon_size)
        if not icon_snooze.isNull():
            self.snooze_button.setIcon(icon_snooze)
            self.snooze_button.setIconSize(icon_size)
        # Button styles with safe defaults using .get()
        drink_button_style = f"""
            QPushButton {{
                background-color: {self.theme.get('button_primary', '#8A2BE2')};
                color: white;
                border: none;
                border-radius: 12px;
                padding: 14px 24px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.theme.get('button_primary_hover', '#7A1BC2')};
            }}
        """
        snooze_button_style = f"""
            QPushButton {{
                background-color: {self.theme.get('button_secondary', '#FF4500')};
                color: white;
                border: none;
                border-radius: 12px;
                padding: 14px 24px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.theme.get('button_secondary_hover', '#E03F00')};
            }}
        """
        self.drink_button.setStyleSheet(drink_button_style)
        self.snooze_button.setStyleSheet(snooze_button_style)
        # Center buttons horizontally
        button_layout.addStretch(1)
        button_layout.addWidget(self.drink_button)
        button_layout.addWidget(self.snooze_button)
        button_layout.addStretch(1)
        content_layout.addLayout(button_layout)

        # Add the content widget to the stacked layout
        stacked_layout.addWidget(content_widget)
        # Ensure content_widget is raised above the background
        content_widget.raise_()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

class TodoReminderDialog(QDialog):
    def __init__(self, todo_item, parent=None, width=420, height=220, theme=None):
        """
        Dialog for showing a task reminder.
        
        :param todo_item: The TodoItem object to display in the reminder
        :param parent: Parent widget
        :param width: The desired width of the dialog
        :param height: The desired height of the dialog
        :param theme: A dictionary of theme colors. If None, a default dark theme is used.
        """
        super().__init__(parent)
        self.setWindowTitle("Task Reminder")
        self.todo = todo_item
        
        # Make the dialog frameless and always on top
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # Enable for shadow effect
        self.resize(width, height)
        
        # Use the provided theme or default to iOS-inspired ocean theme
        self.theme = theme if theme is not None else {
            "is_dark": True,
            "background": "#0A2740",
            "surface": "#123859",
            "surface_raised": "#1A4B80",
            "text": "#FFFFFF",
            "text_secondary": "#B0C4DE",
            "border": "#1A4B80",
            "primary": "#0A84FF",
            "secondary": "#52A8FF",
            "accent": "#5AC8FA",
            "accent_dark": "#4AA8D4",
            "highlight": "#407AA7",
            "overlay": "#1F4C7A",
            "shadow": "#051526",
            "warning": "#FF9F0A",
            "info": "#64D2FF",
            "success": "#30D158",
        }
        
        self.init_ui()
        
    def init_ui(self):
        # Main layout for the dialog
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Use a QWidget as a container for content and shadow
        container = QWidget(self)
        container.setObjectName("container")
        
        # Apply shadow effect to container
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setColor(QColor(self.theme.get("shadow", "#000000")))
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)
        
        # Style the container
        container.setStyleSheet(f"""
            #container {{
                background-color: {self.theme.get('surface', '#123859')};
                border-radius: 16px;
                border: 1px solid {self.theme.get('border', '#1A4B80')}30;
            }}
        """)
        
        # Layout for container content
        content_layout = QVBoxLayout(container)
        content_layout.setContentsMargins(20, 24, 20, 20)
        content_layout.setSpacing(16)
        
        # Header layout with icon and title
        header_layout = QHBoxLayout()
        
        # Use task icon or default reminder icon
        task_icon_path = resource_path(os.path.join("assets", "icons", "task.svg"))
        fallback_icon_path = resource_path(os.path.join("assets", "icons", "bell.svg"))
        
        icon_path = task_icon_path if os.path.exists(task_icon_path) else fallback_icon_path
        
        if os.path.exists(icon_path):
            icon_label = QLabel()
            icon_label.setPixmap(QIcon(icon_path).pixmap(QSize(24, 24)))
            header_layout.addWidget(icon_label)
        
        title_label = QLabel("Task Reminder")
        title_label.setStyleSheet(f"""
            color: {self.theme.get('text', '#FFFFFF')};
            font-size: 16px;
            font-weight: 600;
        """)
        title_font = QFont()
        title_font.setWeight(QFont.DemiBold)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        
        # Task name with priority indicator
        task_label = QLabel(self.todo.text)
        task_label.setWordWrap(True)
        task_label.setStyleSheet(f"""
            color: {self.theme.get('text', '#FFFFFF')};
            font-size: 18px;
            font-weight: 600;
            padding: 8px 0px;
        """)
        task_label.setAlignment(Qt.AlignCenter)
        
        # Task details (category, deadline, etc.)
        details_text = ""
        if hasattr(self.todo, 'category') and self.todo.category:
            details_text += f"Category: {self.todo.category}"
        
        if hasattr(self.todo, 'deadline') and self.todo.deadline:
            try:
                from datetime import datetime
                deadline_dt = datetime.fromisoformat(self.todo.deadline)
                date_str = deadline_dt.strftime("%b %d, %I:%M %p")
                if details_text:
                    details_text += " • "
                details_text += f"Due: {date_str}"
            except (ValueError, TypeError):
                pass
                
        if details_text:
            details_label = QLabel(details_text)
            details_label.setStyleSheet(f"""
                color: {self.theme.get('text_secondary', '#B0C4DE')};
                font-size: 14px;
            """)
            details_label.setAlignment(Qt.AlignCenter)
        else:
            details_label = None
        
        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.snooze_button = QPushButton("Snooze")
        self.complete_button = QPushButton("Complete Task")
        
        icon_size = QSize(16, 16)
        icon_plus = QIcon(resource_path(os.path.join("assets", "icons", "plus.svg")))
        icon_snooze = QIcon(resource_path(os.path.join("assets", "icons", "snooze.svg")))
        icon_check = QIcon(resource_path(os.path.join("assets", "icons", "check.svg")))
        
        if not icon_check.isNull():
            self.complete_button.setIcon(icon_check)
            self.complete_button.setIconSize(icon_size)
        elif not icon_plus.isNull():
            self.complete_button.setIcon(icon_plus)
            self.complete_button.setIconSize(icon_size)
            
        if not icon_snooze.isNull():
            self.snooze_button.setIcon(icon_snooze)
            self.snooze_button.setIconSize(icon_size)
        
        # Set styles for buttons
        self.snooze_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme.get('surface_raised', '#1A4B80')};
                color: {self.theme.get('text', '#FFFFFF')};
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 500;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {self.theme.get('overlay', '#1F4C7A')};
            }}
            QPushButton:pressed {{
                background-color: {self.theme.get('highlight', '#407AA7')};
            }}
        """)
        
        priority_color = self.theme.get('primary', '#0A84FF')
        if hasattr(self.todo, 'priority'):
            if self.todo.priority == "High":
                priority_color = self.theme.get('accent', '#FF453A')
            elif self.todo.priority == "Low":
                priority_color = self.theme.get('success', '#30D158')
        
        self.complete_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {priority_color};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 600;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {self.theme.get('secondary', '#52A8FF')};
            }}
            QPushButton:pressed {{
                background-color: {self.theme.get('accent', '#5AC8FA')};
            }}
        """)
        
        self.snooze_button.setFixedHeight(44)
        self.complete_button.setFixedHeight(44)
        
        button_layout.addWidget(self.snooze_button)
        button_layout.addWidget(self.complete_button)
        
        # Assemble container content
        content_layout.addLayout(header_layout)
        content_layout.addWidget(task_label, 0, Qt.AlignCenter)
        if details_label:
            content_layout.addWidget(details_label, 0, Qt.AlignCenter)
        content_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        content_layout.addLayout(button_layout)
        
        # Add container to main layout
        main_layout.addWidget(container)
        self.setLayout(main_layout)
        
    def mousePressEvent(self, event):
        """Allow the dialog to be moved by dragging it"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """Move the dialog when dragged"""
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()