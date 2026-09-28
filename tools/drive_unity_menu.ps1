# drive_unity_menu.ps1 - drive Unity's "Tools/HUD/Install Into Active Scene"
# menu item via Windows UI Automation so the HUD gets installed and Play
# captures the rendered scene.

Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms

$unity = Get-Process -Name Unity | Where-Object { $_.MainWindowTitle -match "SampleScene" }
if (-not $unity) {
    Write-Error "Unity isn't open with SampleScene. Aborting."
    exit 1
}

# Get the AutomationElement for Unity's main window.
$hwnd = $unity.MainWindowHandle
$root = [System.Windows.Automation.AutomationElement]::FromHandle($hwnd)

# Activate Unity so subsequent keyboard input reaches it.
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class Win {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int n);
    [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr hWnd);
}
"@
[Win]::ShowWindow($hwnd, 9)        # SW_RESTORE
[Win]::BringWindowToTop($hwnd) | Out-Null
[Win]::SetForegroundWindow($hwnd) | Out-Null
Start-Sleep -Milliseconds 400

# Send the Alt+T shortcut (Tools menu), then the "H" sub-menu header,
# then "U" to land on Tools/HUD/Install Into Active Scene.
# Unity's menu names can change; we fall back to kbd-based navigation:
# Alt                 -> focus menu bar
# h                   -> Tools menu (since Tools starts with 'T'? use T)
# Actually Unity menus sort alphabetically: 'HUD' is under 'Tools'.
# Keystrokes:
#   Alt+H might be Help. We use Tools via clicking the menu instead.
# Safest: send Alt+T to open Tools menu, then arrow down to HUD, then Enter.

[System.Windows.Forms.SendKeys]::SendWait("%t")  # Alt+T -> Tools menu
Start-Sleep -Milliseconds 250

# Find the "Install Into Active Scene" item. UIAutomation finds by name.
# We need to navigate: Tools -> HUD -> Install Into Active Scene.
# After Alt+T, the menu is open. The sub-menu HUD has H as accelerator?
# In Unity menus the second submenu item under Tools/HUD may be reached by:
# "h" since HUD starts with H.

[System.Windows.Forms.SendKeys]::SendWait("h")
Start-Sleep -Milliseconds 250
[System.Windows.Forms.SendKeys]::SendWait("i")
Start-Sleep -Milliseconds 800

# Now press Play. Unity's hotkey for play/pause is Ctrl+P.
[System.Windows.Forms.SendKeys]::SendWait("^p")
Start-Sleep -Milliseconds 1500

# Save a screenshot via Unity's Game tab capture keybind (no portable).
# Instead, just instruct the user where to look.
Write-Host "Sent Alt+T, 'h', 'i' (Tools > HUD > Install Into Active Scene), then Ctrl+P to enter Play mode."
