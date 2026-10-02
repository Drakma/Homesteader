Shader "Homesteader/GrassGpu"
{
    // GPU-instanced counterpart to Homesteader/Grass: instead of pre-baked world-space vertices, this reads
    // one GrassInstance per SV_InstanceID from a StructuredBuffer (filled by GrassInstanceGen.compute) and
    // builds the blade's world transform in the vertex shader. Visuals (wind, colour, flowers, cel lighting)
    // match the old shader exactly - only how each blade gets its position/rotation differs.
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
            // Real (wall-clock) time, set by RealTimeClock - unaffected by pausing/timeScale.
            float _RealTime;
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 4.5

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "HomesteaderSky.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _BaseColor;
                half4 _TipColor;
                float _WindStrength;
            CBUFFER_END

            float4 _GrassWindParams; // (dirX, dirZ, speed, gust)

            struct GrassInstance
            {
                float3 position;
                float rotationY;
                float height;
                float tint;
                float flower;
                float _pad;
            };
            StructuredBuffer<GrassInstance> _Instances;

            struct Attributes
            {
                float4 positionOS : POSITION; // unit blade: x in [-1,1], y in [0,1] (bottom to tip)
                float3 normalOS   : NORMAL;
                float2 uv         : TEXCOORD0;
                uint   instanceID : SV_InstanceID;
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

            static const float BladeWidth = 0.04;

            Varyings vert(Attributes input)
            {
                Varyings output;

                GrassInstance inst = _Instances[input.instanceID];

                float s = sin(inst.rotationY), c = cos(inst.rotationY);
                float lx = input.positionOS.x * (BladeWidth * 0.5);
                float ly = input.positionOS.y * inst.height;
                float rx = lx * c - 0 * s;
                float rz = lx * s + 0 * c;
                float3 posWS = inst.position + float3(rx, ly, rz);
                float3 normWS = normalize(float3(input.normalOS.x * c, input.normalOS.y, input.normalOS.x * s));

                float tint = inst.tint;
                float flower = inst.flower;

                float heightFrac = input.uv.y;
                output.heightFrac = heightFrac;

                float windPhase = _RealTime * _GrassWindParams.z * 0.5 + GrassHash(inst.position.xz) * 6.28;
                float windAmt = sin(windPhase) * _WindStrength * _GrassWindParams.w;
                float2 windDir = normalize(_GrassWindParams.xz + float2(0.001, 0.001));
                float windBend = heightFrac * heightFrac * windAmt * 0.4;
                posWS.x += windDir.x * windBend;
                posWS.z += windDir.y * windBend;

                float phase = GrassHash(inst.position.xz + 7.3) * 6.28;
                posWS.x += sin(_RealTime * 2.0 + phase) * heightFrac * 0.03;

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

                float3 normWS = normalize(input.normalWS);
                Light mainLight = GetMainLight();
                float ndotl = max(0.0, dot(normWS, mainLight.direction));
                float celLight = step(0.12, ndotl) * 0.35 + step(0.45, ndotl) * 0.35 + 0.3;
                half3 litColor = saturate(mainLight.color);
                litColor = max(litColor, (half3)(unity_AmbientSky.rgb * 0.9));
                half3 finalRGB = col * (litColor * celLight) * CloudShadowFactor(input.positionWS);

                return half4(finalRGB, 1.0);
            }
            ENDHLSL
        }
    }
    FallBack "Hidden/Universal Render Pipeline/FallbackError"
}
