import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from core.settings_manager import SettingsManager
from core.main_window import MainWindow

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
        # See the instructions for creating a plist file and placing it in ~/Library/LaunchAgents.
        print("Auto-start registration on macOS requires creating a LaunchAgent plist. Please set that up separately.")
    else:
        print("Auto-start registration is not supported on this platform.")

def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)

    instance_id = "bea_apa_instance"
    socket = QLocalSocket()
    socket.connectToServer(instance_id)
    if socket.waitForConnected(100):
        socket.write(b'raise')
        socket.flush()
        socket.disconnectFromServer()
        return

    try:
        QLocalServer.removeServer(instance_id)
    except Exception:
        pass

    server = QLocalServer()
    if not server.listen(instance_id):
        print("Unable to start local server:", server.errorString())
        return

    settings_manager = SettingsManager()
    main_window = MainWindow(settings_manager)
    main_window.show()

    




    # Register auto-start only if enabled in settings
    if settings_manager.get('start_at_login'):
        register_autostart()

    def on_new_connection():
        new_socket = server.nextPendingConnection()
        if new_socket:
            if new_socket.waitForReadyRead(100):
                message = bytes(new_socket.readAll()).decode('utf-8')
                if message == "raise":
                    main_window.showNormal()
                    main_window.activateWindow()
                    main_window.raise_()
            new_socket.disconnectFromServer()

    server.newConnection.connect(on_new_connection)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()