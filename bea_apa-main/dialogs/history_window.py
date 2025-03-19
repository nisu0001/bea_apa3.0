# dialogs/history_window.py

import calendar
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QFrame, QSizePolicy, QComboBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon

from config import MODERN_COLORS  

class HistoryWindow(QDialog):
    """
    Enhanced history visualization window with multiple view options.
    
    Features:
    - Weekly, monthly, and yearly visualizations
    - Modern styling with theme support
    - Interactive charts
    - Statistics and insights
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        self.main_app = parent
        
        # Get theme colors
        self.theme_name = self.main_app.theme_name.lower()
        self.theme = MODERN_COLORS.get(self.theme_name, MODERN_COLORS.get("dark v2"))
        
        # Setup window properties
        self.setWindowTitle("Hydration History")
        self.setMinimumSize(700, 600)
        self.apply_theme()
        
        # Initial view
        self.current_view = "week"
        
        # Create UI
        self.init_ui()
        
        # Connect signals
        if hasattr(self.main_app, 'history_updated'):
            self.main_app.history_updated.connect(self.plot_history)

    def apply_theme(self):
        """Apply theme colors to the window"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.theme['background']};
                color: {self.theme['text']};
                font-family: 'Segoe UI', sans-serif;
            }}
            
            QLabel {{
                color: {self.theme['text']};
            }}
            
            QLabel#title {{
                font-size: 24px;
                font-weight: bold;
            }}
            
            QLabel#subtitle {{
                font-size: 16px;
                color: {self.theme['text']}B0;
            }}
            
            QFrame#statCard {{
                background-color: {self.theme['surface']};
                border-radius: 12px;
                padding: 16px;
            }}
            
            QLabel#statValue {{
                font-size: 24px;
                font-weight: bold;
                color: {self.theme['primary']};
            }}
            
            QLabel#statLabel {{
                font-size: 14px;
                color: {self.theme['text']}B0;
                background-color: transparent;
            }}
            
            QPushButton {{
                background-color: {self.theme['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
            }}
            
            QPushButton:checked {{
                background-color: {self.theme['secondary']};
            }}
            
            QPushButton:hover:!checked {{
                background-color: {self.theme['primary']}D0;
            }}
            
            QComboBox {{
                background-color: {self.theme['surface']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 120px;
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {self.theme['surface']};
                selection-background-color: {self.theme['primary']};
                selection-color: white;
                border: 1px solid {self.theme['border']};
            }}
        """)

    def init_ui(self):
        """Initialize UI components"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header section
        header_layout = QVBoxLayout()
        
        # Title and subtitle
        title_label = QLabel("Hydration History")
        title_label.setObjectName("title")
        
        subtitle_label = QLabel("Track your hydration patterns over time")
        subtitle_label.setObjectName("subtitle")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        
        layout.addLayout(header_layout)
        
        # Stats section
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        
        # Create stat cards
        self.total_card = self.create_stat_card("Total Drinks", "0")
        self.avg_card = self.create_stat_card("Daily Average", "0")
        self.streak_card = self.create_stat_card("Best Streak", "0 days")
        
        stats_layout.addWidget(self.total_card)
        stats_layout.addWidget(self.avg_card)
        stats_layout.addWidget(self.streak_card)
        
        layout.addLayout(stats_layout)
        
        # View control section
        controls_layout = QHBoxLayout()
        
        # View selector
        view_layout = QHBoxLayout()
        view_label = QLabel("View:")
        
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Week", "Month", "Year"])
        self.view_combo.setCurrentText("Week")
        self.view_combo.currentTextChanged.connect(self.change_view)
        
        view_layout.addWidget(view_label)
        view_layout.addWidget(self.view_combo)
        view_layout.addStretch()
        
        controls_layout.addLayout(view_layout)
        
        layout.addLayout(controls_layout)
        
        # Chart section
        self.figure, self.ax = plt.subplots(figsize=(8, 5), dpi=100)
        self.figure.patch.set_facecolor(self.theme['background'])
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout.addWidget(self.canvas, 1)
        
        # Store secondary axis reference
        self.ax2 = None
        
        # Initial plot
        self.plot_history()

    def create_stat_card(self, label, value):
        """Create a statistic display card"""
        card = QFrame()
        card.setObjectName("statCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        
        # Stat value (large, prominent)
        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        value_label.setAlignment(Qt.AlignCenter)
        
        # Stat label (smaller, below)
        description = QLabel(label)
        description.setObjectName("statLabel")
        description.setAlignment(Qt.AlignCenter)
        
        # Add to layout
        layout.addWidget(value_label)
        layout.addWidget(description)
        
        # Store reference to value label for updates
        card.value_label = value_label
        
        return card
        
    def change_view(self, view):
        """Handle view change from combobox"""
        view = view.lower()
        if view in ["week", "month", "year"]:
            self.current_view = view
            self.plot_history()
            
    def plot_history(self):
        """Plot hydration history based on current view"""
        view = self.current_view
        today = datetime.now().date()
        
        # Get history from settings with empty dict fallback
        history = self.main_app.settings_manager.get("history") or {}
        
        # Include today's data
        today_str = today.isoformat()
        history[today_str] = self.main_app.hydration_log_count
        
        # Convert history data from ISO strings to (date, count) tuples
        data = []
        for date_str, count in history.items():
            try:
                d = datetime.fromisoformat(date_str).date()
                data.append((d, count))
            except Exception:
                continue
                
        # Sort by date
        data.sort(key=lambda x: x[0])
        
        # Calculate statistics
        self.calculate_statistics(data)
        
        # Clear previous plot
        self.ax.clear()
        
        # Remove secondary axis if it exists
        if self.ax2 is not None:
            self.ax2.remove()
            self.ax2 = None
        
        # Get theme colors for plot
        theme_color = self.theme['primary']
        background_color = self.theme['background']
        text_color = self.theme['text']
        accent_color = self.theme['accent']
        secondary_color = self.theme['secondary']
        
        # Configure general plot styling
        self.ax.set_facecolor(background_color)
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        
        self.ax.tick_params(axis='x', colors=text_color, length=5, width=1)
        self.ax.tick_params(axis='y', colors=text_color, length=5, width=1)
        self.ax.grid(axis='y', linestyle='--', alpha=0.2, color=text_color)
        
        # Font settings
        title_font = {'color': text_color, 'fontweight': 'bold', 'fontsize': 14}
        axis_font = {'color': text_color, 'fontsize': 10}
        
        # Plot based on selected view
        if view == "week":
            self.plot_weekly_data(data, today, theme_color, text_color, accent_color, title_font, axis_font)
        elif view == "month":
            self.plot_monthly_data(data, today, theme_color, text_color, accent_color, title_font, axis_font)
        elif view == "year":
            self.plot_yearly_data(data, today, theme_color, secondary_color, text_color, title_font, axis_font)
            
        # Final plot adjustments
        self.figure.tight_layout()
        self.canvas.draw()
        
    def calculate_statistics(self, data):
        """Calculate and update statistics from history data"""
        if not data:
            # Update stats cards with zeros
            self.total_card.value_label.setText("0")
            self.avg_card.value_label.setText("0.0")
            self.streak_card.value_label.setText("0 days")
            return
            
        # Total drinks
        total_drinks = sum(count for _, count in data)
        self.total_card.value_label.setText(str(total_drinks))
        
        # Daily average (only count days with data)
        days_with_data = sum(1 for _, count in data if count > 0)
        avg = total_drinks / max(days_with_data, 1)
        self.avg_card.value_label.setText(f"{avg:.1f}")
        
        # Find best streak
        dates = sorted(d for d, count in data if count > 0)
        if not dates:
            self.streak_card.value_label.setText("0 days")
            return
            
        # Calculate streaks
        max_streak = 1
        current_streak = 1
        
        for i in range(1, len(dates)):
            if (dates[i] - dates[i-1]).days == 1:
                current_streak += 1
            else:
                current_streak = 1
                
            max_streak = max(max_streak, current_streak)
        
        # Format streak text
        streak_text = f"{max_streak} day{'s' if max_streak != 1 else ''}"
        self.streak_card.value_label.setText(streak_text)
        
    def plot_weekly_data(self, data, today, theme_color, text_color, accent_color, title_font, axis_font):
        """Plot weekly view of hydration data"""
        # Define the week (last 7 days)
        start_date = today - timedelta(days=6)
        date_range = [start_date + timedelta(days=i) for i in range(7)]
        
        # Filter data for the week
        weekly_data = {}
        for date in date_range:
            weekly_data[date] = 0
            
        for d, count in data:
            if d in date_range:
                weekly_data[d] = count
                
        # Prepare plot data
        dates = list(weekly_data.keys())
        counts = list(weekly_data.values())
        
        # Create gradient bars
        colors = []
        for d in dates:
            if d == today:
                colors.append(theme_color)
            else:
                colors.append(f"{theme_color}A0")  # Semi-transparent
        
        # Plot bars
        bars = self.ax.bar(dates, counts, width=0.7, color=colors, edgecolor=theme_color, linewidth=1)
        
        # Add goal line
        goal = self.main_app.daily_hydration_goal
        self.ax.axhline(y=goal, color=accent_color, linestyle='--', alpha=0.8, label='Daily Goal')
        
        # Format x-axis to show day names
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%a'))
        
        # Highlight today
        for i, d in enumerate(dates):
            if d == today:
                self.ax.get_xticklabels()[i].set_weight('bold')
                self.ax.get_xticklabels()[i].set_color(theme_color)
        
        # Set labels and title
        self.ax.set_title('Weekly Hydration', fontdict=title_font)
        self.ax.set_ylabel('Drinks', fontdict=axis_font)
        
        # Add count labels on top of bars
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                self.ax.annotate(f'{height}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom',
                            color=text_color, fontsize=9)
                            
        # Set y-axis limits with some headroom
        max_count = max(max(counts), goal) if counts else goal
        self.ax.set_ylim(0, max_count * 1.2)
        
    def plot_monthly_data(self, data, today, theme_color, text_color, accent_color, title_font, axis_font):
        """Plot monthly view of hydration data"""
        # Define the month range
        year = today.year
        month = today.month
        _, last_day = calendar.monthrange(year, month)
        date_range = [datetime(year, month, day).date() for day in range(1, last_day + 1)]
        
        # Filter data for the month
        monthly_data = {}
        for date in date_range:
            if date <= today:  # Don't show future dates
                monthly_data[date] = 0
            
        for d, count in data:
            if d.year == year and d.month == month:
                monthly_data[d] = count
                
        # Prepare plot data
        dates = list(monthly_data.keys())
        counts = list(monthly_data.values())
        
        # Create gradient bars
        colors = []
        for d in dates:
            if d == today:
                colors.append(theme_color)
            else:
                colors.append(f"{theme_color}A0")  # Semi-transparent
        
        # Plot bars
        bars = self.ax.bar(dates, counts, width=0.8, color=colors, edgecolor=theme_color, linewidth=1)
        
        # Add goal line
        goal = self.main_app.daily_hydration_goal
        self.ax.axhline(y=goal, color=accent_color, linestyle='--', alpha=0.8, label='Daily Goal')
        
        # Format x-axis
        locator = mdates.AutoDateLocator(minticks=4, maxticks=10)
        formatter = mdates.ConciseDateFormatter(locator)
        self.ax.xaxis.set_major_locator(locator)
        self.ax.xaxis.set_major_formatter(formatter)
        
        # Set labels and title
        month_name = calendar.month_name[month]
        self.ax.set_title(f'{month_name} {year} Hydration', fontdict=title_font)
        self.ax.set_ylabel('Drinks', fontdict=axis_font)
        
        # Set y-axis limits with some headroom
        max_count = max(max(counts), goal) if counts else goal
        self.ax.set_ylim(0, max_count * 1.2)
        
    def plot_yearly_data(self, data, today, theme_color, secondary_color, text_color, title_font, axis_font):
        """Plot yearly view of hydration data"""
        # Group data by month
        year = today.year
        monthly_totals = [0] * 12  # One for each month
        daily_counts = {}
        
        for d, count in data:
            if d.year == year:
                # Add to monthly total
                monthly_totals[d.month - 1] += count
                
                # Store for calculating average
                month_key = d.month
                if month_key not in daily_counts:
                    daily_counts[month_key] = []
                daily_counts[month_key].append(count)
        
        # Calculate monthly averages
        monthly_avgs = []
        for month in range(1, 13):
            if month in daily_counts and daily_counts[month]:
                # Only count days with data
                days_with_data = len([c for c in daily_counts[month] if c > 0])
                if days_with_data > 0:
                    avg = sum(daily_counts[month]) / days_with_data
                else:
                    avg = 0
            else:
                avg = 0
            monthly_avgs.append(avg)
        
        # Only show data up to current month
        current_month = today.month
        months_to_show = list(range(1, current_month + 1))
        totals_to_show = monthly_totals[:current_month]
        avgs_to_show = monthly_avgs[:current_month]
        
        # Month labels
        month_labels = [calendar.month_abbr[m] for m in months_to_show]
        x = range(len(months_to_show))
        
        # Plot total bars and average line
        bars = self.ax.bar(x, totals_to_show, width=0.7, color=theme_color, alpha=0.7, label='Monthly Total')
        
        # Secondary axis for averages
        self.ax2 = self.ax.twinx()
        self.ax2.plot(x, avgs_to_show, 'o-', color=secondary_color, linewidth=2, label='Daily Average')
        self.ax2.set_ylabel('Daily Average', color=secondary_color)
        self.ax2.tick_params(axis='y', colors=secondary_color)
        
        # Add goal reference
        goal = self.main_app.daily_hydration_goal
        self.ax2.axhline(y=goal, color=secondary_color, linestyle='--', alpha=0.6)
        
        # Set x-axis labels
        self.ax.set_xticks(x)
        self.ax.set_xticklabels(month_labels)
        
        # Set labels and title
        self.ax.set_title(f'{year} Hydration', fontdict=title_font)
        self.ax.set_ylabel('Monthly Total', fontdict=axis_font)
        
        # Add count labels on top of bars
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                self.ax.annotate(f'{int(height)}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom',
                            color=text_color, fontsize=9)
                            
        # Create combined legend
        lines1, labels1 = self.ax.get_legend_handles_labels()
        lines2, labels2 = self.ax2.get_legend_handles_labels()
        self.ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # Remove spines from second axis too
        for spine in self.ax2.spines.values():
            spine.set_visible(False)