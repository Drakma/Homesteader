Set WshShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strPath & "\assets"
WshShell.Run "pythonw app.py", 0, False
Set WshShell = Nothing

