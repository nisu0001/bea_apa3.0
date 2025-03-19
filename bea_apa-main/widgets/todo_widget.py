import os
import json
import random
from datetime import datetime, timedelta, time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QLineEdit, QDialog, QListWidget, QListWidgetItem, QSpinBox,
    QGraphicsDropShadowEffect, QComboBox, QDateEdit, QTimeEdit,
    QMessageBox, QSizePolicy, QFrame, QScrollArea, QMenu,
    QAction, QApplication, QCheckBox, QToolTip, QCompleter
)
from PyQt5.QtGui import (
    QIcon, QColor, QPainter, QPen, QBrush, QPainterPath, 
    QLinearGradient, QFont, QCursor, QFontMetrics
)
from PyQt5.QtCore import (
    Qt, QSize, pyqtSignal, QDate, QTimer, QPropertyAnimation,
    QEasingCurve, QRectF, QPoint, QStringListModel, QTime
)
from config import MODERN_COLORS
from utils import resource_path

# ======================================================
# Todo Item Classes
# ======================================================

class TodoItem:
    """Model class for a todo item"""
    def __init__(self, text="", deadline=None, priority="Medium", 
                 tags=None, completed=False, created_at=None,
                 completed_at=None, id=None, category=None,
                 description="", reminder_time=None, repeat_option=None):
        
        # Core properties
        self.id = id or random.randint(10000, 99999)
        self.text = text
        self.completed = completed
        self.priority = priority  # "High", "Medium", "Low"
        self.tags = tags or []
        self.category = category or "Personal"  # Default category
        self.description = description
        
        # Timestamps
        self.created_at = created_at or datetime.now().isoformat()
        self.completed_at = completed_at
        self.deadline = deadline  # Should be a datetime isoformat string or None
        
        # Additional features
        self.reminder_time = reminder_time  # isoformat time string or None
        self.repeat_option = repeat_option  # "Daily", "Weekly", "Monthly", "None"
    
    def to_dict(self):
        """Convert TodoItem to dictionary for storage"""
        return {
            "id": self.id,
            "text": self.text,
            "completed": self.completed,
            "priority": self.priority,
            "tags": self.tags,
            "category": self.category,
            "description": self.description,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "deadline": self.deadline,
            "reminder_time": self.reminder_time,
            "repeat_option": self.repeat_option
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create TodoItem from dictionary"""
        return cls(
            id=data.get("id"),
            text=data.get("text", ""),
            completed=data.get("completed", False),
            priority=data.get("priority", "Medium"),
            tags=data.get("tags", []),
            category=data.get("category", "Personal"),
            description=data.get("description", ""),
            created_at=data.get("created_at"),
            completed_at=data.get("completed_at"),
            deadline=data.get("deadline"),
            reminder_time=data.get("reminder_time"),
            repeat_option=data.get("repeat_option")
        )
    
    def toggle_completed(self):
        """Toggle completion status and update timestamp"""
        self.completed = not self.completed
        if self.completed:
            self.completed_at = datetime.now().isoformat()
        else:
            self.completed_at = None
        return self.completed
    
    def is_overdue(self):
        """Check if the task is overdue but not completed"""
        if not self.deadline or self.completed:
            return False
        
        try:
            deadline_dt = datetime.fromisoformat(self.deadline)
            return deadline_dt < datetime.now()
        except (ValueError, TypeError):
            return False
    
    def days_until_deadline(self):
        """Get days until deadline (negative if overdue)"""
        if not self.deadline:
            return None
        
        try:
            deadline_dt = datetime.fromisoformat(self.deadline)
            days = (deadline_dt.date() - datetime.now().date()).days
            return days
        except (ValueError, TypeError):
            return None
    
    def should_remind(self):
        """Check if a reminder should be sent based on reminder_time"""
        if not self.reminder_time or self.completed:
            return False
        
        try:
            # Only check date part if deadline exists
            if self.deadline:
                deadline_dt = datetime.fromisoformat(self.deadline)
                today = datetime.now().date()
                # Only remind on the deadline day
                if deadline_dt.date() != today:
                    return False
            
            # Check if current time is past the reminder time
            reminder_time = datetime.strptime(self.reminder_time, "%H:%M").time()
            now = datetime.now().time()
            
            # Allow a 5-minute window for the reminder
            five_min_ago = (datetime.now() - timedelta(minutes=5)).time()
            
            return five_min_ago <= reminder_time <= now
        except (ValueError, TypeError):
            return False


class PriorityCheckButton(QPushButton):
    """Custom check button with priority colors"""
    def __init__(self, priority="Medium", theme="dark v2", parent=None):
        super().__init__(parent)
        self.theme = theme.lower()
        self.colors = MODERN_COLORS.get(self.theme, MODERN_COLORS["dark v2"])
        self.priority = priority
        self.setFixedSize(28, 28)
        self.setCheckable(True)
        self.setStyleSheet("border: none; background: transparent;")
        self.setCursor(Qt.PointingHandCursor)
    
    def setPriority(self, priority):
        self.priority = priority
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(4, 4, -4, -4)
        radius = rect.width() / 2
        center = rect.center()
        
        # Priority colors
        priority_colors = {
            "High": QColor("#FF453A"),    # Red
            "Medium": QColor("#FF9F0A"),  # Orange
            "Low": QColor("#30D158")      # Green
        }
        
        color = priority_colors.get(self.priority, QColor("#0A84FF"))  # Default to blue
        
        # Hover effect
        if self.underMouse() and not self.isChecked():
            painter.setBrush(QColor(180, 180, 180, 30))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius, radius)
        
        if self.isChecked():
            # Draw filled circle
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius, radius)
            
            # Draw checkmark
            painter.setPen(QPen(Qt.white, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            checkmark = QPainterPath()
            # Scale checkmark based on button size
            scale = rect.width() / 24.0
            checkmark.moveTo(center.x() - 5 * scale, center.y())
            checkmark.lineTo(center.x() - 1 * scale, center.y() + 4 * scale)
            checkmark.lineTo(center.x() + 6 * scale, center.y() - 4 * scale)
            painter.drawPath(checkmark)
        else:
            # Draw empty circle
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(color, 2))
            painter.drawEllipse(center, radius, radius)


class TodoItemWidget(QWidget):
    """Widget to display a single todo item in the list"""
    # Signals
    completed = pyqtSignal(int, bool)  # id, is_completed
    deleted = pyqtSignal(int)  # id
    edited = pyqtSignal(int, object)  # id, updated_todo
    details_requested = pyqtSignal(int)  # id
    
    def __init__(self, todo_item, theme="dark v2", parent=None):
        super().__init__(parent)
        self.todo = todo_item
        self.theme = theme
        self.colors = MODERN_COLORS.get(theme.lower(), MODERN_COLORS["dark v2"])
        self.expanded = False
        self.editing = False
        
        self.init_ui()
        self.update_appearance()
    
    def init_ui(self):
        """Initialize the widget UI"""
        self.setObjectName("todoItemWidget")
        
        # Main layout with card-like appearance
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 8)
        main_layout.setSpacing(0)
        
        # Card container
        self.card = QFrame()
        self.card.setObjectName("todoCard")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(8)
        
        # Top row: checkbox, text, actions
        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        
        # Checkbox with priority color
        self.check_button = PriorityCheckButton(self.todo.priority, self.theme)
        self.check_button.setChecked(self.todo.completed)
        self.check_button.clicked.connect(self.toggle_completed)
        top_row.addWidget(self.check_button)
        
        # Main task content area
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        # Task text (clickable for details)
        self.text_label = QLabel(self.todo.text)
        self.text_label.setObjectName("todoText")
        self.text_label.setCursor(Qt.PointingHandCursor)
        self.text_label.setWordWrap(True)
        self.text_label.mousePressEvent = lambda e: self.details_requested.emit(self.todo.id) if e.button() == Qt.LeftButton else None
        content_layout.addWidget(self.text_label)
        
        # Deadline and tags row (in smaller text)
        if self.todo.deadline or self.todo.tags:
            info_row = QHBoxLayout()
            info_row.setSpacing(8)
            
            # Show deadline if exists
            if self.todo.deadline:
                try:
                    from datetime import datetime
                    deadline_dt = datetime.fromisoformat(self.todo.deadline)
                    days_left = (deadline_dt.date() - datetime.now().date()).days
                    
                    deadline_text = deadline_dt.strftime("%b %d")
                    if days_left == 0:
                        deadline_text = f"Today, {deadline_dt.strftime('%H:%M')}"
                    elif days_left == 1:
                        deadline_text = f"Tomorrow, {deadline_dt.strftime('%H:%M')}"
                    elif days_left == -1:
                        deadline_text = "Yesterday"
                    elif days_left < -1:
                        deadline_text = f"{abs(days_left)} days overdue"
                    elif days_left > 0:
                        deadline_text = f"{deadline_text} ({days_left} days)"
                    
                    self.deadline_label = QLabel(deadline_text)
                    self.deadline_label.setObjectName(
                        "deadlineOverdue" if days_left < 0 and not self.todo.completed else "deadlineLabel"
                    )
                    info_row.addWidget(self.deadline_label)
                except (ValueError, TypeError):
                    pass
            
            # Show priority
            priority_label = QLabel(self.todo.priority)
            priority_label.setObjectName(f"priority{self.todo.priority}")
            info_row.addWidget(priority_label)
            
            # Add tags if they exist
            if self.todo.tags:
                tags_text = ", ".join(self.todo.tags[:2])  # Show first 2 tags
                if len(self.todo.tags) > 2:
                    tags_text += "..."
                tags_label = QLabel(tags_text)
                tags_label.setObjectName("tagsLabel")
                info_row.addWidget(tags_label)
            
            # Add info row to content
            info_row.addStretch(1)
            content_layout.addLayout(info_row)
        
        top_row.addLayout(content_layout, 1)
        
        # Action buttons container
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(4)
        
        # Edit button
        self.edit_btn = QPushButton()
        self.edit_btn.setObjectName("editButton")
        self.edit_btn.setIcon(QIcon(resource_path("assets/icons/edit.svg")))
        self.edit_btn.setFixedSize(24, 24)
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.clicked.connect(self.request_edit)
        actions_layout.addWidget(self.edit_btn)
        
        # Delete button
        self.delete_btn = QPushButton()
        self.delete_btn.setObjectName("deleteButton")
        self.delete_btn.setIcon(QIcon(resource_path("assets/icons/delete.svg")))
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.clicked.connect(lambda: self.deleted.emit(self.todo.id))
        actions_layout.addWidget(self.delete_btn)
        
        top_row.addLayout(actions_layout)
        
        # Add main content to card
        card_layout.addLayout(top_row)
        
        # Add card to main layout
        main_layout.addWidget(self.card)
        
        # Apply card shadow effect
        self.apply_shadow()
    
    def apply_shadow(self):
        """Apply shadow effect to the card"""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        self.card.setGraphicsEffect(shadow)
    
    def update_appearance(self):
        """Update widget appearance based on todo state"""
        is_completed = self.todo.completed
        is_overdue = self.todo.is_overdue()
        
        # Update check button
        self.check_button.setChecked(is_completed)
        self.check_button.setPriority(self.todo.priority)
        
        # Set card style dynamically based on state
        card_style = "todoCardCompleted" if is_completed else "todoCard"
        if is_overdue and not is_completed:
            card_style = "todoCardOverdue"
        self.card.setObjectName(card_style)
        
        # Update text appearance
        text_style = "todoTextCompleted" if is_completed else "todoText"
        self.text_label.setObjectName(text_style)
        
        # Update the stylesheet
        self.update_styles()
    
    def update_styles(self):
        """Apply current theme styles to the widget"""
        text_color = self.colors.get('text', '#FFFFFF')
        surface_color = self.colors.get('surface', '#2C2C2E')
        muted_color = self.colors.get('text_secondary', '#98989E')
        overdue_color = self.colors.get('accent', '#FF453A')
        priority_high = "#FF453A"  # Red
        priority_medium = "#FF9F0A"  # Orange
        priority_low = "#30D158"  # Green
        
        # Different background for completed and normal tasks
        completed_bg = QColor(surface_color).lighter(110).name() if '#' in surface_color else surface_color
        normal_bg = surface_color
        overdue_bg = QColor(surface_color).darker(110).name() if '#' in surface_color else surface_color
        
        self.setStyleSheet(f"""
            #todoCard {{
                background-color: {normal_bg};
                border-radius: 10px;
                border-left: 3px solid transparent;
            }}
            #todoCardCompleted {{
                background-color: {completed_bg};
                border-radius: 10px;
                border-left: 3px solid {priority_low};
            }}
            #todoCardOverdue {{
                background-color: {overdue_bg};
                border-radius: 10px;
                border-left: 3px solid {priority_high};
            }}
            #todoText {{
                color: {text_color};
                font-size: 15px;
            }}
            #todoTextCompleted {{
                color: {muted_color};
                font-size: 15px;
                text-decoration: line-through;
            }}
            #editButton, #deleteButton {{
                background: transparent;
                border: none;
                border-radius: 12px;
            }}
            #editButton:hover, #deleteButton:hover {{
                background-color: rgba(120, 120, 120, 0.2);
            }}
            #deadlineLabel {{
                color: {muted_color};
                font-size: 12px;
            }}
            #deadlineOverdue {{
                color: {overdue_color};
                font-size: 12px;
                font-weight: bold;
            }}
            #tagsLabel {{
                color: {muted_color};
                font-size: 12px;
            }}
            #priorityHigh {{
                color: {priority_high};
                font-size: 12px;
                font-weight: bold;
            }}
            #priorityMedium {{
                color: {priority_medium};
                font-size: 12px;
            }}
            #priorityLow {{
                color: {priority_low};
                font-size: 12px;
            }}
        """)
    
    def toggle_completed(self, checked):
        """Handle completion checkbox toggle"""
        is_completed = self.todo.toggle_completed()
        self.completed.emit(self.todo.id, is_completed)
        self.update_appearance()
    
    def request_edit(self):
        """Signal that this item wants to be edited"""
        self.details_requested.emit(self.todo.id)


# ======================================================
# Todo Detail Dialog
# ======================================================

class TodoDetailDialog(QDialog):
    """Dialog for viewing/editing task details"""
    todoUpdated = pyqtSignal(object)  # Updated TodoItem
    todoDeleted = pyqtSignal(int)     # TodoItem ID
    
    def __init__(self, todo_item, categories, theme="dark v2", parent=None):
        super().__init__(parent)
        self.todo = todo_item
        self.original_todo = todo_item
        self.theme = theme
        self.colors = MODERN_COLORS.get(theme.lower(), MODERN_COLORS["dark v2"])
        self.categories = categories
        self.all_tags = []
        
        # Collect all unique tags
        if parent and hasattr(parent, 'get_all_tags'):
            self.all_tags = parent.get_all_tags()
        
        self.setWindowTitle("Task Details")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(400)
        
        self.init_ui()
        self.apply_styles()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # Task title/name
        title_layout = QHBoxLayout()
        title_layout.setSpacing(16)
        
        # Completion checkbox
        self.complete_checkbox = QCheckBox()
        self.complete_checkbox.setChecked(self.todo.completed)
        title_layout.addWidget(self.complete_checkbox)
        
        # Title edit
        self.title_edit = QLineEdit(self.todo.text)
        self.title_edit.setPlaceholderText("Task title")
        self.title_edit.setObjectName("titleEdit")
        title_layout.addWidget(self.title_edit, 1)
        
        main_layout.addLayout(title_layout)
        
        # Details section
        details_container = QFrame()
        details_container.setObjectName("detailsContainer")
        details_layout = QVBoxLayout(details_container)
        details_layout.setSpacing(16)
        
        # Description
        description_layout = QVBoxLayout()
        description_layout.setSpacing(8)
        
        description_label = QLabel("Description")
        description_label.setObjectName("sectionLabel")
        description_layout.addWidget(description_label)
        
        self.description_edit = QLineEdit(self.todo.description)
        self.description_edit.setPlaceholderText("Add more details about this task")
        description_layout.addWidget(self.description_edit)
        
        details_layout.addLayout(description_layout)
        
        # Deadline
        deadline_layout = QHBoxLayout()
        deadline_layout.setSpacing(16)
        
        deadline_date_layout = QVBoxLayout()
        deadline_date_layout.setSpacing(8)
        
        deadline_date_label = QLabel("Due Date")
        deadline_date_label.setObjectName("sectionLabel")
        deadline_date_layout.addWidget(deadline_date_label)
        
        self.deadline_date = QDateEdit()
        self.deadline_date.setCalendarPopup(True)
        
        # Set current deadline if exists
        if self.todo.deadline:
            try:
                deadline_dt = datetime.fromisoformat(self.todo.deadline)
                self.deadline_date.setDate(QDate(deadline_dt.year, deadline_dt.month, deadline_dt.day))
            except (ValueError, TypeError):
                self.deadline_date.setDate(QDate.currentDate())
        else:
            self.deadline_date.setDate(QDate.currentDate())
        
        deadline_date_layout.addWidget(self.deadline_date)
        
        # Deadline time
        deadline_time_layout = QVBoxLayout()
        deadline_time_layout.setSpacing(8)
        
        deadline_time_label = QLabel("Due Time")
        deadline_time_label.setObjectName("sectionLabel")
        deadline_time_layout.addWidget(deadline_time_label)
        
        self.deadline_time = QTimeEdit()
        
        # Set current deadline time if exists
        if self.todo.deadline:
            try:
                deadline_dt = datetime.fromisoformat(self.todo.deadline)
                self.deadline_time.setTime(QTime(deadline_dt.hour, deadline_dt.minute))
            except (ValueError, TypeError):
                self.deadline_time.setTime(QTime(9, 0))  # Default 9am
        else:
            self.deadline_time.setTime(QTime(9, 0))  # Default 9am
        
        deadline_time_layout.addWidget(self.deadline_time)
        
        # Option to disable deadline
        has_deadline_layout = QVBoxLayout()
        has_deadline_layout.setSpacing(8)
        
        has_deadline_label = QLabel("Has Deadline")
        has_deadline_label.setObjectName("sectionLabel")
        has_deadline_layout.addWidget(has_deadline_label)
        
        self.has_deadline = QCheckBox("Enable")
        self.has_deadline.setChecked(self.todo.deadline is not None)
        self.has_deadline.stateChanged.connect(self.toggle_deadline_controls)
        has_deadline_layout.addWidget(self.has_deadline)
        
        # Add all deadline controls
        deadline_layout.addLayout(has_deadline_layout)
        deadline_layout.addLayout(deadline_date_layout)
        deadline_layout.addLayout(deadline_time_layout)
        
        details_layout.addLayout(deadline_layout)
        
        # Initialize deadline controls state
        self.toggle_deadline_controls(self.has_deadline.isChecked())
        
        # Priority & Category row
        priority_category_layout = QHBoxLayout()
        priority_category_layout.setSpacing(16)
        
        # Priority
        priority_layout = QVBoxLayout()
        priority_layout.setSpacing(8)
        
        priority_label = QLabel("Priority")
        priority_label.setObjectName("sectionLabel")
        priority_layout.addWidget(priority_label)
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["High", "Medium", "Low"])
        self.priority_combo.setCurrentText(self.todo.priority)
        priority_layout.addWidget(self.priority_combo)
        
        priority_category_layout.addLayout(priority_layout)
        
        # Category
        category_layout = QVBoxLayout()
        category_layout.setSpacing(8)
        
        category_label = QLabel("Category")
        category_label.setObjectName("sectionLabel")
        category_layout.addWidget(category_label)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.categories)
        if self.todo.category in self.categories:
            self.category_combo.setCurrentText(self.todo.category)
        else:
            self.category_combo.addItem(self.todo.category)
            self.category_combo.setCurrentText(self.todo.category)
        
        # Allow adding new categories
        self.category_combo.setEditable(True)
        category_layout.addWidget(self.category_combo)
        
        priority_category_layout.addLayout(category_layout)
        
        details_layout.addLayout(priority_category_layout)
        
        # Tags & Repeat row
        tags_repeat_layout = QHBoxLayout()
        tags_repeat_layout.setSpacing(16)
        
        # Tags
        tags_layout = QVBoxLayout()
        tags_layout.setSpacing(8)
        
        tags_label = QLabel("Tags")
        tags_label.setObjectName("sectionLabel")
        tags_layout.addWidget(tags_label)
        
        self.tags_edit = QLineEdit(", ".join(self.todo.tags) if self.todo.tags else "")
        self.tags_edit.setPlaceholderText("Comma-separated tags")
        
        # Add tag suggestions if available
        if self.all_tags:
            completer = QCompleter(self.all_tags)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            self.tags_edit.setCompleter(completer)
        
        tags_layout.addWidget(self.tags_edit)
        
        tags_repeat_layout.addLayout(tags_layout)
        
        # Repeat option
        repeat_layout = QVBoxLayout()
        repeat_layout.setSpacing(8)
        
        repeat_label = QLabel("Repeat")
        repeat_label.setObjectName("sectionLabel")
        repeat_layout.addWidget(repeat_label)
        
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItems(["None", "Daily", "Weekly", "Monthly"])
        self.repeat_combo.setCurrentText(self.todo.repeat_option or "None")
        repeat_layout.addWidget(self.repeat_combo)
        
        tags_repeat_layout.addLayout(repeat_layout)
        
        details_layout.addLayout(tags_repeat_layout)
        
        # Reminder section
        reminder_layout = QHBoxLayout()
        reminder_layout.setSpacing(16)
        
        has_reminder_layout = QVBoxLayout()
        has_reminder_layout.setSpacing(8)
        
        has_reminder_label = QLabel("Set Reminder")
        has_reminder_label.setObjectName("sectionLabel")
        has_reminder_layout.addWidget(has_reminder_label)
        
        self.has_reminder = QCheckBox("Enable")
        self.has_reminder.setChecked(self.todo.reminder_time is not None)
        self.has_reminder.stateChanged.connect(self.toggle_reminder_controls)
        has_reminder_layout.addWidget(self.has_reminder)
        
        reminder_time_layout = QVBoxLayout()
        reminder_time_layout.setSpacing(8)
        
        reminder_time_label = QLabel("Reminder Time")
        reminder_time_label.setObjectName("sectionLabel")
        reminder_time_layout.addWidget(reminder_time_label)
        
        self.reminder_time = QTimeEdit()
        
        # Set current reminder time if exists
        if self.todo.reminder_time:
            try:
                reminder_time = datetime.strptime(self.todo.reminder_time, "%H:%M").time()
                self.reminder_time.setTime(QTime(reminder_time.hour, reminder_time.minute))
            except (ValueError, TypeError):
                self.reminder_time.setTime(QTime(9, 0))  # Default 9am
        else:
            self.reminder_time.setTime(QTime(9, 0))  # Default 9am
        
        reminder_time_layout.addWidget(self.reminder_time)
        
        reminder_layout.addLayout(has_reminder_layout)
        reminder_layout.addLayout(reminder_time_layout)
        reminder_layout.addStretch()
        
        details_layout.addLayout(reminder_layout)
        
        # Initialize reminder controls state
        self.toggle_reminder_controls(self.has_reminder.isChecked())
        
        main_layout.addWidget(details_container)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        self.delete_btn = QPushButton("Delete Task")
        self.delete_btn.setObjectName("deleteButton")
        self.delete_btn.clicked.connect(self.confirm_delete)
        
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.setObjectName("saveButton")
        self.save_btn.clicked.connect(self.save_changes)
        
        buttons_layout.addWidget(self.delete_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(buttons_layout)
    
    def toggle_deadline_controls(self, enabled):
        """Enable/disable deadline controls based on checkbox"""
        self.deadline_date.setEnabled(enabled)
        self.deadline_time.setEnabled(enabled)
    
    def toggle_reminder_controls(self, enabled):
        """Enable/disable reminder controls based on checkbox"""
        self.reminder_time.setEnabled(enabled)
    
    def save_changes(self):
        """Save the updated todo"""
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Missing Title", "Please enter a task title.")
            return
        
        # Update todo with form values
        self.todo.text = title
        self.todo.completed = self.complete_checkbox.isChecked()
        self.todo.description = self.description_edit.text().strip()
        self.todo.priority = self.priority_combo.currentText()
        self.todo.category = self.category_combo.currentText()
        
        # Parse tags from comma-separated string
        tags_text = self.tags_edit.text().strip()
        if tags_text:
            self.todo.tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
        else:
            self.todo.tags = []
        
        # Set deadline
        if self.has_deadline.isChecked():
            date = self.deadline_date.date().toPyDate()
            time_val = self.deadline_time.time().toPyTime()
            deadline_dt = datetime.combine(date, time_val)
            self.todo.deadline = deadline_dt.isoformat()
        else:
            self.todo.deadline = None
        
        # Set reminder
        if self.has_reminder.isChecked():
            time_val = self.reminder_time.time().toPyTime()
            self.todo.reminder_time = time_val.strftime("%H:%M")
        else:
            self.todo.reminder_time = None
        
        # Set repeat option
        repeat_option = self.repeat_combo.currentText()
        self.todo.repeat_option = None if repeat_option == "None" else repeat_option
        
        # Emit the update signal
        self.todoUpdated.emit(self.todo)
        self.accept()
    
    def confirm_delete(self):
        """Confirm before deleting a task"""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this task?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.todoDeleted.emit(self.todo.id)
            self.accept()
    
    def apply_styles(self):
        """Apply theme-based styles to the dialog"""
        surface_color = self.colors.get('surface', '#2C2C2E')
        background_color = self.colors.get('background', '#1C1C1E')
        text_color = self.colors.get('text', '#FFFFFF')
        border_color = self.colors.get('border', '#3A3A3C')
        muted_color = self.colors.get('text_secondary', '#98989E')
        primary_color = self.colors.get('primary', '#0A84FF')
        danger_color = self.colors.get('accent', '#FF453A')
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {background_color};
                color: {text_color};
            }}
            
            #titleEdit {{
                color: {text_color};
                font-size: 18px;
                font-weight: bold;
                background-color: transparent;
                border: none;
                border-bottom: 1px solid {border_color};
                padding: 8px 0;
            }}
            
            #detailsContainer {{
                background-color: {surface_color};
                border-radius: 12px;
                padding: 8px;
            }}
            
            QLabel {{
                color: {text_color};
            }}
            
            #sectionLabel {{
                color: {muted_color};
                font-size: 13px;
            }}
            
            QLineEdit, QDateEdit, QTimeEdit, QComboBox {{
                background-color: {background_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 8px;
                selection-background-color: {primary_color};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            
            QComboBox::down-arrow {{
                image: url(assets/icons/dropdown.svg);
                width: 12px;
                height: 12px;
            }}
            
            QCheckBox {{
                color: {text_color};
            }}
            
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {border_color};
                border-radius: 4px;
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {primary_color};
                image: url(assets/icons/check.svg);
            }}
            
            QPushButton {{
                background-color: {surface_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {surface_color}CC;
            }}
            
            #saveButton {{
                background-color: {primary_color};
                color: white;
                border: none;
            }}
            
            #saveButton:hover {{
                background-color: {primary_color}DD;
            }}
            
            #deleteButton {{
                background-color: transparent;
                color: {danger_color};
                border: 1px solid {danger_color};
            }}
            
            #deleteButton:hover {{
                background-color: {danger_color}22;
            }}
        """)

# ======================================================
# Todo List Widget
# ======================================================

class TodoListWidget(QWidget):
    """Main todo list widget that can be integrated into the app"""
    tasksChanged = pyqtSignal()  # Signal when tasks change (for achievements)
    
    def __init__(self, settings_manager=None, theme="dark v2", parent=None):
        super().__init__(parent)
        self.theme = theme
        self.colors = MODERN_COLORS.get(theme.lower(), MODERN_COLORS["dark v2"])
        self.settings_manager = settings_manager
        
        # Task data
        self.todos = []
        self.categories = ["Personal", "Work", "Health", "Shopping", "Other"]
        self.selected_category = "All"
        self.filter_completed = False
        
        # State
        self.modified = False
        self.reminder_checked = False
        
        # Setup UI
        self.init_ui()
        
        # Load saved todos
        self.load_todos()
        
        # Start reminder timer
        self.setup_reminder_timer()
        
        # Check for any overdue tasks
        QTimer.singleShot(1000, self.check_todos_on_startup)
    
    def init_ui(self):
        """Initialize the widget UI"""
        # Set up main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header with title and add button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)
        
        title_label = QLabel("To-Do")
        title_label.setObjectName("pageTitle")
        header_layout.addWidget(title_label)
        
        # Spacer to push buttons to the right
        header_layout.addStretch(1)
        
        # Filter button
        self.filter_btn = QPushButton("Filter")
        self.filter_btn.setObjectName("filterButton")
        self.filter_btn.setIcon(QIcon(resource_path("assets/icons/filter.svg")))
        self.filter_btn.setCursor(Qt.PointingHandCursor)
        self.filter_btn.clicked.connect(self.show_filter_menu)
        header_layout.addWidget(self.filter_btn)
        
        # Add task button
        self.add_btn = QPushButton("Add Task")
        self.add_btn.setObjectName("addButton")
        self.add_btn.setIcon(QIcon(resource_path("assets/icons/plus.svg")))
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.clicked.connect(self.add_new_task)
        header_layout.addWidget(self.add_btn)
        
        main_layout.addLayout(header_layout)
        
        # Quick add row (simplified entry)
        quick_add_layout = QHBoxLayout()
        quick_add_layout.setSpacing(12)
        
        self.quick_add_edit = QLineEdit()
        self.quick_add_edit.setObjectName("quickAddEdit")
        self.quick_add_edit.setPlaceholderText("Add a task, press Enter to save")
        self.quick_add_edit.returnPressed.connect(self.quick_add_task)
        quick_add_layout.addWidget(self.quick_add_edit, 1)
        
        main_layout.addLayout(quick_add_layout)
        
        # Filter summary label (shows current filter settings)
        self.filter_label = QLabel("Showing: All categories, Incomplete tasks")
        self.filter_label.setObjectName("filterLabel")
        main_layout.addWidget(self.filter_label)
        
        # Create main task list with scrolling
        task_scroll = QScrollArea()
        task_scroll.setObjectName("taskScroll")
        task_scroll.setWidgetResizable(True)
        task_scroll.setFrameShape(QFrame.NoFrame)
        task_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.task_container = QWidget()
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.setContentsMargins(2, 2, 2, 2)
        self.task_layout.setSpacing(8)
        self.task_layout.addStretch(1)  # Push items to the top
        
        task_scroll.setWidget(self.task_container)
        main_layout.addWidget(task_scroll, 1)  # Give this most of the space
        
        # Stats and batch actions
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        
        # Stats label
        self.stats_label = QLabel("0 tasks, 0 completed")
        self.stats_label.setObjectName("statsLabel")
        stats_layout.addWidget(self.stats_label)
        
        stats_layout.addStretch(1)
        
        # Clear completed button
        self.clear_btn = QPushButton("Clear Completed")
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear_completed_tasks)
        stats_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(stats_layout)
        
        # Apply theme styles
        self.apply_styles()
    
    def apply_styles(self):
        """Apply current theme styles to the widget"""
        background_color = self.colors.get('background', '#1C1C1E')
        surface_color = self.colors.get('surface', '#2C2C2E')
        text_color = self.colors.get('text', '#FFFFFF')
        primary_color = self.colors.get('primary', '#0A84FF')
        secondary_color = self.colors.get('secondary', '#52A8FF')
        border_color = self.colors.get('border', '#3A3A3C')
        muted_color = self.colors.get('text_secondary', '#98989E')
        
        self.setStyleSheet(f"""
            /* Main widget */
            TodoListWidget {{
                background-color: {background_color};
                color: {text_color};
            }}
            
            /* Headers */
            #pageTitle {{
                color: {text_color};
                font-size: 24px;
                font-weight: bold;
            }}
            
            /* Buttons */
            #addButton {{
                background-color: {primary_color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            
            #addButton:hover {{
                background-color: {secondary_color};
            }}
            
            #filterButton {{
                background-color: transparent;
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 8px 16px;
            }}
            
            #filterButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            
            #clearButton {{
                background-color: transparent;
                color: {primary_color};
                border: 1px solid {primary_color};
                border-radius: 8px;
                padding: 4px 12px;
            }}
            
            #clearButton:hover {{
                background-color: {primary_color}20;
            }}
            
            /* Quick add */
            #quickAddEdit {{
                background-color: {surface_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 15px;
            }}
            
            #quickAddEdit:focus {{
                border: 1px solid {primary_color};
            }}
            
            /* Filter label */
            #filterLabel {{
                color: {muted_color};
                font-size: 13px;
                font-style: italic;
            }}
            
            /* Stats label */
            #statsLabel {{
                color: {muted_color};
                font-size: 14px;
            }}
            
            /* Scrollbar styling */
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background: {border_color}80;
                border-radius: 4px;
                min-height: 30px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: {border_color};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
    
    def setup_reminder_timer(self):
        """Set up timer to check for reminders"""
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(60000)  # Check every minute
    
    def load_todos(self):
        """Load todos from settings"""
        if not self.settings_manager:
            # Create some sample todos if no settings manager
            self.create_sample_todos()
            return
        
        try:
            todos_data = self.settings_manager.get("todos")
            if not todos_data:
                self.create_sample_todos()
                return
            
            # Convert stored data to TodoItem objects
            self.todos = [TodoItem.from_dict(item) for item in todos_data]
            
            # Handle repeating tasks that need new instances
            self.process_repeating_tasks()
            
            # Update UI
            self.update_task_list()
            self.update_stats()
        except Exception as e:
            print(f"Error loading todos: {e}")
            # Fall back to sample todos
            self.create_sample_todos()
    
    def create_sample_todos(self):
        """Create some sample todos for first-time users"""
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        
        self.todos = [
            TodoItem(
                text="Drink 8 glasses of water",
                priority="High",
                category="Health",
                deadline=today.replace(hour=18, minute=0).isoformat(),
                tags=["health", "daily"]
            ),
            TodoItem(
                text="Add your own tasks here",
                priority="Medium",
                category="Personal"
            ),
            TodoItem(
                text="Customize app settings",
                priority="Low",
                category="Other",
                deadline=tomorrow.replace(hour=12, minute=0).isoformat()
            )
        ]
        
        self.update_task_list()
        self.update_stats()
    
    def save_todos(self):
        """Save todos to settings"""
        if not self.settings_manager:
            return
        
        try:
            # Convert TodoItems to dictionaries
            todos_data = [todo.to_dict() for todo in self.todos]
            self.settings_manager.set("todos", todos_data)
            self.settings_manager.save_settings()
            self.modified = False
        except Exception as e:
            print(f"Error saving todos: {e}")
    
    def process_repeating_tasks(self):
        """Process repeating tasks and create new instances if needed"""
        today = datetime.now().date()
        new_todos = []
        
        for todo in self.todos[:]:
            if todo.completed and todo.repeat_option:
                # Get completion date
                try:
                    if not todo.completed_at:
                        # Skip if no completion timestamp
                        continue
                    
                    completed_dt = datetime.fromisoformat(todo.completed_at)
                    completed_date = completed_dt.date()
                    
                    # Only create a new task if the completion was recent
                    days_since_completion = (today - completed_date).days
                    
                    if days_since_completion <= 0:
                        # Skip if completed today (avoid duplicates)
                        continue
                    
                    # Determine if we need to create a new instance based on repeat pattern
                    create_new = False
                    
                    if todo.repeat_option == "Daily":
                        create_new = True
                    elif todo.repeat_option == "Weekly" and days_since_completion >= 7:
                        create_new = True
                    elif todo.repeat_option == "Monthly" and days_since_completion >= 28:
                        create_new = True
                    
                    if create_new:
                        # Create a new instance of this task
                        new_todo = TodoItem(
                            text=todo.text,
                            priority=todo.priority,
                            tags=todo.tags,
                            category=todo.category,
                            description=todo.description,
                            repeat_option=todo.repeat_option,
                            reminder_time=todo.reminder_time
                        )
                        
                        # Set new deadline if original had one
                        if todo.deadline:
                            try:
                                deadline_dt = datetime.fromisoformat(todo.deadline)
                                if todo.repeat_option == "Daily":
                                    new_deadline = datetime.combine(today, deadline_dt.time())
                                elif todo.repeat_option == "Weekly":
                                    days_to_add = 7
                                    new_deadline = deadline_dt + timedelta(days=days_to_add)
                                elif todo.repeat_option == "Monthly":
                                    # Try to maintain the same day of month
                                    day = min(deadline_dt.day, 28)  # Cap at 28 to handle all months
                                    month = today.month
                                    year = today.year
                                    if month == 12:
                                        month = 1
                                        year += 1
                                    else:
                                        month += 1
                                    new_date = datetime(year, month, day).date()
                                    new_deadline = datetime.combine(new_date, deadline_dt.time())
                                else:
                                    new_deadline = None
                                
                                if new_deadline:
                                    new_todo.deadline = new_deadline.isoformat()
                            except (ValueError, TypeError):
                                # In case of errors, don't set a deadline
                                pass
                        
                        new_todos.append(new_todo)
                except (ValueError, TypeError):
                    # Skip this task if there are date parsing issues
                    continue
        
        # Add any new repeating tasks
        if new_todos:
            self.todos.extend(new_todos)
            self.modified = True
    
    def update_task_list(self):
        """Update the task list UI based on current todos and filters"""
        # Clear existing tasks
        self._clear_task_layout()
        
        # Filter tasks
        filtered_todos = self.get_filtered_todos()
        
        if not filtered_todos:
            # Show empty state
            empty_label = QLabel("No tasks match your filters")
            empty_label.setObjectName("emptyLabel")
            empty_label.setAlignment(Qt.AlignCenter)
            self.task_layout.insertWidget(0, empty_label)
        else:
            # Add task widgets in reverse order (newest at top)
            for todo in reversed(filtered_todos):
                todo_widget = TodoItemWidget(todo, self.theme)
                
                # Connect signals
                todo_widget.completed.connect(self.on_task_completed)
                todo_widget.deleted.connect(self.on_task_deleted)
                todo_widget.details_requested.connect(self.on_task_details)
                
                self.task_layout.insertWidget(0, todo_widget)
    
    def _clear_task_layout(self):
        """Clear all task widgets from the layout"""
        while self.task_layout.count() > 1:  # Keep the stretch
            item = self.task_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def get_filtered_todos(self):
        """Get todos filtered by current filter settings"""
        # Apply category filter
        if self.selected_category == "All":
            filtered = self.todos[:]
        else:
            filtered = [todo for todo in self.todos if todo.category == self.selected_category]
        
        # Apply completed filter
        if self.filter_completed:
            filtered = [todo for todo in filtered if not todo.completed]
        
        return filtered
    
    def update_stats(self):
        """Update stats label with current counts"""
        total = len(self.todos)
        completed = sum(1 for todo in self.todos if todo.completed)
        
        self.stats_label.setText(f"{total} tasks, {completed} completed")
        
        # Update filter label
        category_text = "All categories" if self.selected_category == "All" else f"Category: {self.selected_category}"
        completed_text = "Incomplete tasks" if self.filter_completed else "All tasks"
        self.filter_label.setText(f"Showing: {category_text}, {completed_text}")
    
    def update_filter_label(self):
        """Update the filter summary label"""
        category_text = "All categories" if self.selected_category == "All" else f"Category: {self.selected_category}"
        completed_text = "Incomplete tasks" if self.filter_completed else "All tasks"
        self.filter_label.setText(f"Showing: {category_text}, {completed_text}")
    
    def on_task_completed(self, task_id, completed):
        """Handle task completion status change"""
        for todo in self.todos:
            if todo.id == task_id:
                todo.completed = completed
                if completed:
                    todo.completed_at = datetime.now().isoformat()
                else:
                    todo.completed_at = None
                
                self.modified = True
                self.save_todos()
                self.update_stats()
                
                # Emit signal for achievements
                self.tasksChanged.emit()
                break
    
    def on_task_deleted(self, task_id):
        """Handle task deletion"""
        for i, todo in enumerate(self.todos):
            if todo.id == task_id:
                self.todos.pop(i)
                self.modified = True
                self.save_todos()
                self.update_task_list()
                self.update_stats()
                
                # Emit signal for achievements
                self.tasksChanged.emit()
                break
    
    def on_task_details(self, task_id):
        """Show task details dialog"""
        # Find the todo item
        todo = None
        for t in self.todos:
            if t.id == task_id:
                todo = t
                break
        
        if not todo:
            return
        
        # Create and show the details dialog
        dialog = TodoDetailDialog(todo, self.categories, self.theme, self)
        dialog.todoUpdated.connect(self.on_task_updated)
        dialog.todoDeleted.connect(self.on_task_deleted)
        dialog.exec_()
    
    def on_task_updated(self, updated_todo):
        """Handle task update from detail dialog"""
        # Find and update the todo
        for i, todo in enumerate(self.todos):
            if todo.id == updated_todo.id:
                self.todos[i] = updated_todo
                self.modified = True
                
                # Add new category if it doesn't exist
                if updated_todo.category and updated_todo.category not in self.categories:
                    self.categories.append(updated_todo.category)
                
                self.save_todos()
                self.update_task_list()
                self.update_stats()
                
                # Emit signal for achievements
                self.tasksChanged.emit()
                break
    
    def quick_add_task(self):
        """Quickly add a task from the quick add field"""
        text = self.quick_add_edit.text().strip()
        if not text:
            return
        
        # Create a new task with some defaults
        new_todo = TodoItem(
            text=text,
            priority="Medium",
            category=self.selected_category if self.selected_category != "All" else "Personal"
        )
        
        # Check for smart syntax for priority: ! for high, !! for medium (default)
        if text.endswith("!!!"):
            new_todo.text = text[:-3].strip()
            new_todo.priority = "High"
        elif text.endswith("!!"):
            new_todo.text = text[:-2].strip()
            new_todo.priority = "Medium"
        elif text.endswith("!"):
            new_todo.text = text[:-1].strip()
            new_todo.priority = "Low"
        
        # Parse deadlines with @ syntax: @tomorrow, @friday, @5/15, etc.
        deadlines = {
            "@today": datetime.now().date(),
            "@tomorrow": datetime.now().date() + timedelta(days=1),
            "@nextweek": datetime.now().date() + timedelta(days=7)
        }
        
        # Check for date keywords
        for keyword, date_val in deadlines.items():
            if keyword in text.lower():
                new_todo.text = new_todo.text.replace(keyword, "").strip()
                new_todo.deadline = datetime.combine(date_val, time(18, 0)).isoformat()
                break
        
        # Parse tags with # syntax: #work #personal
        tags = []
        words = text.split()
        for word in words:
            if word.startswith("#"):
                tag = word[1:]
                if tag:
                    tags.append(tag)
                    new_todo.text = new_todo.text.replace(word, "").strip()
        
        if tags:
            new_todo.tags = tags
        
        # Add the task
        self.todos.append(new_todo)
        self.modified = True
        self.save_todos()
        self.update_task_list()
        self.update_stats()
        
        # Clear quick add field
        self.quick_add_edit.clear()
        
        # Emit signal for achievements
        self.tasksChanged.emit()
    
    def add_new_task(self):
        """Open the full task detail dialog to add a new task"""
        # Create a blank task
        new_todo = TodoItem()
        
        # Set default category if filter is active
        if self.selected_category != "All":
            new_todo.category = self.selected_category
        
        # Show detail dialog
        dialog = TodoDetailDialog(new_todo, self.categories, self.theme, self)
        dialog.todoUpdated.connect(self.on_new_task_added)
        dialog.exec_()
    
    def on_new_task_added(self, new_todo):
        """Handle a new task created from the detail dialog"""
        self.todos.append(new_todo)
        
        # Add new category if it doesn't exist
        if new_todo.category and new_todo.category not in self.categories:
            self.categories.append(new_todo.category)
        
        self.modified = True
        self.save_todos()
        self.update_task_list()
        self.update_stats()
        
        # Emit signal for achievements
        self.tasksChanged.emit()
    
    def show_filter_menu(self):
        """Show filter dropdown menu"""
        menu = QMenu(self)
        
        # Category submenu
        categories_menu = QMenu("Categories", menu)
        
        # Add "All" option
        all_action = QAction("All", categories_menu)
        all_action.setCheckable(True)
        all_action.setChecked(self.selected_category == "All")
        all_action.triggered.connect(lambda: self.set_category_filter("All"))
        categories_menu.addAction(all_action)
        
        categories_menu.addSeparator()
        
        # Add category options
        for category in sorted(self.categories):
            category_action = QAction(category, categories_menu)
            category_action.setCheckable(True)
            category_action.setChecked(self.selected_category == category)
            category_action.triggered.connect(lambda checked, cat=category: self.set_category_filter(cat))
            categories_menu.addAction(category_action)
        
        # Add categories submenu
        menu.addMenu(categories_menu)
        
        menu.addSeparator()
        
        # Show completed tasks option
        completed_action = QAction("Show Completed Tasks", menu)
        completed_action.setCheckable(True)
        completed_action.setChecked(not self.filter_completed)
        completed_action.triggered.connect(self.toggle_completed_filter)
        menu.addAction(completed_action)
        
        # Show menu under the filter button
        menu.exec_(self.filter_btn.mapToGlobal(
            QPoint(0, self.filter_btn.height())))
    
    def set_category_filter(self, category):
        """Set category filter"""
        self.selected_category = category
        self.update_task_list()
        self.update_filter_label()
    
    def toggle_completed_filter(self, show_completed):
        """Toggle filter for completed tasks"""
        self.filter_completed = not show_completed
        self.update_task_list()
        self.update_filter_label()
    
    def clear_completed_tasks(self):
        """Remove all completed tasks after confirmation"""
        # Count completed tasks
        completed_count = sum(1 for todo in self.todos if todo.completed)
        
        if completed_count == 0:
            QMessageBox.information(self, "No Completed Tasks", 
                                  "There are no completed tasks to clear.")
            return
        
        # Ask for confirmation
        reply = QMessageBox.question(
            self, "Clear Completed Tasks",
            f"Are you sure you want to delete {completed_count} completed tasks?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove completed tasks
            self.todos = [todo for todo in self.todos if not todo.completed]
            self.modified = True
            self.save_todos()
            self.update_task_list()
            self.update_stats()
            
            # Emit signal for achievements
            self.tasksChanged.emit()
    
    def check_reminders(self):
        """Check for tasks with active reminders"""
        # Don't check more than once per minute
        current_time = datetime.now().strftime("%H:%M")
        
        # Skip if already checked this minute
        if hasattr(self, 'last_check_time') and self.last_check_time == current_time:
            return
        
        self.last_check_time = current_time
        
        # Check each task for reminders
        reminders = []
        for todo in self.todos:
            if todo.should_remind():
                reminders.append(todo)
        
        # Show notification if any reminders are due
        if reminders:
            self.show_reminders(reminders)
    
    def show_reminders(self, reminder_tasks):
        """Show notification for tasks with reminders"""
        # Use parent's show_message method if available
        if self.parent() and hasattr(self.parent(), 'show_message'):
            if len(reminder_tasks) == 1:
                task = reminder_tasks[0]
                message = f"Reminder: {task.text}"
                self.parent().show_message(message)
            else:
                message = f"Reminder: {len(reminder_tasks)} tasks due"
                self.parent().show_message(message)
        else:
            # Fallback to message box
            if len(reminder_tasks) == 1:
                QMessageBox.information(self, "Task Reminder", 
                                      f"Reminder: {reminder_tasks[0].text}")
            else:
                task_list = "\n".join([f"• {task.text}" for task in reminder_tasks[:5]])
                if len(reminder_tasks) > 5:
                    task_list += f"\n...and {len(reminder_tasks) - 5} more"
                QMessageBox.information(self, "Task Reminders", 
                                      f"You have {len(reminder_tasks)} tasks due:\n\n{task_list}")
    
    def check_todos_on_startup(self):
        """Check for overdue or today's tasks on app startup"""
        # Group tasks by status
        today = datetime.now().date()
        today_tasks = []
        overdue_tasks = []
        
        for todo in self.todos:
            if todo.completed:
                continue
                
            if todo.deadline:
                try:
                    deadline_dt = datetime.fromisoformat(todo.deadline)
                    deadline_date = deadline_dt.date()
                    
                    if deadline_date < today:
                        overdue_tasks.append(todo)
                    elif deadline_date == today:
                        today_tasks.append(todo)
                except (ValueError, TypeError):
                    pass
        
        # Show summary message if there are tasks
        if overdue_tasks or today_tasks:
            # Use parent's show_message method if available
            message = ""
            if overdue_tasks:
                message += f"{len(overdue_tasks)} task{'s' if len(overdue_tasks) > 1 else ''} overdue. "
            if today_tasks:
                message += f"{len(today_tasks)} task{'s' if len(today_tasks) > 1 else ''} due today."
                
            if self.parent() and hasattr(self.parent(), 'show_message'):
                self.parent().show_message(message)
    
    def get_task_stats(self):
        """Get statistics about tasks for achievements"""
        total = len(self.todos)
        completed = sum(1 for todo in self.todos if todo.completed)
        today = datetime.now().date()
        
        # Count tasks completed today
        completed_today = 0
        for todo in self.todos:
            if todo.completed and todo.completed_at:
                try:
                    completed_date = datetime.fromisoformat(todo.completed_at).date()
                    if completed_date == today:
                        completed_today += 1
                except (ValueError, TypeError):
                    pass
        
        # Count overdue tasks
        overdue = sum(1 for todo in self.todos if todo.is_overdue())
        
        # Count tasks by category
        categories = {}
        for todo in self.todos:
            cat = todo.category or "Uncategorized"
            if cat not in categories:
                categories[cat] = {"total": 0, "completed": 0}
            categories[cat]["total"] += 1
            if todo.completed:
                categories[cat]["completed"] += 1
        
        return {
            "total": total,
            "completed": completed,
            "completed_today": completed_today,
            "completion_rate": completed / total if total > 0 else 0,
            "overdue": overdue,
            "categories": categories
        }
    
    def get_all_tags(self):
        """Get all unique tags from all tasks"""
        tags = set()
        for todo in self.todos:
            if todo.tags:
                tags.update(todo.tags)
        return sorted(list(tags))
    
    def closeEvent(self, event):
        """Save todos before closing"""
        if self.modified:
            self.save_todos()
        super().closeEvent(event)