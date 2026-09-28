Shader "Homesteader/WaterSurface"
{
    Properties
    {
        _WaterMask ("Water Mask (R=depth, G=water flag)", 2D) = "white" {}
        _TerrainBounds ("Terrain Bounds (X, Z, Height, 0)", Vector) = (500.0, 500.0, 60.0, 0.0)
        _BaseColor ("Base Water Color", Color) = (0.04, 0.18, 0.32, 0.88)
        _DeepDarken ("Deep Darken Amount", Range(0, 1)) = 0.6
        _RippleAmplitude ("Ripple Amplitude", Range(0, 0.3)) = 0.12
        _RippleFrequency ("Ripple Frequency", Range(0.5, 5.0)) = 1.8
        _FoamWidth ("Foam Width (metres)", Range(0.3, 3.0)) = 0.8
        _FoamColor ("Foam Color", Color) = (0.85, 0.92, 0.98, 1.0)
    }

    SubShader
    {
        Tags { "RenderType"="Transparent" "RenderPipeline"="UniversalPipeline" "Queue"="Transparent" }
        LOD 200

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode"="UniversalForward" }

            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
            Cull Back

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE
            #pragma multi_compile _ _SHADOWS_SOFT

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            struct Attributes
            {
                float4 positionOS : POSITION;
                float2 uv         : TEXCOORD0;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float2 uv         : TEXCOORD1;
            };

            TEXTURE2D(_WaterMask);
            SAMPLER(sampler_WaterMask);

            CBUFFER_START(UnityPerMaterial)
                float4 _TerrainBounds;
                half4 _BaseColor;
                float _DeepDarken;
                float _RippleAmplitude;
                float _RippleFrequency;
                float _FoamWidth;
                half4 _FoamColor;
            CBUFFER_END

            // Hash-based value noise for ripples (GPU-side, cheap)
            float hash21(float2 p)
            {
                return frac(sin(dot(p, float2(127.1, 311.7))) * 43758.5453);
            }

            float valueNoise2D(float2 p)
            {
                float2 i = floor(p);
                float2 f = frac(p);
                float2 u = f * f * (3.0 - 2.0 * f);
                return lerp(lerp(hash21(i), hash21(i + float2(1, 0)), u.x),
                            lerp(hash21(i + float2(0, 1)), hash21(i + float2(1, 1)), u.x), u.y);
            }

            Varyings vert(Attributes input)
            {
                Varyings output;
                float3 posOS = input.positionOS.xyz;

                // Vertex displacement: animated ripples (two layers for directional + cross flow)
                float t = _Time.y;
                float ripple1 = sin(posOS.x * 1.2 * _RippleFrequency + t * 1.8) * 0.5
                              + cos(posOS.z * 0.9 * _RippleFrequency - t * 1.5) * 0.5;
                float ripple2 = sin(posOS.x * 2.5 * _RippleFrequency + t * 2.3) * 0.15
                              + sin(posOS.z * -1.8 * _RippleFrequency + t * 2.3) * 0.15;
                float ripple3 = valueNoise2D(posOS.xz * 0.8 + t * 0.3) * 0.4 - 0.2;
                float displacement = (ripple1 + ripple2 + ripple3) * _RippleAmplitude;

                posOS.y += displacement;

                float3 posWS = TransformObjectToWorld(posOS);
                output.positionWS = posWS;
                output.positionCS = TransformWorldToHClip(posWS);
                output.uv = input.uv;
                return output;
            }

            half4 frag(Varyings input) : SV_Target
            {
                float3 posWS = input.positionWS;
                float2 uv = input.uv;

                // Sample water mask: R = depth (0-1), G = water flag
                float4 mask = SAMPLE_TEXTURE2D(_WaterMask, sampler_WaterMask, uv);
                if (mask.g < 0.5) discard;
                float depth = mask.r; // 0 = shallow, 1 = deep

                // Edge distance: sample neighbors to find how close we are to the shore
                float2 texelSize = float2(1.0 / _TerrainBounds.x, 1.0 / _TerrainBounds.y);
                float edgeDist = 999.0;
                [unroll]
                for (int r = 1; r <= 4; r++)
                {
                    [unroll]
                    for (int a = 0; a < 8; a++)
                    {
                        float ang = a * 0.785; // 45 degrees
                        float2 offset = float2(cos(ang), sin(ang)) * r * texelSize;
                        float s = SAMPLE_TEXTURE2D(_WaterMask, sampler_WaterMask, uv + offset).g;
                        if (s < 0.5)
                        {
                            float d = length(offset) * _TerrainBounds.x;
                            edgeDist = min(edgeDist, d);
                        }
                    }
                    if (edgeDist < 999.0) break;
                }

                // Single base color, darkened by depth
                half4 waterCol = _BaseColor;
                waterCol.rgb *= (1.0 - depth * _DeepDarken);

                // Flowing directional ripples in the fragment shader (subtle color variation)
                float flow = sin(posWS.x * 0.4 + posWS.z * 1.1 + _Time.y * 1.8) * 0.5
                           + cos(posWS.z * 1.3 - posWS.x * 0.3 - _Time.y * 2.2) * 0.5;
                waterCol.rgb = lerp(waterCol.rgb * 0.85, waterCol.rgb * 1.15, saturate(flow * 0.3 + 0.4));

                // Celestial reflection: specular highlight from the main light
                Light mainLight = GetMainLight();
                float3 viewDir = normalize(_WorldSpaceCameraPos - posWS);
                // Perturb normal with the same ripple function
                float nx = cos(posWS.x * 1.2 * _RippleFrequency + _Time.y * 1.8) * 0.15;
                float nz = sin(posWS.z * 0.9 * _RippleFrequency - _Time.y * 1.5) * 0.15;
                float3 normal = normalize(float3(nx, 1.0, nz));

                float3 halfDir = normalize(viewDir + mainLight.direction);
                float spec = pow(max(0.0, dot(normal, halfDir)), 64.0);
                half3 reflection = mainLight.color * spec * 0.6;
                waterCol.rgb += reflection;

                // Foam at edges
                float foamMask = saturate(1.0 - edgeDist / _FoamWidth);
                foamMask = smoothstep(0.0, 0.5, foamMask);
                float foamNoise = valueNoise2D(posWS.xz * 3.0 + _Time.y * 0.5);
                foamMask *= (0.6 + foamNoise * 0.4);
                waterCol.rgb = lerp(waterCol.rgb, _FoamColor.rgb, foamMask * _FoamColor.a);
                waterCol.a = max(waterCol.a, foamMask);

                // Simple cel lighting
                float ndotl = max(0.0, dot(normal, mainLight.direction));
                float celLight = step(0.12, ndotl) * 0.35 + step(0.45, ndotl) * 0.35 + 0.3;
                waterCol.rgb *= celLight;

                return waterCol;
            }
            ENDHLSL
        }
    }
    FallBack "Hidden/Universal Render Pipeline/FallbackError"
}
