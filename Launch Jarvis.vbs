Set WshShell = CreateObject("WScript.Shell")
' Run python.exe or pythonw.exe completely silently (0 means hide window)
' We use cmd /c to ensure it picks up the virtual environment if necessary, but here we just point to the script.
WshShell.Run "pythonw """ & CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & "\jarvis.py""", 0, False
