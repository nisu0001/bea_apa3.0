# dialogs/profile_system.py
"""
Profile system that handles achievement tracking and notifications
with reliable integration into the main application.
"""
from PyQt5.QtWidgets import QPushButton, QAction, QMenu, QMessageBox
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt, QTimer, QSize, QObject, pyqtSignal

# Update imports to match your SettingsManager implementation
from dialogs.profile_page import ProfilePage
from dialogs.achievement_manager import AchievementManager
from dialogs.achievement_notification import show_achievement_notification
from utils import resource_path

class ProfileSystem(QObject):
    """
    Manages the profile subsystem with achievements and notifications.
    
    This class handles:
    - Achievement tracking and unlocking
    - Profile page access 
    - Achievement notifications with sound and visual effects
    """
    # Signal emitted when an achievement is unlocked
    achievement_unlocked = pyqtSignal(object)
    
    def __init__(self, main_app):
        """
        Initialize the profile system with the main app.
        
        Args:
            main_app: The main application instance
        """
        super().__init__()
        self.main_app = main_app
        
        # Initialize achievement manager
        self.achievement_manager = AchievementManager(main_app.settings_manager)
        
        # Connect signals
        self.achievement_manager.achievement_unlocked.connect(self.on_achievement_unlocked)
        
        # Queue for pending notifications
        self.notification_queue = []
        
        # Active notification reference
        self.active_notification = None
        
        # Install UI elements
        self._install_ui_elements()
        
        # Check achievements after a short delay to ensure app is fully loaded
        QTimer.singleShot(1000, self.update_achievements)
    
    def _install_ui_elements(self):
        """Install UI elements for accessing the profile page"""
        # Add method to main window for showing profile page
        self.main_app.show_profile_page = self.show_profile_page
        
        # Add keyboard shortcut (Ctrl+P)
        try:
            profile_shortcut = QAction(self.main_app)
            profile_shortcut.setShortcut(QKeySequence("Ctrl+P"))
            profile_shortcut.triggered.connect(self.show_profile_page)
            self.main_app.addAction(profile_shortcut)
        except Exception as e:
            print(f"Could not add profile shortcut: {e}")
        
        # Add profile button (floating or in menu)
        self._add_profile_button()
    
    def _add_profile_button(self):
        """Add a profile button to the main application"""
        try:
            # Create a button with style matching the app's theme
            self.profile_btn = QPushButton(self.main_app)
            
            # Use emoji or icon depending on availability
            try:
                icon_path = resource_path("assets/icons/profile.svg")
                self.profile_btn.setIcon(QIcon(icon_path))
                self.profile_btn.setIconSize(QSize(20, 20))
            except:
                # Fallback to emoji if icon not available
                self.profile_btn.setText("👤")
            
            self.profile_btn.setToolTip("Profile & Achievements")
            self.profile_btn.setFixedSize(40, 40)
            self.profile_btn.setCursor(Qt.PointingHandCursor)
            self.profile_btn.clicked.connect(self.show_profile_page)
            
            # Update button styling based on theme
            self._update_button_style()
            
            # Position in the bottom right
            self._position_profile_button()
            
            # Update position when window is resized
            original_resize_event = self.main_app.resizeEvent
            def new_resize_event(event):
                if original_resize_event:
                    original_resize_event(event)
                self._position_profile_button()
            
            self.main_app.resizeEvent = new_resize_event
            
            # Make button visible
            self.profile_btn.show()
            
            # Update button style when theme changes
            if hasattr(self.main_app, 'theme_changed'):
                self.main_app.theme_changed.connect(self._update_button_style)
            
        except Exception as e:
            print(f"Could not add profile button: {e}")
    
    def _position_profile_button(self):
        """Position the profile button in the bottom right of the window"""
        if hasattr(self, 'profile_btn'):
            margin = 16  # Margin from edges
            self.profile_btn.move(
                self.main_app.width() - self.profile_btn.width() - margin,
                self.main_app.height() - self.profile_btn.height() - margin
            )
    
    def _update_button_style(self):
        """Update the profile button style based on current theme"""
        if not hasattr(self, 'profile_btn'):
            return
            
        # Get theme colors
        theme = {}
        if hasattr(self.main_app, 'get_theme'):
            theme = self.main_app.get_theme()
        
        # Default colors
        is_dark = theme.get("is_dark", True)
        primary = theme.get("primary", "#0A84FF")
        text = theme.get("text", "#FFFFFF" if is_dark else "#000000")
        
        # Set button style
        self.profile_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {primary};
                color: white;
                border-radius: 20px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {primary}DD;  /* Slightly transparent on hover */
            }}
        """)
    
    def show_profile_page(self):
        """Show the profile page dialog"""
        try:
            dialog = ProfilePage(self.main_app)
            dialog.exec_()
        except Exception as e:
            print(f"Error showing profile page: {e}")
            if hasattr(self.main_app, 'show_message'):
                self.main_app.show_message(f"Could not open profile page: {str(e)}")
    
    def update_achievements(self):
        """Check for new achievement unlocks and show notifications"""
        try:
            # Update achievements
            newly_unlocked = self.achievement_manager.update_achievements()
            
            # Queue notifications for any newly unlocked achievements
            for achievement in newly_unlocked:
                self.queue_achievement_notification(achievement)
            
            # Start showing notifications if we have any
            self._process_notification_queue()
            
            return newly_unlocked
        except Exception as e:
            print(f"Error updating achievements: {e}")
            return []
    
    def on_achievement_unlocked(self, achievement):
        """Handle when an achievement is unlocked via signal"""
        # Queue a notification
        self.queue_achievement_notification(achievement)
        
        # Process the queue
        self._process_notification_queue()
    
    def queue_achievement_notification(self, achievement):
        """Add an achievement to the notification queue"""
        self.notification_queue.append(achievement)
    
    def _process_notification_queue(self):
        """Process queued notifications one at a time"""
        # If we're already showing a notification or queue is empty, return
        if self.active_notification or not self.notification_queue:
            return
        
        # Get next achievement
        achievement = self.notification_queue.pop(0)
        
        # Get theme
        theme = {}
        if hasattr(self.main_app, 'get_theme'):
            theme = self.main_app.get_theme()
        
        # Show notification
        try:
            self.active_notification = show_achievement_notification(
                achievement, 
                self.main_app,
                theme,
                play_sound=hasattr(self.main_app, 'sound_enabled') and self.main_app.sound_enabled
            )
            
            # After notification is shown, set up timer to process next notification
            def on_notification_finished():
                self.active_notification = None
                # Process next notification with a delay
                QTimer.singleShot(500, self._process_notification_queue)
            
            # Connect to window close event
            QTimer.singleShot(5500, on_notification_finished)
            
        except Exception as e:
            print(f"Error showing achievement notification: {e}")
            self.active_notification = None
            
            # Try next notification
            QTimer.singleShot(500, self._process_notification_queue)


def install_profile_system(main_app):
    """
    Install the profile system into the main application.
    
    Args:
        main_app: The main application instance
    
    Returns:
        ProfileSystem: The initialized profile system
    """
    try:
        print("Installing profile system...")
        profile_system = ProfileSystem(main_app)
        
        # Store a reference in the main app
        main_app.profile_system = profile_system
        
        # Verify installation
        has_profile_system = hasattr(main_app, 'profile_system')
        has_profile_page = hasattr(main_app, 'show_profile_page')
        print(f"Profile system installed: {has_profile_system}")
        print(f"Profile page method added: {has_profile_page}")
        
        return profile_system
    except Exception as e:
        print(f"Failed to install profile system: {e}")
        return None