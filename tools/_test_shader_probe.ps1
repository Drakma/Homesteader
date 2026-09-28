Set-Location C:\Users\casey\Desktop\Homesteader
$s = @"
using UnityEngine;
public class TestShaderProbe
{
    public static void Probe()
    {
        string[] shaderNames = new[]
        {
            "Universal Render Pipeline/Particles/Unlit",
            "Particles/Standard Unlit",
            "Particles/Alpha Blended",
            "Sprites/Default",
            "UI/Default"
        };
        foreach (var name in shaderNames)
        {
            var sh = Shader.Find(name);
            Debug.Log($"Shader probe: {name} => {(sh != null ? sh.name : "NULL")}");
        }
    }
}
"@
