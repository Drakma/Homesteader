$unity = Get-Process -Name Unity -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -ne '' } | Select-Object -First 1
if (-not $unity) {
    Write-Host "No active Unity Editor window found."
    exit 0
}

Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class WinRef {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int n);
    [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr hWnd);
}
"@

$hwnd = $unity.MainWindowHandle
[WinRef]::ShowWindow($hwnd, 9) | Out-Null
[WinRef]::BringWindowToTop($hwnd) | Out-Null
[WinRef]::SetForegroundWindow($hwnd) | Out-Null

Write-Host "Focused Unity window: $($unity.MainWindowTitle)"

