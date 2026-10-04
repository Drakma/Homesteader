Shader "Homesteader/PathSurface"
{
    // The surface of a built path or road (PathRun.cs): a ribbon draped on the ground whose soft, ragged edge comes from the ALPHA of _BaseMap
    // (u across the ribbon, v along it), and whose colour is made from the pixel's place in the WORLD: the tint times a fine grain, a slow
    // blotching at two sizes (value noise, so it never repeats) and, for stone, the joints between flagstones. Because the colour depends only on
    // where a pixel is and not on which ribbon it belongs to, two routes of the same kind that cross or join show one continuous surface: the
    // fading edge of the one on top melts into the other with no seam, no line and no change of grain.
    Properties
    {
        _BaseMap ("Edge (alpha = coverage)", 2D) = "white" {}
        _BaseColor ("Colour", Color) = (0.6, 0.58, 0.5, 1)
        _GrainAmt ("Grain strength (0 = flat)", Float) = 1
        _Flags ("Flagstone joints (stone)", Float) = 0
        _Gloss ("Gloss", Range(0, 1)) = 0.05
    }

    SubShader
    {
        Tags { "RenderType"="Transparent" "RenderPipeline"="UniversalPipeline" "Queue"="Transparent-1" }
        LOD 100

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode"="UniversalForward" }
            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
            ZTest LEqual
            Cull Off

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.5
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fragment _ _SHADOWS_SOFT
            #pragma multi_compile_fog

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "HomesteaderSky.hlsl"

            TEXTURE2D(_BaseMap);  SAMPLER(sampler_BaseMap);

            CBUFFER_START(UnityPerMaterial)
                half4 _BaseColor;
                float _GrainAmt;
                float _Flags;
                float _Gloss;
            CBUFFER_END

            float4 _WeatherGroundEffects;  // (snow coverage, ground wetness, rain, -)

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS   : NORMAL;
                float2 uv         : TEXCOORD0;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float3 normalWS   : TEXCOORD1;
                float2 uv         : TEXCOORD2;
                float  fogFactor  : TEXCOORD3;
            };

            float PHash(float2 p)
            {
                p = frac(p * float2(123.34, 456.21));
                p += dot(p, p + 45.32);
                return frac(p.x * p.y);
            }

            float PNoise(float2 p)
            {
                float2 i = floor(p), f = frac(p);
                f = f * f * (3.0 - 2.0 * f);
                return lerp(lerp(PHash(i), PHash(i + float2(1, 0)), f.x), lerp(PHash(i + float2(0, 1)), PHash(i + float2(1, 1)), f.x), f.y);
            }

            Varyings vert(Attributes input)
            {
                Varyings o;
                VertexPositionInputs p = GetVertexPositionInputs(input.positionOS.xyz);
                o.positionCS = p.positionCS;
                o.positionWS = p.positionWS;
                o.normalWS = TransformObjectToWorldNormal(input.normalOS);
                o.uv = input.uv;
                o.fogFactor = ComputeFogFactor(p.positionCS.z);
                return o;
            }

            half4 frag(Varyings input) : SV_Target
            {
                half coverage = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, input.uv).a;
                float2 w = input.positionWS.xz;
                // a fine grain (2.5 cm), a mid blotching (about 60 cm) and a slow one (about 3 m); the fine one fades out where a pixel covers many grains
                float fine = (PHash(floor(w * 40.0)) - 0.5) * 0.20 * saturate(1.5 - length(fwidth(w * 40.0)));
                float mid = (PNoise(w * 1.7) - 0.5) * 0.16;
                float slow = (PNoise(w * 0.33 + 17.0) - 0.5) * 0.14;
                half3 col = _BaseColor.rgb * (1.0 + (fine + mid + slow) * _GrainAmt);
                float2 jf = frac(w * 2.0);   // flagstones half a metre apart
                col *= 1.0 - _Flags * _GrainAmt * 0.3 * saturate(step(jf.x, 0.03) + step(jf.y, 0.03));
                col *= 1.0 - 0.22 * saturate(_WeatherGroundEffects.y);   // wet ground is darker
                float3 n = normalize(input.normalWS);
                float4 shadowCoord = TransformWorldToShadowCoord(input.positionWS);
                Light mainLight = GetMainLight(shadowCoord);
                half ndl = saturate(dot(n, mainLight.direction));
                half3 lit = mainLight.color * (ndl * mainLight.shadowAttenuation);
                half3 ambient = SampleSH(n);
                half3 outCol = col * (lit + ambient) * CloudShadowFactor(input.positionWS);
                outCol = MixFog(outCol, input.fogFactor);
                return half4(outCol, coverage * _BaseColor.a);
            }
            ENDHLSL
        }
    }
    FallBack Off
}
