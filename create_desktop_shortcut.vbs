' create_desktop_shortcut.vbs
' Creates a Windows desktop shortcut for Image Compressor.
' Double-click this file once to create the shortcut, then delete it if you like.
'
' Expects these three files to be together in the SAME folder:
'   image_compressor_gui.pyw   (the app - .pyw so no console window pops up)
'   app_icon.ico                (the icon)
'   create_desktop_shortcut.vbs (this file)

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
appPath   = scriptDir & "\image_compressor_gui.pyw"
iconPath  = scriptDir & "\app_icon.ico"
desktop   = shell.SpecialFolders("Desktop")
shortcutPath = desktop & "\Image Compressor.lnk"

' Find pythonw.exe (no console window) via the 'py' launcher first, fall back to PATH
pythonwPath = ""

On Error Resume Next
result = shell.Exec("py -3 -c ""import sys; print(sys.executable)""")
Do While result.Status = 0
    WScript.Sleep 50
Loop
outText = result.StdOut.ReadAll()
On Error Goto 0

If InStr(outText, ".exe") > 0 Then
    exePath = Trim(outText)
    pythonwPath = Replace(exePath, "python.exe", "pythonw.exe")
    If Not fso.FileExists(pythonwPath) Then
        pythonwPath = exePath ' fall back to python.exe if pythonw not found
    End If
Else
    pythonwPath = "pythonw.exe" ' rely on PATH
End If

If Not fso.FileExists(appPath) Then
    MsgBox "Could not find image_compressor_gui.pyw next to this script." & vbCrLf & _
           "Make sure all files are in the same folder:" & vbCrLf & scriptDir, vbExclamation, "Setup"
    WScript.Quit 1
End If

Set link = shell.CreateShortcut(shortcutPath)
link.TargetPath = pythonwPath
link.Arguments = """" & appPath & """"
link.WorkingDirectory = scriptDir
If fso.FileExists(iconPath) Then
    link.IconLocation = iconPath
End If
link.Description = "Compress images with Pillow"
link.WindowStyle = 1
link.Save

MsgBox "Desktop shortcut 'Image Compressor' created!" & vbCrLf & vbCrLf & _
       "Using Python at: " & pythonwPath, vbInformation, "Done"
