import os
import subprocess

base_dir = os.path.dirname(os.path.abspath(__file__))
vbs_path = os.path.join(base_dir, "Launch_Silent.vbs")
bat_path = os.path.join(base_dir, "Launch_App.bat")

desktop_dir = os.path.expandvars(r"%USERPROFILE%\OneDrive\Desktop")
if not os.path.exists(desktop_dir):
    desktop_dir = os.path.expandvars(r"%USERPROFILE%\Desktop")

shortcut_path = os.path.join(desktop_dir, "Intelligent Expense Tracker.lnk")

# PowerShell command to create Windows shortcut
ps_command = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
$Shortcut.TargetPath = '{vbs_path}'
$Shortcut.WorkingDirectory = '{base_dir}'
$Shortcut.Description = 'Intelligent Expense Tracker with Personalized Spending Insights'
$Shortcut.IconLocation = 'shell32.dll,283'
$Shortcut.Save()
"""

try:
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_command], check=True)
    print("Desktop shortcut created successfully at:", shortcut_path)
except Exception as e:
    print("Failed to create shortcut:", e)
