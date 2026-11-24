Set WshShell = CreateObject("WScript.Shell")
strPath = WshShell.CurrentDirectory
WshShell.Run "python """ & strPath & "\desktop_launcher.py""", 0, False
