Shader "Homesteader/HoverOutline"
{
    // Inverted-hull outline: renders a scaled-up back-face copy of the mesh
    // in a solid unlit glow color. Applied to a duplicate child renderer
    // sitting on top of the real mesh (see HoverOutline.cs) rather than
    // replacing the object's own material, so it works on any glTFast-loaded
    // GLB without touching its generated materials.
    Properties
    {
        _OutlineColor ("Outline Color", Color) = (0.35, 0.9, 1.0, 1)
        _OutlineWidth ("Outline Width (object space)", Range(0, 0.1)) = 0.02
        _PulseSpeed ("Pulse Speed", Range(0, 10)) = 2.5
        _PulseAmount ("Pulse Amount", Range(0, 1)) = 0.35
    }

    SubShader
    {
        Tags { "RenderType"="Transparent" "RenderPipeline"="UniversalPipeline" "Queue"="Transparent" }
        LOD 100

        Pass
        {
            Name "OutlineHull"
            Tags { "LightMode"="UniversalForward" }

            Cull Front
            ZWrite Off
            Blend SrcAlpha OneMinusSrcAlpha

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS   : NORMAL;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
            };

            CBUFFER_START(UnityPerMaterial)
                float4 _OutlineColor;
                float _OutlineWidth;
                float _PulseSpeed;
                float _PulseAmount;
            CBUFFER_END

            Varyings vert(Attributes IN)
            {
                Varyings OUT;
                float pulse = 1.0 + sin(_Time.y * _PulseSpeed) * _PulseAmount;
                float3 expanded = IN.positionOS.xyz + normalize(IN.normalOS) * (_OutlineWidth * pulse);
                OUT.positionCS = TransformObjectToHClip(expanded);
                return OUT;
            }

            half4 frag(Varyings IN) : SV_Target
            {
                return _OutlineColor;
            }
            ENDHLSL
        }
    }
}
