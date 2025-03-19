# core/main_window.py
import os
import subprocess
import time
import random
import calendar
from datetime import datetime, timedelta
import json

from PyQt5.QtCore import (Qt, QTimer, QRectF, QPropertyAnimation, QPoint, QEasingCurve,
                          QUrl, QSize, QParallelAnimationGroup, pyqtSignal, QAbstractAnimation)
from PyQt5.QtGui import (QPainter, QPen, QColor, QFont, QIcon, QBrush,
                         QFontDatabase, QGuiApplication, QCloseEvent, QRegion, QPainterPath)
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                             QMenu, QAction, QSystemTrayIcon, QMessageBox, QSpacerItem, QSizePolicy,
                             QGraphicsDropShadowEffect, QFrame)
from PyQt5.QtMultimedia import QSoundEffect

from config import MODERN_COLORS, SOUND_OPTIONS  
from widgets.progress_ring_widget import ProgressRingWidget
from dialogs.history_window import HistoryWindow
from dialogs.settings_dialog import SettingsDialog
from core.settings_manager import SettingsManager
from dialogs.reminder_dialog import ReminderDialog
from widgets.toast import ToastLabel
from utils import resource_path
from widgets.time_since import LoveTimer
from widgets.todo_widget import TodoListWidget
from widgets.tracker_widget import WaterLevelWidget
from dialogs.profile_system import install_profile_system

class MainWindow(QMainWindow):
    history_updated = pyqtSignal()  
    theme_changed = pyqtSignal()

    def __init__(self, settings_manager: SettingsManager):
        super().__init__()
        self.settings_manager = settings_manager

        # Load settings
        self.min_hydration_interval = self.settings_manager.get('min_minutes')
        self.max_hydration_interval = self.settings_manager.get('max_minutes')
        self.snooze_duration = self.settings_manager.get('snooze_minutes')
        self.daily_hydration_goal = self.settings_manager.get('daily_goal')
        self.sound_enabled = self.settings_manager.get('sound_enabled')
        self.sound_file = self.settings_manager.get('sound_choice')
        self.hydration_log_count = self.settings_manager.get('log_count')
        self.theme_name = self.settings_manager.get('theme')
        self.show_progress_text = self.settings_manager.get('show_progress_text')
        self.exit_on_close = False

        self.setWindowTitle("Bea Apă")
        self.setFixedSize(420, 700)
        self.setWindowIcon(QIcon(resource_path("assets/icons/icon.png")))
        QFontDatabase.addApplicationFont(resource_path("assets/fonts/SegoeUI.ttf"))

        self.init_data()
        self.check_daily_reset()
        self.schedule_daily_reset()
        self.init_ui()
        self.setup_tray_icon()
        self.profile_system = install_profile_system(self)
        

        self.apply_theme()




    def init_data(self):
        self.motivational_quotes = self.load_motivational_quotes()
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.show_reminder)
        self.schedule_reminder()

        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_timer)
        self.countdown_timer.start(1000)

        self.sound_effect = QSoundEffect()
        self.sound_effect.setVolume(1)
        self.water_level = None

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Apply container shadow for depth
        container_shadow = QGraphicsDropShadowEffect()
        container_shadow.setBlurRadius(20)
        container_shadow.setColor(QColor(0, 0, 0, 50))
        container_shadow.setOffset(0, 2)
        central_widget.setGraphicsEffect(container_shadow)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)

        # ===== Header Section =====
        header_container = QFrame()
        header_container.setObjectName("headerContainer")
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = QLabel("Bea Apă")
        self.title_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        self.title_label.setObjectName("titleLabel")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch(1)
        
        self.menu_btn = QPushButton()
        self.menu_btn.setIcon(QIcon(resource_path("assets/icons/menu.svg")))
        self.menu_btn.setFixedSize(48, 48)
        self.menu_btn.setObjectName("menuButton")
        self.menu_btn.setToolTip("Open Menu")
        self.menu_btn.setCursor(Qt.PointingHandCursor)
        self.menu_btn.clicked.connect(self.show_context_menu)
        header_layout.addWidget(self.menu_btn)
        
        main_layout.addWidget(header_container)

        # ===== Progress Section =====
        progress_container = QFrame()
        progress_container.setObjectName("progressContainer")
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(16)
        
        self.progress_ring = ProgressRingWidget()
        self.progress_ring.setFixedSize(300, 300)
        self.progress_ring.setObjectName("progressRing")
        
        ring_shadow = QGraphicsDropShadowEffect()
        ring_shadow.setBlurRadius(20)
        ring_shadow.setColor(QColor(0, 0, 0, 40))
        ring_shadow.setOffset(0, 4)
        self.progress_ring.setGraphicsEffect(ring_shadow)
        
        progress_layout.addWidget(self.progress_ring, 0, Qt.AlignCenter)
        
        main_layout.addWidget(progress_container)
        
        # Store the original position of the progress_ring after layout
        QTimer.singleShot(0, lambda: setattr(self, 'initial_progress_ring_pos', self.progress_ring.pos()))

        # ===== Stats Section =====
        stats_container = QFrame()
        stats_container.setObjectName("statsContainer")
        stats_layout = QHBoxLayout(stats_container)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(16)
        
        self.stats_today = self.create_stat_widget("Today", "0")
        self.stats_avg = self.create_stat_widget("7-day Avg", "0")
        self.stats_streak = self.create_stat_widget("Streak", "0 🔥")
        
        stats_layout.addWidget(self.stats_today)
        stats_layout.addWidget(self.stats_avg)
        stats_layout.addWidget(self.stats_streak)
        
        main_layout.addWidget(stats_container)

        # ===== Control Section =====
        controls_container = QFrame()
        controls_container.setObjectName("controlsContainer")
        controls_layout = QVBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(16)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(16)
        
        self.log_btn = QPushButton("Log Drink")
        self.log_btn.setFixedHeight(56)
        self.log_btn.setObjectName("logButton")
        self.log_btn.setIcon(QIcon(resource_path("assets/icons/plus.svg")))
        self.log_btn.setIconSize(QSize(22, 22))
        self.log_btn.setToolTip("Record a water drink")
        self.log_btn.setCursor(Qt.PointingHandCursor)
        self.log_btn.clicked.connect(self.log_drink)
        
        self.snooze_btn = QPushButton("Snooze")
        self.snooze_btn.setFixedHeight(56)
        self.snooze_btn.setObjectName("snoozeButton")
        self.snooze_btn.setIcon(QIcon(resource_path("assets/icons/snooze.svg")))
        self.snooze_btn.setIconSize(QSize(22, 22))
        self.snooze_btn.setToolTip("Snooze the next reminder")
        self.snooze_btn.setCursor(Qt.PointingHandCursor)
        self.snooze_btn.clicked.connect(self.snooze_reminder)
        
        button_layout.addWidget(self.log_btn)
        button_layout.addWidget(self.snooze_btn)
        controls_layout.addLayout(button_layout)
        
        self.countdown_container = QFrame()
        self.countdown_container.setObjectName("countdownContainer")
        countdown_layout = QVBoxLayout(self.countdown_container)
        countdown_layout.setContentsMargins(16, 12, 16, 12)
        
        countdown_title = QLabel("Next reminder in")
        countdown_title.setObjectName("countdownTitle")
        countdown_title.setAlignment(Qt.AlignCenter)
        countdown_layout.addWidget(countdown_title)
        
        self.countdown_label = QLabel("00:00")
        self.countdown_label.setObjectName("countdownLabel")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        countdown_layout.addWidget(self.countdown_label)
        
        controls_layout.addWidget(self.countdown_container)
        
        main_layout.addWidget(controls_container)

        # Initialize wave_animation once and reuse it
        self.wave_animation = QPropertyAnimation(self.progress_ring, b"pos")
        self.wave_animation.setDuration(400)
        self.wave_animation.setEasingCurve(QEasingCurve.OutElastic)

    def get_theme(self):
        """Return the current theme dictionary for UI components"""
        theme = MODERN_COLORS.get(self.theme_name.lower())
        if not theme:
            print(f"Warning: Theme '{self.theme_name}' not found. Using default theme.")
            theme = MODERN_COLORS.get("dark v2")
        return theme

    def create_stat_widget(self, title, value):
        widget = QFrame()
        widget.setObjectName("statWidget")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        return widget

    def apply_theme(self):
        theme = MODERN_COLORS.get(self.theme_name.lower())
        if not theme:
            print(f"Warning: Theme '{self.theme_name}' not found. Using default theme.")
            theme = MODERN_COLORS.get("dark v2")
            
        accent_dark = theme.get('accent_dark')
        if not accent_dark:
            accent_color = theme.get('accent', '#EF4565')
            accent_dark = accent_color 
                
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {theme['background']};
                color: {theme['text']};
                font-family: 'Segoe UI', sans-serif;
            }}
            
            #titleLabel {{
                color: {theme['text']};
                font-size: 28px;
                font-weight: bold;
                letter-spacing: -0.5px;
            }}
            
            #menuButton {{
                background-color: transparent;
                border: none;
                border-radius: 24px;
            }}
            
            #menuButton:hover {{
                background-color: {theme.get('highlight', '#72757E')}40;
            }}
            
            #statWidget {{
                background-color: {theme.get('surface', theme['background'])};
                border-radius: 16px;
                border: 1px solid {theme.get('border', '#555')}50;
            }}
            
            #statTitle {{
                color: {theme['text']}80;
                font-size: 14px;
                font-weight: normal;
                background-color: transparent;
            }}
            
            #statValue {{
                color: {theme['text']};
                font-size: 20px;
                font-weight: bold;
                background-color: transparent;
            }}
            
            #logButton, #snoozeButton {{
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: 600;
                padding: 8px 16px;
            }}
            
            #logButton {{
                background-color: {theme['primary']};
                color: white;
            }}
            
            #logButton:hover {{
                background-color: {theme.get('secondary', theme['primary'])};
            }}
            
            #snoozeButton {{
                background-color: {theme['accent']};
                color: white;
            }}
            
            #snoozeButton:hover {{
                background-color: {accent_dark};
            }}
            
            #countdownContainer {{
                background-color: {theme.get('surface', theme['background'])};
                border-radius: 16px;
                border: 1px solid {theme.get('border', '#555')}50;
            }}
            
            #countdownTitle {{
                color: {theme['text']}80;
                font-size: 14px;
                background-color: transparent;
            }}
            
            #countdownLabel {{
                color: {theme['text']};
                font-size: 24px;
                font-weight: bold;
                background-color: transparent;
            }}
            
            QToolTip {{
                background-color: {theme.get('surface', theme['background'])};
                color: {theme['text']};
                border: 1px solid {theme.get('border', '#555')};
                border-radius: 6px;
                padding: 6px;
                font-size: 14px;
            }}
        """)
        
        self.update_progress_ring()

        if hasattr(self, 'theme_changed'):
            self.theme_changed.emit()

    def show_profile_page(self):
        """Show the profile page with achievements"""
        try:
            from dialogs.profile_page import ProfilePage
            profile_dialog = ProfilePage(self)
            profile_dialog.exec_()
        except Exception as e:
            print(f"Error showing profile page: {e}")
            self.show_message(f"Could not show profile page: {str(e)}")

    def load_motivational_quotes(self):
        quotes_file = resource_path(os.path.join("assets", "data", "motivational_quotes.json"))
        try:
            with open(quotes_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("quotes", [])
        except Exception as e:
            print(f"Error loading motivational quotes: {e}")
            return []

    def update_progress_ring(self):
        progress = min(self.hydration_log_count / self.daily_hydration_goal, 1.0)
        countdown_progress = self.get_countdown_progress()
        self.progress_ring.setProgress(progress, self.hydration_log_count, self.daily_hydration_goal,
                                         self.show_progress_text, self.theme_name, countdown_progress)
        self.update_stats()

    def update_stats(self):
        today = datetime.now().date()
        history = self.settings_manager.get("history")

        sum_last_7_days = 0
        for i in range(7):
            day = today - timedelta(days=i)
            count = self.hydration_log_count if day == today else history.get(day.isoformat(), 0)
            sum_last_7_days += count
        avg = sum_last_7_days / 7.0

        streak = 0
        day = today
        while True:
            count = self.hydration_log_count if day == today else history.get(day.isoformat(), 0)
            if count > 0:
                streak += 1
                day -= timedelta(days=1)
            else:
                break
                
        self.stats_today.findChild(QLabel, "statValue").setText(f"{self.hydration_log_count}")
        self.stats_avg.findChild(QLabel, "statValue").setText(f"{avg:.1f}")
        self.stats_streak.findChild(QLabel, "statValue").setText(f"{streak} 🔥")

    def get_countdown_progress(self):
        if hasattr(self, 'current_reminder_interval') and self.current_reminder_interval > 0 and \
           hasattr(self, 'reminder_monotonic_start'):
            elapsed = time.monotonic() - self.reminder_monotonic_start
            progress = elapsed / self.current_reminder_interval
            return min(max(progress, 0.0), 1.0)
        return 0.0

    def update_timer(self):
        now = datetime.now()
        last_log_date_str = self.settings_manager.get('last_log_date')
        try:
            last_date = datetime.fromisoformat(last_log_date_str).date()
        except Exception:
            last_date = now.date()
        if last_date < now.date():
            self.perform_daily_reset()

        if hasattr(self, 'current_reminder_interval') and hasattr(self, 'reminder_monotonic_start'):
            elapsed = time.monotonic() - self.reminder_monotonic_start
            remaining = self.current_reminder_interval - elapsed
            if remaining < 0:
                time_str = "00:00"
            else:
                minutes, seconds = divmod(int(remaining), 60)
                time_str = f"{minutes:02d}:{seconds:02d}"
            self.countdown_label.setText(time_str)
        else:
            self.countdown_label.setText("--:--")
        self.update_progress_ring()

    def schedule_reminder(self):
        interval_minutes = random.randint(self.min_hydration_interval, self.max_hydration_interval)
        self.current_reminder_interval = interval_minutes * 60  # seconds
        self.reminder_monotonic_start = time.monotonic()
        self.next_reminder_time = datetime.now() + timedelta(seconds=self.current_reminder_interval)
        print(f"Next reminder scheduled in {interval_minutes} minutes at {self.next_reminder_time}")
        self.reminder_timer.start(self.current_reminder_interval * 1000)
    
    def show_reminder(self):
        print("Showing reminder!")

        if hasattr(self, 'current_reminder') and self.current_reminder:
            self.current_reminder.close()

        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.showMessage("Time to Hydrate!", "Your body needs water! ✨",
                                       QSystemTrayIcon.Information, 10000)

        theme = MODERN_COLORS.get(self.theme_name.lower())
        if not theme:
            theme = MODERN_COLORS.get("dark v2")
        
        notification_style = self.settings_manager.get('notification_style')
        if notification_style == "Legacy":
            from dialogs.reminder_dialog import LegacyReminderDialog
            self.current_reminder = LegacyReminderDialog(width=400, height=150, theme=theme)
        elif notification_style == "Over the Top":
            from dialogs.reminder_dialog import OverTheTopReminderDialog
            self.current_reminder = OverTheTopReminderDialog(width=460, height=240, theme=theme)
        else:
            from dialogs.reminder_dialog import ReminderDialog
            self.current_reminder = ReminderDialog(width=420, height=220, theme=theme)

        self.current_reminder.drink_button.clicked.connect(lambda: self._handle_drink(self.current_reminder))
        self.current_reminder.snooze_button.clicked.connect(lambda: self._handle_snooze(self.current_reminder))

        from PyQt5.QtGui import QGuiApplication
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        dialog_width = self.current_reminder.width()
        dialog_height = self.current_reminder.height()
        x = screen_geometry.center().x() - dialog_width // 2
        y = screen_geometry.bottom() - dialog_height - 40
        self.current_reminder.move(x, y)

        self.current_reminder.show()
        
        if self.sound_enabled:
            try:
                sound_path = resource_path(self.sound_file)
                if not os.path.exists(sound_path):
                    raise FileNotFoundError(f"Sound file not found: {sound_path}")
                self.sound_effect.setSource(QUrl.fromLocalFile(sound_path))
                self.sound_effect.play()
            except Exception as e:
                print(f"Error playing sound: {e}")
        
        self.schedule_reminder()

    def _handle_drink(self, dialog):
        dialog.close()
        self.log_drink()

    def _handle_snooze(self, dialog):
        dialog.close()
        self.snooze_reminder()

    def snooze_reminder(self):
        self.reminder_timer.stop()
        self.current_reminder_interval = self.snooze_duration * 60  # seconds
        self.reminder_monotonic_start = time.monotonic()
        self.next_reminder_time = datetime.now() + timedelta(seconds=self.current_reminder_interval)
        self.reminder_timer.start(self.current_reminder_interval * 1000)
        self.show_message("Reminder snoozed! I'll remind you again later. 💤")

    def classroom_mode(self):
        self.reminder_timer.stop()
        sleeping_time_ms = 90 * 60 * 1000
        self.current_reminder_interval = sleeping_time_ms / 1000
        self.next_reminder_time = datetime.now() + timedelta(milliseconds=sleeping_time_ms)
        self.reminder_timer.start(sleeping_time_ms)
        self.show_message("Classroom mode activated! I'll be quiet for 90 minutes. 📚")

    def open_love_timer(self):
        print("Opening love timer...")
        if not hasattr(self, 'love_timer') or self.love_timer is None:
            print("Creating new LoveTimer instance")
            self.love_timer = LoveTimer(self)
            def setup_callbacks():
                self.love_timer.fade_out_finished = self.on_love_timer_hidden
            QTimer.singleShot(100, setup_callbacks)
            self.love_timer.show()
            return
        if not self.love_timer.isVisible():
            print("Timer exists but is hidden, showing it again")
            QTimer.singleShot(50, self.love_timer.show_widget)
            return
        print("Timer is already visible")
        self.love_timer.raise_()
        self.love_timer.activateWindow()

    def on_love_timer_hidden(self):
        print("LoveTimer is now hidden but still exists in memory")
            
    def open_todo_list(self):
        if not hasattr(self, 'todo_list') or self.todo_list is None:
            self.todo_list = TodoListWidget(theme=self.theme_name)
            self.todo_list.setWindowTitle("To-Do List")
            self.todo_list.setWindowFlags(Qt.Window)
        self.todo_list.show()

    def open_water_level(self):
        print("Opening water level widget...")
        if not hasattr(self, 'water_level') or self.water_level is None:
            print("Creating new WaterLevelWidget instance")
            self.water_level = WaterLevelWidget(parent=self, settings_path=self.settings_manager.settings_path)
            def setup_callbacks():
                self.water_level.fade_out_finished = self.on_water_level_hidden
            QTimer.singleShot(100, setup_callbacks)
            self.water_level.show()
            return
        if not self.water_level.isVisible():
            print("Widget exists but is hidden, showing it again")
            self.water_level.show()
            return
        print("Widget is already visible")
        self.water_level.raise_()
        self.water_level.activateWindow()

    def on_water_level_hidden(self):
        print("WaterLevelWidget is now hidden but still exists in memory")
    
    def show_context_menu(self):
        theme = MODERN_COLORS.get(self.theme_name.lower(), MODERN_COLORS.get("dark v2"))
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {theme['surface'] if 'surface' in theme else theme['background']};
                color: {theme['text']};
                border: 1px solid {theme['border']}50;
                border-radius: 12px;
                padding: 8px 4px;
            }}
            QMenu::item {{
                padding: 10px 28px;
                border-radius: 6px;
                margin: 2px 8px;
            }}
            QMenu::item:selected {{
                background-color: {theme['primary']}40;
                color: {theme['primary']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {theme['border']}30;
                margin: 6px 12px;
            }}
        """)

        history_action = self.create_menu_action("History", "View your hydration history", self.show_history)
        settings_action = self.create_menu_action("Settings", "Customize your experience", self.show_settings)
        menu.addAction(history_action)
        menu.addAction(settings_action)
        menu.addSeparator()
        
        timer_action = self.create_menu_action("Forever Clock", "Show countdown timer", self.open_love_timer)
        todo_action = self.create_menu_action("To-Do List", "Manage your tasks", self.open_todo_list)
        water_level_action = self.create_menu_action("Water Level", "Track hydration levels", self.open_water_level)
        menu.addAction(timer_action)
        menu.addAction(water_level_action)
        menu.addAction(todo_action)
        menu.addSeparator()
        
        classroom_action = self.create_menu_action("Classroom Mode", "Pause reminders for 90 minutes", self.classroom_mode)
        '''
        achievements_action = self.create_menu_action("Achievements", "View your progress", 
                                                      self.show_profile_page if hasattr(self, 'show_profile_page') 
                                                      else 
                                                        lambda: self.show_message("You are amazing! More achievements coming soon! 💖"))
        '''
        achievements_action = self.create_menu_action("Achievements", 
                                                      "View your progress", 
                                                      self.show_profile_page
                                                      )
        help_action = self.create_menu_action("Help", "Get assistance", 
                                               lambda: self.show_message("Need help? Contact your Future Husband 💌"))
        menu.addAction(classroom_action)
        menu.addAction(achievements_action)
        menu.addAction(help_action)
        
        from PyQt5.QtCore import QPoint
        menu.exec_(self.menu_btn.mapToGlobal(QPoint(0, self.menu_btn.height())))

    def create_menu_action(self, text, tooltip, callback):
        action = QAction(text, self)
        action.setToolTip(tooltip)
        action.triggered.connect(callback)
        return action

    def reload_settings(self):
        self.min_hydration_interval = self.settings_manager.get('min_minutes')
        self.max_hydration_interval = self.settings_manager.get('max_minutes')
        self.snooze_duration = self.settings_manager.get('snooze_minutes')
        self.daily_hydration_goal = self.settings_manager.get('daily_goal')
        self.sound_enabled = self.settings_manager.get('sound_enabled')
        self.sound_file = self.settings_manager.get('sound_choice')
        self.hydration_log_count = self.settings_manager.get('log_count')
        self.theme_name = self.settings_manager.get('theme')
        self.show_progress_text = self.settings_manager.get('show_progress_text')
            
        self.apply_theme()
        
        self.update_progress_ring()
            
        self.reminder_timer.stop()
        self.schedule_reminder()

    def show_history(self):
        self.history_window = HistoryWindow(self)
        self.history_window.setWindowModality(Qt.NonModal)
        self.history_window.show()

    def show_settings(self):
        self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.setWindowModality(Qt.NonModal)
        self.settings_dialog.show()
        self.settings_dialog.finished.connect(self.reload_settings)

    # --- Updated animate_log method ---
    def animate_log(self):
        # Ensure we have the original position stored
        if not hasattr(self, 'initial_progress_ring_pos'):
            self.initial_progress_ring_pos = self.progress_ring.pos()
        
        # If an animation is already running, stop it and reset the position.
        if self.wave_animation.state() == QAbstractAnimation.Running:
            self.wave_animation.stop()
            self.progress_ring.move(self.initial_progress_ring_pos)
        
        bounce_height = 15
        start_pos = self.initial_progress_ring_pos
        end_pos = start_pos - QPoint(0, bounce_height)
        
        # Disconnect any previously connected finished signal to avoid accumulating callbacks.
        try:
            self.wave_animation.finished.disconnect()
        except Exception:
            pass
        self.wave_animation.setStartValue(start_pos)
        self.wave_animation.setEndValue(end_pos)
        self.wave_animation.finished.connect(lambda: self.progress_ring.move(start_pos))
        self.wave_animation.start()

    def log_drink(self):
        self.animate_log()
        self.hydration_log_count = min(self.hydration_log_count + 1, self.daily_hydration_goal)
        
        # Save before updating achievements so the current count is in settings
        self.save_settings()
        
        # Update achievements after logging a drink
        if hasattr(self, 'profile_system'):
            self.profile_system.update_achievements()
        
        self.update_progress_ring()
        self.show_message(random.choice(self.motivational_quotes))
        self.history_updated.emit()

    def show_message(self, text):
        if hasattr(self, "_current_toast") and self._current_toast:
            self._current_toast.close()
            self._current_toast = None

        toast = ToastLabel(f"💞 {text} 💞")
        toast.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        toast.adjustSize()

        from PyQt5.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().availableGeometry()
        x = screen.center().x() - toast.width() // 2
        y = screen.bottom() - toast.height() - 60

        toast.move(x, y + 40)
        toast.setWindowOpacity(0.0)

        entrance_group = QParallelAnimationGroup(toast)
        
        slide_anim = QPropertyAnimation(toast, b"pos")
        slide_anim.setDuration(400)
        slide_anim.setStartValue(toast.pos())
        slide_anim.setEndValue(QPoint(x, y))
        slide_anim.setEasingCurve(QEasingCurve.OutBack)
        
        fade_anim = QPropertyAnimation(toast, b"windowOpacity")
        fade_anim.setDuration(300)
        fade_anim.setStartValue(0.0)
        fade_anim.setEndValue(1.0)
        
        entrance_group.addAnimation(slide_anim)
        entrance_group.addAnimation(fade_anim)

        toast.show()
        entrance_group.start()

        self._current_toast = toast

        QTimer.singleShot(8000, lambda: self.fade_out_toast(toast))

    def fade_out_toast(self, toast):
        exit_group = QParallelAnimationGroup(toast)

        slide_anim = QPropertyAnimation(toast, b"pos")
        slide_anim.setDuration(800)
        slide_anim.setStartValue(toast.pos())
        slide_anim.setEndValue(toast.pos() + QPoint(0, 20))
        slide_anim.setEasingCurve(QEasingCurve.InSine)
        
        fade_anim = QPropertyAnimation(toast, b"windowOpacity")
        fade_anim.setDuration(800)
        fade_anim.setStartValue(1.0)
        fade_anim.setEndValue(0.0)
        fade_anim.setEasingCurve(QEasingCurve.InQuint)
        
        exit_group.addAnimation(slide_anim)
        exit_group.addAnimation(fade_anim)
        exit_group.finished.connect(lambda: self._hide_toast(toast))
        exit_group.start()

    def _hide_toast(self, toast):
        toast.close()
        if hasattr(self, "_current_toast") and self._current_toast == toast:
            self._current_toast = None

    def save_settings(self):
        self.settings_manager.set('min_minutes', self.min_hydration_interval)
        self.settings_manager.set('max_minutes', self.max_hydration_interval)
        self.settings_manager.set('snooze_minutes', self.snooze_duration)
        self.settings_manager.set('daily_goal', self.daily_hydration_goal)
        self.settings_manager.set('sound_enabled', self.sound_enabled)
        self.settings_manager.set('sound_choice', self.sound_file)
        self.settings_manager.set('log_count', self.hydration_log_count)
        self.settings_manager.set('theme', self.theme_name)
        self.settings_manager.set('show_progress_text', self.show_progress_text)
        self.settings_manager.update_last_log_date()
        
        # Get log_times without default value
        log_times = self.settings_manager.get('log_times')
        # Initialize if None
        if log_times is None:
            log_times = []
        
        # Add current time
        log_times.append(datetime.now().isoformat())
        
        # Keep only the most recent 100 timestamps to avoid growing too large
        if len(log_times) > 100:
            log_times = log_times[-100:]
        
        self.settings_manager.set('log_times', log_times)
        self.settings_manager.save_settings()

    def check_daily_reset(self):
        today = datetime.now().date()
        last_log_date_str = self.settings_manager.get('last_log_date')
        try:
            last_date = datetime.fromisoformat(last_log_date_str).date()
        except Exception:
            last_date = today
        if last_date < today:
            if self.hydration_log_count > 0:
                history = self.settings_manager.get('history')
                history[last_date.isoformat()] = self.hydration_log_count
                self.settings_manager.set('history', history)
            self.hydration_log_count = 0
            self.settings_manager.set('last_log_date', datetime.now().isoformat())
            self.save_settings()
            
            # Check for new achievements after daily reset
            if hasattr(self, 'profile_system'):
                self.profile_system.update_achievements()

    def schedule_daily_reset(self):
        now = datetime.now()
        tomorrow = now.date() + timedelta(days=1)
        midnight = datetime.combine(tomorrow, datetime.min.time())
        seconds_until_midnight = (midnight - now).total_seconds()
        msecs_until_midnight = int(seconds_until_midnight * 1000)
        
        self.daily_reset_timer = QTimer(self)
        self.daily_reset_timer.setSingleShot(True)
        self.daily_reset_timer.timeout.connect(self.perform_daily_reset)
        self.daily_reset_timer.start(msecs_until_midnight)
        print(f"Daily reset scheduled in {seconds_until_midnight:.0f} seconds.")

    def perform_daily_reset(self):
        self.check_daily_reset()
        self.schedule_daily_reset()

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon = QIcon(resource_path("assets/icons/icon.png"))
        self.tray_icon.setIcon(icon)
        
        tray_menu = QMenu()
        theme = MODERN_COLORS.get(self.theme_name.lower(), MODERN_COLORS.get("dark v2"))
        tray_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {theme['surface'] if 'surface' in theme else theme['background']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                border-radius: 8px;
                padding: 6px 2px;
            }}
            QMenu::item {{
                padding: 8px 24px;
                border-radius: 4px;
                margin: 2px 6px;
            }}
            QMenu::item:selected {{
                background-color: {theme['primary']}40;
                color: {theme['primary']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {theme['border']}30;
                margin: 4px 8px;
            }}
        """)
        
        show_action = QAction("Open Bea Apă", self)
        show_action.triggered.connect(self.show)
        show_action.setIcon(QIcon(resource_path("assets/icons/icon.png")))
        tray_menu.addAction(show_action)
        
        log_action = QAction("Log Drink", self)
        log_action.triggered.connect(self.log_drink)
        log_action.setIcon(QIcon(resource_path("assets/icons/plus.svg")))
        tray_menu.addAction(log_action)
        
        tray_menu.addSeparator()
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        tray_menu.addAction(settings_action)
        
        classroom_action = QAction("Classroom Mode", self)
        classroom_action.triggered.connect(self.classroom_mode)
        classroom_action.setToolTip("Pause reminders for 90 minutes")
        tray_menu.addAction(classroom_action)
        
        tray_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        self.tray_icon.showMessage(
            "Bea Apă is running", 
            "I'll remind you to stay hydrated! 💧", 
            QSystemTrayIcon.Information, 
            3000
        )
        

    def exit_app(self):
        self.exit_on_close = True
        self.close()

    def closeEvent(self, event: QCloseEvent):
        if self.exit_on_close:
            event.accept()
        else:
            self.hide()
            self.tray_icon.showMessage(
                "Bea Apă is still running", 
                "The app will continue to remind you to drink water. Right-click the tray icon for options.",
                QSystemTrayIcon.Information,
                3000
            )
            event.ignore()
