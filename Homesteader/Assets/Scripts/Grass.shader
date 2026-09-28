Shader "Homesteader/Grass"
{
    Properties
    {
        _BaseColor ("Base Color", Color) = (0.20, 0.65, 0.28, 1)
        _TipColor ("Tip Color", Color) = (0.35, 0.78, 0.35, 1)
        _WindStrength ("Wind Strength", Range(0, 1)) = 0.3
    }

    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" }
        LOD 100
        Cull Off

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode"="UniversalForward" }

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.5

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _BaseColor;
                half4 _TipColor;
                float _WindStrength;
            CBUFFER_END

            // Global wind vector: (dirX, dirZ, speed, gust)
            float4 _GrassWindParams;

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS   : NORMAL;
                float2 uv         : TEXCOORD0;
                float2 uv2        : TEXCOORD1; // x=tint, y=flower
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float3 normalWS   : TEXCOORD1;
                float2 uv         : TEXCOORD2;
                float  heightFrac : TEXCOORD3;
                float  tint       : TEXCOORD4;
                float  flower     : TEXCOORD5;
            };

            float GrassHash(float2 p)
            {
                return frac(sin(dot(p, float2(127.1, 311.7))) * 43758.5453);
            }

            Varyings vert(Attributes input)
            {
                Varyings output;

                // Vertices are pre-baked at world positions in the combined mesh.
                // positionOS IS world position (mesh is at origin, no transform).
                float3 posWS = input.positionOS.xyz;
                float3 normWS = input.normalOS;

                // Per-blade data from UV2
                float tint = input.uv2.x;
                float flower = input.uv2.y;

                // Wind sway: more at the top
                float heightFrac = input.uv.y;
                output.heightFrac = heightFrac;

                float windPhase = _Time.y * _GrassWindParams.z * 0.5 + GrassHash(posWS.xz) * 6.28;
                float windAmt = sin(windPhase) * _WindStrength * _GrassWindParams.w;
                float2 windDir = normalize(_GrassWindParams.xz + float2(0.001, 0.001));
                float windBend = heightFrac * heightFrac * windAmt * 0.4;
                posWS.x += windDir.x * windBend;
                posWS.z += windDir.y * windBend;

                // Per-blade phase variation
                float phase = GrassHash(posWS.xz + 7.3) * 6.28;
                posWS.x += sin(_Time.y * 2.0 + phase) * heightFrac * 0.03;

                output.positionWS = posWS;
                output.positionCS = TransformWorldToHClip(posWS);
                output.normalWS = normWS;
                output.uv = input.uv;
                output.tint = tint;
                output.flower = flower;
                return output;
            }

            half4 frag(Varyings input) : SV_Target
            {
                float hf = input.heightFrac;

                half3 col = lerp(_BaseColor.rgb, _TipColor.rgb, hf);
                col *= lerp(0.75, 1.15, input.tint);

                // Flower: color the tip
                if (input.flower > 0.5 && hf > 0.75)
                {
                    half3 fc;
                    int ftype = (int)input.flower;
                    if (ftype == 1)      fc = half3(0.95, 0.85, 0.25);
                    else if (ftype == 2) fc = half3(0.92, 0.35, 0.45);
                    else if (ftype == 3) fc = half3(0.75, 0.55, 0.95);
                    else if (ftype == 4) fc = half3(0.98, 0.98, 0.95);
                    else                 fc = half3(0.98, 0.65, 0.30);
                    col = lerp(col, fc, smoothstep(0.75, 0.95, hf));
                }

                // Cel-style lighting
                float3 normWS = normalize(input.normalWS);
                Light mainLight = GetMainLight();
                float ndotl = max(0.0, dot(normWS, mainLight.direction));
                float celLight = step(0.12, ndotl) * 0.35 + step(0.45, ndotl) * 0.35 + 0.3;
                half3 litColor = saturate(mainLight.color);
                litColor = max(litColor, (half3)(unity_AmbientSky.rgb * 0.9));
                half3 finalRGB = col * (litColor * celLight);

                return half4(finalRGB, 1.0);
            }
            ENDHLSL
        }
    }
    FallBack "Hidden/Universal Render Pipeline/FallbackError"
}
