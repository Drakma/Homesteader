Set-Location C:\Users\casey\Desktop\Homesteader
$scene = "Homesteader\Assets\Scenes\SampleScene.unity"
Select-String -Path $scene -Pattern "Camera" | Select-Object -First 10
Select-String -Path $scene -Pattern "m_Orthographic" | Select-Object -First 5
