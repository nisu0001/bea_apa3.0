# dialogs/achievement_manager.py
from datetime import datetime, timedelta
import json
from PyQt5.QtCore import QObject, pyqtSignal

class Achievement:
    """Class representing an achievement that can be unlocked"""
    def __init__(self, id, name, description, icon="trophy", is_major=False):
        self.id = id
        self.name = name
        self.description = description
        self.icon = icon
        self.unlocked = False
        self.unlock_date = None
        self.is_major = is_major  # Special/important achievements
        self.progress = 0
        self.progress_max = 0
    
    def __repr__(self):
        return f"<Achievement: {self.name} - Unlocked: {self.unlocked}>"
    
    def to_dict(self):
        """Convert achievement to dictionary for storage"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "unlocked": self.unlocked,
            "unlock_date": self.unlock_date.isoformat() if self.unlock_date else None,
            "is_major": self.is_major,
            "progress": self.progress,
            "progress_max": self.progress_max
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create achievement from dictionary"""
        achievement = cls(
            data["id"],
            data["name"],
            data["description"],
            data.get("icon", "trophy"),
            data.get("is_major", False)
        )
        achievement.unlocked = data.get("unlocked", False)
        
        # Parse unlock date if present
        if data.get("unlock_date"):
            try:
                achievement.unlock_date = datetime.fromisoformat(data["unlock_date"])
            except (ValueError, TypeError):
                achievement.unlock_date = None
        
        # Set progress if available
        achievement.progress = data.get("progress", 0)
        achievement.progress_max = data.get("progress_max", 0)
        
        return achievement
    
    def unlock(self):
        """Mark achievement as unlocked with current timestamp"""
        if not self.unlocked:
            self.unlocked = True
            self.unlock_date = datetime.now()
            return True
        return False
    
    def update_progress(self, new_progress):
        """Update progress towards achievement completion"""
        if self.unlocked:
            return False
            
        old_progress = self.progress
        self.progress = min(new_progress, self.progress_max)
        
        # Check if achievement should be unlocked
        if self.progress >= self.progress_max and self.progress_max > 0:
            self.unlock()
            return True
            
        # Return True if progress changed
        return old_progress != self.progress


class AchievementManager(QObject):
    """Manages tracking and unlocking of achievements"""
    
    # Signal emitted when an achievement is unlocked
    achievement_unlocked = pyqtSignal(object)
    
    def __init__(self, settings_manager=None):
        super().__init__()
        self.settings_manager = settings_manager
        self.achievements = []
        self.initialized = False
        
        # Initialize achievements
        self.initialize_achievements()
    
    def initialize_achievements(self):
        """Create and initialize all achievements"""
        if self.initialized:
            return
            
        # Define achievement list if not loaded
        if not self.achievements:
            # Load from settings or create defaults
            stored_achievements = {}
            if self.settings_manager:
                # Updated to match your SettingsManager's get() method signature
                stored_achievements = self.settings_manager.get("achievements")
                if stored_achievements is None:
                    stored_achievements = {}
            
            if stored_achievements:
                # Check if stored_achievements is a list or dictionary
                if isinstance(stored_achievements, list):
                    # If it's a list, convert to dictionary format by ID
                    achievement_dict = {}
                    for achievement_data in stored_achievements:
                        if isinstance(achievement_data, dict) and 'id' in achievement_data:
                            achievement_dict[achievement_data['id']] = achievement_data
                    stored_achievements = achievement_dict
                
                # Now load the achievements
                try:
                    # If it's a dictionary, iterate over values
                    if isinstance(stored_achievements, dict):
                        for achievement_data in stored_achievements.values():
                            self.achievements.append(Achievement.from_dict(achievement_data))
                    # If it's a list (fallback)
                    elif isinstance(stored_achievements, list):
                        for achievement_data in stored_achievements:
                            if isinstance(achievement_data, dict):
                                self.achievements.append(Achievement.from_dict(achievement_data))
                except Exception as e:
                    print(f"Error loading achievements: {e}")
                    # Create default achievements if loading fails
                    self.create_default_achievements()
            else:
                # Create default achievements
                self.create_default_achievements()
        
        self.initialized = True
    
    def create_default_achievements(self):
        """Create default achievement list"""
        # Daily goals achievements
        self.achievements.extend([
            Achievement(
                "first_drink", 
                "First Sip", 
                "Log your first hydration", 
                icon="water"
            ),
            Achievement(
                "daily_goal", 
                "Daily Goal Achieved", 
                "Reach your daily hydration goal", 
                icon="target"
            ),
            Achievement(
                "three_day_streak", 
                "Three Day Streak", 
                "Meet your daily goal for 3 days in a row", 
                icon="fire",
                is_major=True
            ),
            Achievement(
                "week_streak", 
                "Week Warrior", 
                "Meet your daily goal for 7 days in a row", 
                icon="fire",
                is_major=True
            ),
            Achievement(
                "month_streak", 
                "Monthly Master", 
                "Meet your daily goal for 30 days in a row", 
                icon="trophy",
                is_major=True
            ),
        ])
        
        # Accumulated counts
        total_drinks = Achievement(
            "total_drinks_100", 
            "Century Sipper", 
            "Log 100 total drinks", 
            icon="water"
        )
        total_drinks.progress_max = 100
        
        total_drinks_500 = Achievement(
            "total_drinks_500", 
            "Hydration Hero", 
            "Log 500 total drinks", 
            icon="badge",
            is_major=True
        )
        total_drinks_500.progress_max = 500
        
        self.achievements.extend([total_drinks, total_drinks_500])
        
        # Time-based achievements
        self.achievements.extend([
            Achievement(
                "morning_person", 
                "Morning Person", 
                "Log a drink before 9am for 5 days", 
                icon="sunrise"
            ),
            Achievement(
                "night_owl", 
                "Night Owl", 
                "Log a drink after 10pm for 5 days", 
                icon="moon"
            ),
            Achievement(
                "consistency", 
                "Consistency is Key", 
                "Log drinks at regular intervals throughout the day", 
                icon="clock"
            ),
        ])
        
        # Special achievements
        perfect_week = Achievement(
            "perfect_week", 
            "Perfect Week", 
            "Meet or exceed your goal every day for a week", 
            icon="star",
            is_major=True
        )
        perfect_week.progress_max = 7  # Need 7 perfect days
        
        self.achievements.append(perfect_week)
        
        # Todo-related achievements
        task_master = Achievement(
            "task_master", 
            "Task Master", 
            "Complete 10 tasks", 
            icon="check",
            is_major=False
        )
        task_master.progress_max = 10
        
        productivity_guru = Achievement(
            "productivity_guru", 
            "Productivity Guru", 
            "Complete 50 tasks", 
            icon="star",
            is_major=True
        )
        productivity_guru.progress_max = 50
        
        deadline_hero = Achievement(
            "deadline_hero", 
            "Deadline Hero", 
            "Complete 5 tasks before their deadlines", 
            icon="clock"
        )
        deadline_hero.progress_max = 5
        
        daily_grind = Achievement(
            "daily_grind", 
            "Daily Grind", 
            "Complete at least one task every day for 5 days", 
            icon="calendar"
        )
        daily_grind.progress_max = 5
        
        hydrated_worker = Achievement(
            "hydrated_worker", 
            "Hydrated Worker", 
            "Reach your hydration goal and complete 3 tasks in a single day", 
            icon="water"
        )
        
        category_master = Achievement(
            "category_master", 
            "Category Champion", 
            "Complete all tasks in a category", 
            icon="badge"
        )
        
        self.achievements.extend([
            task_master,
            productivity_guru,
            deadline_hero,
            daily_grind,
            hydrated_worker,
            category_master
        ])
    
    def save_achievements(self):
        """Save achievements to settings"""
        if not self.settings_manager:
            return False
            
        # Convert achievements to dictionary format
        achievement_dict = {}
        for achievement in self.achievements:
            achievement_dict[achievement.id] = achievement.to_dict()
            
        # Save to settings
        self.settings_manager.set("achievements", achievement_dict)
        # Make sure to save the settings
        self.settings_manager.save_settings()
        return True
    
    def get_achievement(self, achievement_id):
        """Get achievement by ID"""
        for achievement in self.achievements:
            if achievement.id == achievement_id:
                return achievement
        return None
    
    def unlock_achievement(self, achievement_id):
        """Unlock an achievement by ID"""
        achievement = self.get_achievement(achievement_id)
        if achievement and not achievement.unlocked:
            if achievement.unlock():
                self.save_achievements()
                self.achievement_unlocked.emit(achievement)
                return achievement
        return None
    
    def update_achievement_progress(self, achievement_id, progress):
        """Update progress for an achievement"""
        achievement = self.get_achievement(achievement_id)
        if achievement:
            if achievement.update_progress(progress):
                self.save_achievements()
                if achievement.unlocked:
                    self.achievement_unlocked.emit(achievement)
                return True
        return False
    
    def get_unlocked_achievements(self):
        """Get list of all unlocked achievements"""
        return [a for a in self.achievements if a.unlocked]
    
    def get_locked_achievements(self):
        """Get list of all locked (not yet unlocked) achievements"""
        return [a for a in self.achievements if not a.unlocked]
    
    def check_streak_achievements(self, history):
        """Check and update streak-based achievements"""
        newly_unlocked = []
        
        if not history:
            return newly_unlocked
            
        # Calculate current streak
        sorted_dates = sorted([datetime.fromisoformat(date) for date in history.keys()])
        
        # If no dates or latest date is not yesterday/today, no streak
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        if not sorted_dates or sorted_dates[-1].date() < yesterday:
            current_streak = 0
        else:
            # Count consecutive days backward from latest date
            current_streak = 1
            for i in range(len(sorted_dates) - 1, 0, -1):
                if (sorted_dates[i].date() - sorted_dates[i-1].date()).days == 1:
                    current_streak += 1
                else:
                    break
        
        # Check streak achievements
        streak_achievements = {
            "three_day_streak": 3,
            "week_streak": 7,
            "month_streak": 30
        }
        
        for achievement_id, required_streak in streak_achievements.items():
            if current_streak >= required_streak:
                achievement = self.get_achievement(achievement_id)
                if achievement and not achievement.unlocked:
                    achievement.unlock()
                    newly_unlocked.append(achievement)
        
        # Perfect week achievement
        # This checks if there were 7 consecutive days where the goal was met
        perfect_week = self.get_achievement("perfect_week")
        if perfect_week and not perfect_week.unlocked:
            # We'll need the daily goal to check if it was met
            daily_goal = self.settings_manager.get("daily_goal")
            if daily_goal is None:
                daily_goal = 8
            
            # Check for 7 consecutive days meeting or exceeding the goal
            perfect_days = 0
            for date_str, count in history.items():
                try:
                    date = datetime.fromisoformat(date_str).date()
                    # Check if this day met or exceeded the goal
                    if count >= daily_goal:
                        perfect_days += 1
                    else:
                        perfect_days = 0  # Reset on non-perfect days
                    
                    # If we've accumulated 7 perfect days
                    if perfect_days >= 7:
                        perfect_week.unlock()
                        newly_unlocked.append(perfect_week)
                        break
                except (ValueError, TypeError):
                    continue
        
        if newly_unlocked:
            self.save_achievements()
            
        return newly_unlocked
    
    def check_count_achievements(self, total_count):
        """Check and update count-based achievements"""
        newly_unlocked = []
        
        # First drink achievement
        if total_count > 0:
            first_drink = self.get_achievement("first_drink")
            if first_drink and not first_drink.unlocked:
                first_drink.unlock()
                newly_unlocked.append(first_drink)
        
        # Total drinks achievements
        count_achievements = [
            ("total_drinks_100", 100),
            ("total_drinks_500", 500)
        ]
        
        for achievement_id, required_count in count_achievements:
            achievement = self.get_achievement(achievement_id)
            if achievement:
                if achievement.update_progress(total_count) and achievement.unlocked:
                    newly_unlocked.append(achievement)
        
        if newly_unlocked:
            self.save_achievements()
            
        return newly_unlocked
    
    def check_daily_goal_achievement(self, current_count, daily_goal):
        """Check if daily goal has been achieved"""
        if current_count >= daily_goal:
            achievement = self.get_achievement("daily_goal")
            if achievement and not achievement.unlocked:
                achievement.unlock()
                self.save_achievements()
                return achievement
        return None
    
    def check_time_based_achievements(self, log_times):
        """Check and update time-based achievements"""
        newly_unlocked = []
        
        if not log_times or len(log_times) < 5:
            return newly_unlocked
        
        # Morning person: Log a drink before 9am for 5 days
        morning_achievement = self.get_achievement("morning_person")
        if morning_achievement and not morning_achievement.unlocked:
            morning_count = 0
            for timestamp in log_times:
                dt = datetime.fromisoformat(timestamp)
                if dt.hour < 9:  # Before 9am
                    morning_count += 1
            
            if morning_count >= 5:
                morning_achievement.unlock()
                newly_unlocked.append(morning_achievement)
        
        # Night owl: Log a drink after 10pm for 5 days
        night_achievement = self.get_achievement("night_owl")
        if night_achievement and not night_achievement.unlocked:
            night_count = 0
            for timestamp in log_times:
                dt = datetime.fromisoformat(timestamp)
                if dt.hour >= 22:  # After 10pm
                    night_count += 1
            
            if night_count >= 5:
                night_achievement.unlock()
                newly_unlocked.append(night_achievement)
        
        # Consistency achievement: Logs throughout the day
        consistency_achievement = self.get_achievement("consistency")
        if consistency_achievement and not consistency_achievement.unlocked:
            # Group timestamps by day
            days = {}
            for timestamp in log_times:
                dt = datetime.fromisoformat(timestamp)
                day_key = dt.date().isoformat()
                if day_key not in days:
                    days[day_key] = []
                days[day_key].append(dt)
            
            # Check if any day has good distribution (at least 4 logs with >2 hours between)
            consistent_days = 0
            for day, times in days.items():
                if len(times) < 4:
                    continue
                    
                # Sort times and check intervals
                times.sort()
                good_intervals = 0
                for i in range(1, len(times)):
                    interval = (times[i] - times[i-1]).total_seconds() / 3600  # Hours
                    if interval >= 2:
                        good_intervals += 1
                
                if good_intervals >= 3:  # At least 3 good intervals
                    consistent_days += 1
            
            if consistent_days >= 1:  # At least one day with good consistency
                consistency_achievement.unlock()
                newly_unlocked.append(consistency_achievement)
        
        if newly_unlocked:
            self.save_achievements()
            
        return newly_unlocked
    
    def check_todo_achievements(self, todo_widget):
        """Check for todo-related achievements"""
        newly_unlocked = []
        
        if not todo_widget:
            return newly_unlocked
        
        # Get task statistics
        task_stats = todo_widget.get_task_stats()
        daily_goal = 8
        hydration_log_count = 0
        
        # Try to get current hydration values from settings
        if self.settings_manager:
            daily_goal = self.settings_manager.get("daily_goal") or 8
            hydration_log_count = self.settings_manager.get("log_count") or 0
        
        # Track achievements
        task_master = self.get_achievement("task_master")
        productivity_guru = self.get_achievement("productivity_guru") 
        deadline_hero = self.get_achievement("deadline_hero")
        daily_grind = self.get_achievement("daily_grind")
        hydrated_worker = self.get_achievement("hydrated_worker")
        category_master = self.get_achievement("category_master")
        
        # Update task completion counts
        if task_master:
            completed_tasks = task_stats.get("completed", 0)
            if self.update_achievement_progress("task_master", completed_tasks):
                newly_unlocked.append(task_master)
        
        if productivity_guru:
            completed_tasks = task_stats.get("completed", 0)
            if self.update_achievement_progress("productivity_guru", completed_tasks):
                newly_unlocked.append(productivity_guru)
        
        # Track "Daily Grind" achievement (task completion for 5 consecutive days)
        if daily_grind and not daily_grind.unlocked:
            # Get or create the daily task completion tracking
            daily_task_completions = self.settings_manager.get("daily_task_completions")
            if not daily_task_completions:
                daily_task_completions = []
                
            # Add today if tasks were completed today
            today = datetime.now().date().isoformat()
            if task_stats.get("completed_today", 0) > 0 and today not in daily_task_completions:
                daily_task_completions.append(today)
                
                # Keep only the last 10 days
                if len(daily_task_completions) > 10:
                    daily_task_completions = daily_task_completions[-10:]
                
                # Save back to settings
                self.settings_manager.set("daily_task_completions", daily_task_completions)
                
                # Count consecutive days
                dates = [datetime.fromisoformat(d).date() for d in daily_task_completions]
                dates.sort(reverse=True)
                
                consecutive = 1
                max_consecutive = 1
                
                for i in range(1, len(dates)):
                    if (dates[i-1] - dates[i]).days == 1:
                        consecutive += 1
                        max_consecutive = max(max_consecutive, consecutive)
                    else:
                        consecutive = 1
                
                # Update progress
                if self.update_achievement_progress("daily_grind", max_consecutive):
                    newly_unlocked.append(daily_grind)
        
        # Check for "Hydrated Worker" achievement (combined hydration and tasks)
        if hydrated_worker and not hydrated_worker.unlocked:
            if task_stats.get("completed_today", 0) >= 3 and hydration_log_count >= daily_goal:
                if hydrated_worker.unlock():
                    newly_unlocked.append(hydrated_worker)
        
        # Check for "Category Champion" achievement (all tasks in a category complete)
        if category_master and not category_master.unlocked:
            for category, counts in task_stats.get("categories", {}).items():
                if counts.get("total", 0) > 0 and counts.get("total", 0) == counts.get("completed", 0):
                    if category_master.unlock():
                        newly_unlocked.append(category_master)
                    break
        
        # Check for "Deadline Hero" achievement (complete tasks before deadline)
        # This needs to track individual task completions
        
        # Save achievements if any were newly unlocked
        if newly_unlocked:
            self.save_achievements()
            
        return newly_unlocked
    
    def update_achievements(self):
        """
        Update all achievements based on current app state.
        Returns a list of newly unlocked achievements.
        """
        if not self.settings_manager:
            return []
            
        newly_unlocked = []
        
        # Get necessary data from settings
        history = self.settings_manager.get("history")
        if history is None:
            history = {}
            
        daily_goal = self.settings_manager.get("daily_goal")
        if daily_goal is None:
            daily_goal = 8
            
        current_count = self.settings_manager.get("log_count")
        if current_count is None:
            current_count = 0
            
        log_times = self.settings_manager.get("log_times")
        if log_times is None:
            log_times = []
        
        # Calculate total drinks (sum of all history + current day)
        total_count = sum(history.values(), 0) + current_count
        
        # Check count-based achievements
        newly_unlocked.extend(self.check_count_achievements(total_count))
        
        # Check streaks
        newly_unlocked.extend(self.check_streak_achievements(history))
        
        # Check daily goal
        daily_achievement = self.check_daily_goal_achievement(current_count, daily_goal)
        if daily_achievement:
            newly_unlocked.append(daily_achievement)
        
        # Check time-based achievements
        newly_unlocked.extend(self.check_time_based_achievements(log_times))
        
        # Find and check todo widget if available
        todo_widget = None
        main_app = None
        
        # Try to find the main app and todo widget
        if hasattr(self, 'parent') and self.parent():
            main_app = self.parent()
            
            if hasattr(main_app, 'todo_list') and main_app.todo_list:
                todo_widget = main_app.todo_list
        
        # Check todo achievements if we found the widget
        if todo_widget:
            newly_unlocked.extend(self.check_todo_achievements(todo_widget))
        
        # Return list of newly unlocked achievements
        return newly_unlocked