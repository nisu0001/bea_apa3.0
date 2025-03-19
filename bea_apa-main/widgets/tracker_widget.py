import sys
import random
import json
import os
from datetime import datetime, timedelta
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF, QPropertyAnimation, QVariantAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QLinearGradient, QFont, QPen, QPainterPath, QBrush, QIcon, QFontDatabase
from PyQt5.QtWidgets import (QApplication, QLabel, QWidget, QVBoxLayout, QMenu, 
                             QGraphicsDropShadowEffect, QHBoxLayout, QPushButton, 
                             QDesktopWidget, QSizePolicy)
from utils import resource_path

class WaterLevelWidget(QWidget):
    def __init__(self, parent=None, settings_path="settings.json"):
        super().__init__(parent)
        self.settings_path = settings_path
        self.days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        self.animation_progress = 0
        self.bar_animations = []
        self.percentage_animation = None
        
        self.percentage = 0
        self.animated_percentage = 0
        self.old_percentage = 0
        
        # --- Set color palette ---
        # For an Apple-like design on macOS, we use a light background with dark text.
        # Otherwise, we retain the darker theme.
        if sys.platform == "darwin":
            self.bg_color = QColor(245, 245, 245)
            self.accent_color = QColor(0, 122, 255)
            self.secondary_accent = QColor(0, 122, 255).lighter(110)
            self.bar_color = QColor(0, 0, 0, 180)
            self.text_color = QColor(20, 20, 20)
            self.muted_text_color = QColor(120, 120, 120)
            self.highlight_color = QColor(20, 20, 20)
        else:
            self.bg_color = QColor(40, 40, 45)
            self.accent_color = QColor(0, 122, 255)
            self.secondary_accent = QColor(88, 86, 214)
            self.bar_color = QColor(255, 255, 255, 180)
            self.text_color = QColor(255, 255, 255)
            self.muted_text_color = QColor(180, 180, 180)
            self.highlight_color = QColor(255, 255, 255)
        
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WA_NoSystemBackground, False)
        
        self.load_fonts()
        self.load_settings()
        self.load_hydration_data()
        self.update_stats()
        
        self.setMinimumSize(270, 140)
        self.setMaximumSize(270, 140)
        
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        
        if sys.platform == 'win32':
            self.setStyleSheet("background-color: rgba(40, 40, 45, 255);")
        else:
            self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.apply_shadow()
        self.create_add_button()
        
        try:
            self.icon_path = resource_path(os.path.join("assets", "icons", "icon.png"))
        except Exception as e:
            self.icon_path = None
        
        self.calculate_layout()
        self.setup_timers()
        
        self.dragging = False
        self.offset = None
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.position_widget()
        self.setToolTip("Drag to move. Right-click for menu. Double-click to hide.")
        
        # Connect parent's history_updated signal if available.
        if self.parent() is not None and hasattr(self.parent(), 'history_updated'):
            self.parent().history_updated.connect(self.refresh_data)
        
        self.animate_bars()
    
    def load_fonts(self):
        self.title_font = QFont("SF Pro Display", 11, QFont.DemiBold)
        self.day_font = QFont("SF Pro Text", 9)
        self.stats_font = QFont("SF Pro Display", 18, QFont.Bold)
        self.small_stats_font = QFont("SF Pro Text", 10)
        
        font_db = QFontDatabase()
        font_families = list(font_db.families())
        
        if "SF Pro Display" not in font_families and "SF Pro Text" not in font_families:
            if sys.platform == "darwin":
                self.title_font = QFont(".AppleSystemUIFont", 11, QFont.DemiBold)
                self.day_font = QFont(".AppleSystemUIFont", 9)
                self.stats_font = QFont(".AppleSystemUIFont", 18, QFont.Bold)
                self.small_stats_font = QFont(".AppleSystemUIFont", 10)
            elif sys.platform == "win32":
                self.title_font = QFont("Segoe UI", 11, QFont.DemiBold)
                self.day_font = QFont("Segoe UI", 9)
                self.stats_font = QFont("Segoe UI", 18, QFont.Bold)
                self.small_stats_font = QFont("Segoe UI", 10)
            else:
                self.title_font = QFont("Ubuntu", 11, QFont.DemiBold)
                self.day_font = QFont("Ubuntu", 9)
                self.stats_font = QFont("Ubuntu", 18, QFont.Bold)
                self.small_stats_font = QFont("Ubuntu", 10)
    
    def apply_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
    
    def create_add_button(self):
        self.add_button = QPushButton("+", self)
        self.add_button.setFixedSize(22, 22)
        # Use refined styling on macOS
        if sys.platform == "darwin":
            self.add_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.accent_color.name()};
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                    border-radius: 11px;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {self.accent_color.lighter(120).name()};
                }}
                QPushButton:pressed {{
                    background-color: {self.accent_color.darker(110).name()};
                }}
            """)
        else:
            self.add_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.accent_color.name()};
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                    border-radius: 11px;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: #1a86ff;
                }}
                QPushButton:pressed {{
                    background-color: #0062cc;
                }}
            """)
        self.add_button.clicked.connect(self.log_drink)
        self.add_button.setCursor(Qt.PointingHandCursor)
    
    def calculate_layout(self):
        width = self.width()
        height = self.height()
        
        self.layout = {}
        self.layout['title_rect'] = QRectF(16, 12, width - 50, 25)
        self.layout['add_button_pos'] = QPointF(width - 28, 12)
        
        chart_width = width * 0.65
        chart_left = 16
        chart_top = height * 0.35
        chart_bottom = height * 0.85
        chart_height = chart_bottom - chart_top
        
        self.layout['chart'] = {
            'width': chart_width,
            'left': chart_left,
            'top': chart_top,
            'bottom': chart_bottom,
            'height': chart_height,
            'separator_x': chart_width + 16
        }
        
        bar_width = (chart_width - 16) / 7 * 0.7
        bar_spacing = (chart_width - 16) / 7 - bar_width
        
        self.layout['bars'] = {
            'width': bar_width,
            'spacing': bar_spacing
        }
        
        stats_x = chart_width + 32
        stats_width = width - stats_x - 16
        
        self.layout['stats'] = {
            'x': stats_x,
            'width': stats_width,
            'counter_rect': QRectF(stats_x, height * 0.4, stats_width, 30),
            'label_rect': QRectF(stats_x, height * 0.4 + 30, stats_width, 20),
            'arc_center_x': stats_x + stats_width / 2,
            'arc_center_y': height * 0.7,
            'arc_radius': 16,
            'percent_rect': QRectF(stats_x + stats_width / 2 - 40, height * 0.7 + 16 + 5, 80, 20)
        }
        
        self.add_button.move(int(self.layout['add_button_pos'].x()), int(self.layout['add_button_pos'].y()))
    
    def setup_timers(self):
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(60000)
        
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animations)
        self.animation_timer.start(33)
    
    def position_widget(self):
        desktop = QDesktopWidget().availableGeometry()
        self.move(desktop.width() - self.width() - 20, desktop.height() - self.height() - 40)
    
    def load_settings(self):
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, "r") as f:
                    settings = json.load(f)
                self.target_drinks = settings.get("daily_goal", 8)
                if not isinstance(self.target_drinks, int) or self.target_drinks <= 0:
                    self.target_drinks = 8
                self.current_log_count = settings.get("log_count", 0)
                if not isinstance(self.current_log_count, int) or self.current_log_count < 0:
                    self.current_log_count = 0
                print(f"Loaded settings: target={self.target_drinks}, current={self.current_log_count}")
            else:
                self.target_drinks = 8
                self.current_log_count = 0
                print(f"Settings file not found: {self.settings_path}, using defaults")
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.target_drinks = 8
            self.current_log_count = 0
    
    def load_hydration_data(self):
        try:
            self.drink_data = [0] * 7
            self.bar_targets = [0] * 7
            
            if os.path.exists(self.settings_path):
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                history = settings.get("history", {})
                if not isinstance(history, dict):
                    print(f"Invalid history data format: {type(history)}, using defaults")
                    history = {}
                
                today = datetime.now().date()
                current_weekday = today.weekday()
                print(f"Current weekday: {current_weekday}, today: {today}")
                
                for i in range(7):
                    day_offset = i - current_weekday
                    date = today + timedelta(days=day_offset)
                    date_str = date.isoformat()
                    if date == today:
                        log_count = settings.get("log_count", 0)
                        if not isinstance(log_count, int):
                            log_count = 0
                        self.drink_data[i] = log_count
                    else:
                        history_count = history.get(date_str, 0)
                        if not isinstance(history_count, int):
                            history_count = 0
                        self.drink_data[i] = history_count
                    self.bar_targets[i] = self.drink_data[i]
                print(f"Loaded drink data: {self.drink_data}")
            else:
                print(f"Settings file not found: {self.settings_path}, using sample data")
                self.drink_data = [3, 4, 5, 4, 6, 5, 4]
                self.bar_targets = self.drink_data.copy()
        except Exception as e:
            print(f"Error loading hydration data: {e}")
            self.drink_data = [3, 4, 5, 4, 6, 5, 4]
            self.bar_targets = self.drink_data.copy()
        
        self.animated_values = self.drink_data.copy()
        self.old_percentage = getattr(self, 'percentage', 0)
    
    def update_stats(self):
        self.total_drinks = sum(self.drink_data)
        self.weekly_target = 7 * self.target_drinks
        
        today_index = datetime.now().weekday()
        today_drinks = self.drink_data[today_index] if 0 <= today_index < len(self.drink_data) else 0
        
        self.old_percentage = self.percentage
        if self.target_drinks > 0:
            self.percentage = min(100, int((today_drinks / self.target_drinks) * 100))
        else:
            self.percentage = 0
        
        if self.percentage_animation:
            self.percentage_animation.stop()
        self.animated_percentage = self.old_percentage
        
        self.percentage_animation = QVariantAnimation()
        self.percentage_animation.setStartValue(self.animated_percentage)
        self.percentage_animation.setEndValue(self.percentage)
        self.percentage_animation.setDuration(800)
        self.percentage_animation.setEasingCurve(QEasingCurve.OutQuart)
        self.percentage_animation.valueChanged.connect(lambda value: self._update_percentage(value))
        self.percentage_animation.start()
        
        print(f"Stats updated: today's drinks={today_drinks}, target={self.target_drinks}, percentage={self.percentage}%")
    
    def _update_percentage(self, value):
        self.animated_percentage = value
    
    def animate_bars(self):
        for anim in self.bar_animations:
            if anim is not None:
                anim.stop()
        self.bar_animations = []
        
        for i, target in enumerate(self.bar_targets):
            animation = QVariantAnimation()
            animation.setStartValue(self.animated_values[i])
            animation.setEndValue(float(target))
            animation.setDuration(800)
            animation.setEasingCurve(QEasingCurve.OutQuart)
            
            def create_update_function(idx):
                return lambda value: self._update_bar_value(idx, value)
            animation.valueChanged.connect(create_update_function(i))
            animation.start()
            self.bar_animations.append(animation)
    
    def _update_bar_value(self, idx, value):
        self.animated_values[idx] = value
        self.update()
    
    def update_animations(self):
        needs_update = any(anim and anim.state() == QVariantAnimation.Running for anim in self.bar_animations)
        if needs_update or (self.percentage_animation and self.percentage_animation.state() == QVariantAnimation.Running):
            self.update()
    
    def update_display(self):
        self.refresh_data()
    
    def refresh_data(self):
        old_values = self.drink_data.copy()
        old_animated_values = self.animated_values.copy()
        old_percentage = self.animated_percentage
        
        self.load_settings()
        self.load_hydration_data()
        self.update_stats()
        
        if old_values != self.drink_data:
            self.animated_values = old_animated_values
            self.animate_bars()
    
    def paintEvent(self, event):
        width = self.width()
        height = self.height()
        
        if not hasattr(self, 'layout'):
            self.calculate_layout()
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        rect = QRectF(0, 0, width, height)
        path = QPainterPath()
        path.addRoundedRect(rect, 16, 16)
        
        painter.setPen(Qt.NoPen)
        if sys.platform == 'win32':
            painter.setBrush(QBrush(self.bg_color))
            painter.drawRoundedRect(rect, 16, 16)
        else:
            # For macOS, use a subtle light gradient.
            gradient = QLinearGradient(0, 0, 0, height)
            if sys.platform == "darwin":
                gradient.setColorAt(0, self.bg_color.lighter(105))
                gradient.setColorAt(1, self.bg_color)
            else:
                gradient.setColorAt(0, self.bg_color.lighter(110))
                gradient.setColorAt(1, self.bg_color)
            painter.fillPath(path, gradient)
        
        # Draw the title.
        painter.setPen(self.text_color)
        painter.setFont(self.title_font)
        painter.drawText(self.layout['title_rect'], Qt.AlignLeft | Qt.AlignVCenter, "Water Level")
        
        # Draw chart area.
        chart_left = self.layout['chart']['left']
        chart_top = self.layout['chart']['top']
        chart_bottom = self.layout['chart']['bottom']
        chart_height = self.layout['chart']['height']
        chart_width = self.layout['chart']['width']
        
        # Separator line.
        painter.setPen(QPen(QColor(100, 100, 100, 40), 1))
        painter.drawLine(int(self.layout['chart']['separator_x']), 50, int(self.layout['chart']['separator_x']), height - 20)
        
        # Guide lines.
        painter.setPen(QPen(QColor(100, 100, 100, 20), 1, Qt.DashLine))
        for guide in [chart_top, chart_top + chart_height * 0.5, chart_bottom]:
            painter.drawLine(int(chart_left), int(guide), int(chart_left + chart_width - 16), int(guide))
        
        bar_width = self.layout['bars']['width']
        bar_spacing = self.layout['bars']['spacing']
        
        today_index = datetime.now().weekday()
        for i in range(7):
            x = chart_left + i * (bar_width + bar_spacing)
            max_bar_height = chart_height
            value = self.animated_values[i]
            fill_percentage = min(1.0, value / self.target_drinks) if self.target_drinks > 0 else 0
            bar_height = fill_percentage * max_bar_height
            
            bg_bar_rect = QRectF(x, chart_top, bar_width, max_bar_height)
            empty_gradient = QLinearGradient(0, chart_top, 0, chart_bottom)
            empty_gradient.setColorAt(0, QColor(100, 100, 100, 30))
            empty_gradient.setColorAt(1, QColor(80, 80, 80, 30))
            painter.setBrush(empty_gradient)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(bg_bar_rect, 3, 3)
            
            if bar_height > 0:
                fill_bar_rect = QRectF(x, chart_bottom - bar_height, bar_width, bar_height)
                fill_gradient = QLinearGradient(0, chart_bottom - bar_height, 0, chart_bottom)
                if i == today_index:
                    fill_gradient.setColorAt(0, self.accent_color.lighter(110))
                    fill_gradient.setColorAt(1, self.accent_color)
                else:
                    fill_gradient.setColorAt(0, self.secondary_accent.lighter(120))
                    fill_gradient.setColorAt(1, self.secondary_accent)
                painter.setBrush(fill_gradient)
                painter.drawRoundedRect(fill_bar_rect, 3, 3)
            
            painter.setPen(self.muted_text_color)
            painter.setFont(self.day_font)
            day_label_rect = QRectF(x - bar_spacing/4, chart_bottom + 5, bar_width + bar_spacing/2, 20)
            if i == today_index:
                painter.setPen(self.text_color)
            painter.drawText(day_label_rect, Qt.AlignCenter, self.days[i])
        
        # Draw stats (today's count and circular progress).
        stats = self.layout['stats']
        today_drinks = self.drink_data[today_index] if 0 <= today_index < len(self.drink_data) else 0
        drinks_text = f"{today_drinks}"
        
        painter.setPen(self.text_color)
        painter.setFont(self.stats_font)
        painter.drawText(stats['counter_rect'], Qt.AlignCenter, drinks_text)
        
        painter.setPen(self.muted_text_color)
        painter.setFont(self.small_stats_font)
        painter.drawText(stats['label_rect'], Qt.AlignCenter, f"of {self.target_drinks}")
        
        # Draw circular progress arc.
        arc_center_x = stats['arc_center_x']
        arc_center_y = stats['arc_center_y']
        arc_radius = stats['arc_radius']
        painter.setPen(QPen(QColor(100, 100, 100, 100), 3))
        painter.drawEllipse(int(arc_center_x - arc_radius), int(arc_center_y - arc_radius), 
                            int(arc_radius * 2), int(arc_radius * 2))
        painter.setPen(QPen(self.accent_color, 3))
        start_angle = 90 * 16
        span_angle = -int(3.6 * 16 * self.animated_percentage)
        painter.drawArc(int(arc_center_x - arc_radius), int(arc_center_y - arc_radius),
                        int(arc_radius * 2), int(arc_radius * 2), start_angle, span_angle)
        painter.setPen(self.text_color)
        painter.setFont(self.small_stats_font)
        percent_text = f"{int(self.animated_percentage)}%"
        painter.drawText(stats['percent_rect'], Qt.AlignCenter, percent_text)
    
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
    
    def mouseDoubleClickEvent(self, event):
        self.start_fade_out()
    
    def show_context_menu(self, position):
        menu = QMenu(self)
        # Use an Apple-like (light) context menu on macOS.
        if sys.platform == "darwin":
            menu.setStyleSheet("""
                QMenu {
                    background-color: #ffffff;
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    padding: 5px;
                    color: #000;
                }
                QMenu::item {
                    padding: 8px 25px;
                    border-radius: 5px;
                }
                QMenu::item:selected {
                    background-color: #e5f1fb;
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #ddd;
                    margin: 4px 10px;
                }
            """)
        else:
            menu.setStyleSheet("""
                QMenu {
                    background-color: #333333;
                    border-radius: 10px;
                    padding: 5px;
                    color: white;
                }
                QMenu::item {
                    padding: 8px 25px;
                    border-radius: 5px;
                }
                QMenu::item:selected {
                    background-color: #0a84ff;
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #444444;
                    margin: 4px 10px;
                }
            """)
        
        refresh_action = menu.addAction("Refresh Data")
        menu.addSeparator()
        reset_action = menu.addAction("Reset Today's Count")
        menu.addSeparator()
        hide_action = menu.addAction("Hide Widget")
        
        action = menu.exec_(self.mapToGlobal(position))
        if action == hide_action:
            self.start_fade_out()
        elif action == refresh_action:
            self.refresh_data()
        elif action == reset_action:
            self.reset_today()
    
    def reset_today(self):
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, "r") as f:
                    settings = json.load(f)
                settings["log_count"] = 0
                with open(self.settings_path, "w") as f:
                    json.dump(settings, f, indent=4)
                self.refresh_data()
        except Exception as e:
            print(f"Error resetting count: {e}")
    
    def log_drink(self):
        # Delegate to parent's log_drink if available.
        if self.parent() is not None and hasattr(self.parent(), 'log_drink'):
            self.parent().log_drink()
            self.refresh_data()
            return
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, "r") as f:
                    settings = json.load(f)
                current_count = settings.get("log_count", 0)
                new_count = min(current_count + 1, settings.get("daily_goal", 15))
                settings["log_count"] = new_count
                settings["last_log_date"] = datetime.now().isoformat()
                with open(self.settings_path, "w") as f:
                    json.dump(settings, f, indent=4)
                today_index = datetime.now().weekday()
                self.drink_data[today_index] = new_count
                old_value = self.animated_values[today_index]
                self.bar_targets[today_index] = new_count
                self.update_stats()
                if self.bar_animations and len(self.bar_animations) > today_index:
                    if self.bar_animations[today_index]:
                        self.bar_animations[today_index].stop()
                animation = QVariantAnimation()
                animation.setStartValue(old_value)
                animation.setEndValue(float(new_count))
                animation.setDuration(600)
                animation.setEasingCurve(QEasingCurve.OutQuad)
                animation.valueChanged.connect(lambda value, idx=today_index: self._update_bar_value(idx, value))
                animation.start()
                while len(self.bar_animations) <= today_index:
                    self.bar_animations.append(None)
                self.bar_animations[today_index] = animation
                old_percentage = self.animated_percentage
                new_percentage = min(100, int((new_count / self.target_drinks) * 100)) if self.target_drinks > 0 else 0
                if self.percentage_animation:
                    self.percentage_animation.stop()
                self.percentage_animation = QVariantAnimation()
                self.percentage_animation.setStartValue(old_percentage)
                self.percentage_animation.setEndValue(new_percentage)
                self.percentage_animation.setDuration(600)
                self.percentage_animation.setEasingCurve(QEasingCurve.OutQuad)
                self.percentage_animation.valueChanged.connect(lambda value: self._update_percentage(value))
                self.percentage_animation.start()
        except Exception as e:
            print(f"Error logging drink: {e}")
            self.refresh_data()
    
    def start_fade_out(self):
        print("WaterLevelWidget starting fade out")
        if sys.platform == 'win32':
            self.hide_widget()
            return
        self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.OutQuad)
        self.fade_out_animation.finished.connect(self.hide_widget)
        self.fade_out_animation.start()
    
    def hide_widget(self):
        print("WaterLevelWidget hide_widget called")
        self.hide()
        if hasattr(self, 'fade_out_finished') and callable(self.fade_out_finished):
            self.fade_out_finished()
