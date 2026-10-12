Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)

pythonExe = currentDir & "\venv\Scripts\pythonw.exe"
scriptPath = currentDir & "\desktop_app.py"

If fso.FileExists(pythonExe) Then
    WshShell.CurrentDirectory = currentDir
    WshShell.Run """" & pythonExe & """ """ & scriptPath & """", 0, False
Else
    WshShell.CurrentDirectory = currentDir
    WshShell.Run """" & currentDir & "\Chay_Vietlott_PC.bat""", 1, False
End If
