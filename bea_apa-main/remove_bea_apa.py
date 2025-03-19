import sys
import os

def unregister_autostart():
    """
    Removes the auto-start registration for the application.
    On Windows, it deletes the registry key; on Linux, it removes the .desktop file.
    """
    if sys.platform == 'win32':
        try:
            import winreg as reg
            reg_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, reg_key, 0, reg.KEY_ALL_ACCESS)
            try:
                reg.DeleteValue(key, "bea_apa")
                print("Removed auto-start registry entry.")
            except FileNotFoundError:
                print("Auto-start registry entry not found.")
            reg.CloseKey(key)
        except Exception as e:
            print("Error removing auto-start registry entry:", e)
    elif sys.platform.startswith('linux'):
        try:
            autostart_dir = os.path.expanduser("~/.config/autostart")
            desktop_path = os.path.join(autostart_dir, "beaapa.desktop")
            if os.path.exists(desktop_path):
                os.remove(desktop_path)
                print("Removed autostart .desktop file.")
            else:
                print("Autostart .desktop file not found.")
        except Exception as e:
            print("Error removing autostart on Linux:", e)
    elif sys.platform == 'darwin':
        # For macOS, instruct the user (or script the removal) of the LaunchAgent plist.
        print("Please remove the LaunchAgent plist file manually from ~/Library/LaunchAgents.")
    else:
        print("Auto-start removal is not supported on this platform.")
def main():
    
    unregister_autostart()
    sys.exit()

if __name__ == "__main__":
    main()