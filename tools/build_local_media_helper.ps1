# Builds the Local media helper (Windows SMTC reader) into Homesteader/Assets/StreamingAssets/LocalMedia.
# Needs the .NET 8 SDK to build and the .NET 8 desktop runtime on the machine that runs the game.
# Not checked in; run once per machine:  powershell tools/build_local_media_helper.ps1
$root = Split-Path $PSScriptRoot -Parent
dotnet publish "$PSScriptRoot/LocalMediaHelper/LocalMediaHelper.csproj" -c Release -o "$root/Homesteader/Assets/StreamingAssets/LocalMedia" --self-contained false
