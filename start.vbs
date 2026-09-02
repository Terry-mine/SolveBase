' Silent launcher for SolveBase.
' Runs start.bat in silent mode with no visible console window.
' Comments kept ASCII on purpose: .vbs is read with the system ANSI codepage.

Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
root = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = root
sh.Run """" & root & "\start.bat"" silent", 0, False
