import sys
import os
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QMessageBox
from PyQt5.QtCore import Qt, QTimer, QUrl, QPropertyAnimation, QEasingCurve
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QIcon

from core.settings_manager import SettingsManager
from core.main_window import MainWindow
from utils import resource_path


class HTMLSplashScreen(QWidget):
    """
    Custom splash screen that loads an HTML/CSS/JS animation
    and displays it for a minimum specified duration.
    """
    def __init__(self, html_path, min_display_time=10):
        super().__init__()
        self.min_display_time = min_display_time * 1000  # Convert to milliseconds
        self.html_path = html_path
        self.start_time = None
        self.main_window = None
        
        # Initialize UI without showing it yet
        self.init_ui()
        
    def init_ui(self):
        """Set up the splash screen UI components"""
        # Remove window frame and stay on top
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # Create a main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create web view for HTML content
        self.web_view = QWebEngineView()
        self.web_view.setContextMenuPolicy(Qt.NoContextMenu)  # Disable right-click menu
        
        # Set fixed size for splash screen
        self.web_view.setFixedSize(800, 600)
        self.setFixedSize(800, 600)
        
        # Add web view to layout
        layout.addWidget(self.web_view)
        
        # Center on screen
        self.center_on_screen()
        
    def center_on_screen(self):
        """Center the splash screen on the primary display"""
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        
    def show_splash(self, main_window):
        """
        Show the splash screen and start the timer for minimum display time.
        
        Args:
            main_window: The main application window to show after splash completes
        """
        self.main_window = main_window
        self.start_time = time.time() * 1000  # Current time in milliseconds
        
        try:
            # Try to load the HTML file from assets
            splash_url = QUrl.fromLocalFile(os.path.abspath(self.html_path))
            self.web_view.load(splash_url)
            
            # Connect the loadFinished signal to handle when loading completes
            self.web_view.loadFinished.connect(self.on_load_finished)
            
            # Show the splash screen
            self.show()
            
        except Exception as e:
            # Handle error loading splash screen
            self.handle_error(f"Error loading splash screen: {str(e)}")
    
    def on_load_finished(self, success):
        """Handle the completion of HTML loading"""
        if not success:
            self.handle_error("Failed to load the splash screen animation")
            return
            
        # Calculate how much time has already passed
        elapsed_time = time.time() * 1000 - self.start_time
        
        # If we haven't displayed for the minimum time, set a timer for the remaining time
        if elapsed_time < self.min_display_time:
            remaining_time = self.min_display_time - elapsed_time
            QTimer.singleShot(int(remaining_time), self.prepare_transition)
        else:
            # We've already displayed long enough, transition immediately
            self.prepare_transition()
    
    def prepare_transition(self):
        """Prepare to transition by signaling the HTML animation"""
        # Signal to the HTML that we're preparing to transition
        self.web_view.page().runJavaScript(
            "document.dispatchEvent(new CustomEvent('prepareTransition'));")
        
        # Give a moment for final animations
        QTimer.singleShot(1000, self.finish_splash)
    
    def finish_splash(self):
        """Transition from the splash screen to the main application window"""
        if self.main_window:
            # Create a fade-out animation for the splash screen
            self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
            self.fade_out_animation.setDuration(500)  # 500ms fade
            self.fade_out_animation.setStartValue(1.0)
            self.fade_out_animation.setEndValue(0.0)
            self.fade_out_animation.setEasingCurve(QEasingCurve.OutQuad)
            
            # When fade completes, hide splash and show main window
            self.fade_out_animation.finished.connect(self.hide)
            self.fade_out_animation.finished.connect(self.main_window.show)
            
            # Start the animation
            self.fade_out_animation.start()
        else:
            # In case main_window wasn't set
            self.hide()
    
    def handle_error(self, message):
        """Handle errors with loading the splash screen"""
        print(f"Splash Screen Error: {message}")
        
        # Close the splash screen
        self.hide()
        
        # Show error message box
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Warning)
        error_box.setWindowTitle("Splash Screen Error")
        error_box.setText(message)
        error_box.setStandardButtons(QMessageBox.Ok)
        
        # Show the main window directly
        if self.main_window:
            self.main_window.show()
            
        # Display the error box
        error_box.exec_()

def register_autostart():
    """
    Registers the application to run automatically on system startup.
    Supports Windows and Linux. On macOS, the user must create a LaunchAgent plist.
    """
    if sys.platform == 'win32':
        try:
            import winreg as reg
            # Determine the path to use:
            exe_path = sys.executable
            # If running as a script, sys.executable points to python.exe,
            # so we use the full path to the current script.
            if exe_path.endswith("python.exe"):
                exe_path = os.path.abspath(sys.argv[0])
            reg_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, reg_key, 0, reg.KEY_SET_VALUE)
            # The registry value name ("bea_apa") can be changed to suit your app
            reg.SetValueEx(key, "bea_apa", 0, reg.REG_SZ, exe_path)
            reg.CloseKey(key)
            print("Registered in Windows startup.")
        except Exception as e:
            print("Error registering auto-start in Windows:", e)
    elif sys.platform.startswith('linux'):
        try:
            # Create a .desktop file for autostart
            desktop_entry = f"""[Desktop Entry]
Type=Application
Exec={sys.executable} {os.path.abspath(sys.argv[0])}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=BeaApa
Comment=Automatically start BeaApa on login
"""
            autostart_dir = os.path.expanduser("~/.config/autostart")
            if not os.path.exists(autostart_dir):
                os.makedirs(autostart_dir)
            desktop_path = os.path.join(autostart_dir, "beaapa.desktop")
            with open(desktop_path, "w") as f:
                f.write(desktop_entry)
            print("Registered auto-start on Linux.")
        except Exception as e:
            print("Error registering auto-start on Linux:", e)
    elif sys.platform == 'darwin':
        # For macOS, auto-start registration is typically handled with LaunchAgents.
        print("Auto-start registration on macOS requires creating a LaunchAgent plist. Please set that up separately.")
    else:
        print("Auto-start registration is not supported on this platform.")

def main():
    # Enable high DPI scaling (useful for HiDPI displays)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)

    # Unique name for our local server
    instance_id = "bea_apa_instance"

    # Try connecting to an already running instance
    socket = QLocalSocket()
    socket.connectToServer(instance_id)
    if socket.waitForConnected(100):
        # If connected, send a message to raise the existing window
        socket.write(b'raise')
        socket.flush()
        socket.disconnectFromServer()
        # Exit this second instance.
        return

    # No existing instance, so remove any stray server (especially on Unix) and start one.
    try:
        QLocalServer.removeServer(instance_id)
    except Exception:
        pass

    server = QLocalServer()
    if not server.listen(instance_id):
        print("Unable to start local server:", server.errorString())
        return

    # Initialize settings and create the main window (but don't show it yet)
    settings_manager = SettingsManager()
    main_window = MainWindow(settings_manager)

    # Set up the server connection handler
    def on_new_connection():
        new_socket = server.nextPendingConnection()
        if new_socket:
            if new_socket.waitForReadyRead(100):
                # Read and decode the message from the new instance
                message = bytes(new_socket.readAll()).decode('utf-8')
                if message == "raise":
                    # Bring the main window to the front
                    main_window.showNormal()
                    main_window.activateWindow()
                    main_window.raise_()
            new_socket.disconnectFromServer()

    server.newConnection.connect(on_new_connection)

    # Define path to HTML splash screen
    splash_path = resource_path(os.path.join("assets", "splash", "splash.html"))
    
    # Create and show the splash screen
    splash = HTMLSplashScreen(splash_path, min_display_time=10)
    
    # Start the application by showing the splash screen
    # The splash will handle showing the main window when it's done
    splash.show_splash(main_window)

    # Register the application to run at startup
    register_autostart()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()