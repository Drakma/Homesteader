Set-Location C:\Users\casey\Desktop\Homesteader
Select-String -Path "Homesteader\Assets\Resources\HUDTree\HudUI.uxml" -Pattern "name=.View" | Select-Object LineNumber, Line
