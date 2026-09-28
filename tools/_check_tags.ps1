Set-Location C:\Users\casey\Desktop\Homesteader
$scene = "Homesteader\Assets\Scenes\SampleScene.unity"
Select-String -Path $scene -Pattern "m_TagString"
