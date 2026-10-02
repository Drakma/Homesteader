Shader "Homesteader/Vegetation"
{
    // Flat-shaded lit shader for the procedural world dressing (trees, rocks, cattails, flowers, tufts).
    //  - Wind: vertices sway downwind by height above the object's base, using the global _GrassWindParams
    //    (dirX, dirZ, speed, gust) that WeatherEffectsManager sets, so storms bend everything harder.
    //  - Seasons: VegetationSeasons drives _BaseColor (leaf / straw colour) and _Grow (0 = gone, 1 = full)
    //    per material. Growth scales the mesh about (0, _GrowPivotY, 0), so leaves shrink away in place.
    //  - Weather: global _WeatherGroundEffects (snow, wetness) whitens upward faces and darkens when wet.
    Properties
    {
        _BaseColor ("Base Color", Color) = (0.3, 0.6, 0.25, 1)
        _SwayAmp ("Sway Amplitude (m at full height)", Float) = 0
        _SwayRef ("Sway Reference Height (m)", Float) = 1
        _Grow ("Grow", Range(0, 1)) = 1
        _GrowPivotY ("Grow Pivot Y", Float) = 0
        _FocusFade ("Fade With View Distance (small plants)", Float) = 0
        _Spots ("Dark bark marks (birch)", Float) = 0
        _SpotColor ("Mark Color", Color) = (0.1, 0.1, 0.1, 1)
        _LeafLoss ("Crown Fade (0 = every crown, 1 = none; each tree goes at its own random point)", Range(0, 1)) = 0
        _SnowAmount ("Snow Receptiveness", Range(0, 1)) = 1
        _AgeStages ("Stage ends (days), w=1 to age", Vector) = (15, 40, 75, 0)
    }

    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        LOD 100

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
        #include "HomesteaderSky.hlsl"

        CBUFFER_START(UnityPerMaterial)
            half4 _BaseColor;
            float _SwayAmp;
            float _SwayRef;
            float _Grow;
            float _GrowPivotY;
            float _FocusFade;
            float _Spots;
            half4 _SpotColor;
            float _LeafLoss;
            float _SnowAmount;
            float4 _AgeStages;
        CBUFFER_END

        // Real (wall-clock) time, set by RealTimeClock - unaffected by pausing/timeScale.
        float _RealTime;
        float4 _GrassWindParams;       // (dirX, dirZ, speed, gust)
        float4 _WeatherGroundEffects;  // (snow coverage, ground wetness, rain, -)
        float _VegDay;                 // absolute game day, set by VegetationSeasons
        float _WindSwayOff;            // set globally by Settings > Graphics > Wind Animation (0 = sway on, the default)
        float _VegWindPhase;          // accumulated sway phase, advanced by VegetationSeasons at the current wind speed
        float4 _VegFocus;              // (view-centre x, z, fade start m, fade end m), set by VegetationFocusFade

        float VegHash(float2 p)
        {
            return frac(sin(dot(p, float2(127.1, 311.7))) * 43758.5453);
        }

        // Tree growth: four stages (sapling, small, medium, mature) sized 16 / 35 / 65 / 100 percent, with the stage
        // windows in _AgeStages (taken from the asset kit's growth group). w = 0 means "not a growing thing".
        float VegAgeScale(float birth)
        {
            if (_AgeStages.w < 0.5) return 1.0;
            float age = _VegDay - birth;
            float4 st = _AgeStages;
            float sc = 0.16;
            sc += 0.19 * smoothstep(st.x - 1.0, st.x + 1.0, age);
            sc += 0.30 * smoothstep(st.y - 1.0, st.y + 1.0, age);
            sc += 0.35 * smoothstep(st.z - 1.0, st.z + 1.0, age);
            return sc;
        }

        // Vertices are baked in WORLD space (see ProceduralVegetation.Combine). UV1 = the source object origin x,z;
        // UV2 = its origin y and uniform scale; UV3.x = birth day. Grows/shrinks about the object's own pivot and sways
        // it by height above its base. Returns the world position.
        float3 VegWorldPos(float3 positionOS, float2 uv1, float2 uv2, float2 uv3, bool windSway = true)
        {
            float3 o = float3(uv1.x, uv2.x, uv1.y);
            float ageScale = VegAgeScale(uv3.x);
            float baseScale = max(uv2.y, 0.0001);
            float s = baseScale * ageScale;

            float3 rel = positionOS - o;
            rel *= ageScale;
            rel.y -= _GrowPivotY * s;
            // Each tree's crown has its own random moment to go: _LeafLoss (0..1, driven by the season) passes a per-tree threshold and that
            // crown shrinks away quickly (and grows back at its own moment in spring). Whole crowns, tree by tree, not the whole forest at once.
            float crownFade = 1.0;
            if (_LeafLoss > 0.001)
                crownFade = 1.0 - smoothstep(0.05 + VegHash(o.xz) * 0.85 - 0.04, 0.05 + VegHash(o.xz) * 0.85 + 0.04, _LeafLoss);
            rel *= _Grow * crownFade;
            rel.y += _GrowPivotY * s;
            // Small plants shrink away with distance from the centre of the view (not from the player), see VegetationFocusFade.
            float focusScale = 1.0;
            if (_FocusFade > 0.5)
                focusScale = 1.0 - smoothstep(_VegFocus.z, _VegFocus.w, distance(o.xz, _VegFocus.xy));
            rel *= focusScale;
            float3 posWS = TransformObjectToWorld(o + rel);

            if (windSway && _SwayAmp > 0.0001 && _WindSwayOff < 0.5)
            {
                float h = saturate((positionOS.y - o.y) * ageScale / max(_SwayRef * baseScale, 0.01));
                h *= h;
                float speed = _GrassWindParams.z;
                float gust = _GrassWindParams.w;
                // The phase is ACCUMULATED on the CPU (speed changes only change how fast it advances). Computing it as
                // time * speed here made the phase jump whenever the wind speed changed, and everything shook.
                float t = _VegWindPhase + VegHash(o.xz) * 6.2831;
                float sway = sin(t) + 0.5 * sin(t * 2.3 + 1.7);
                float amt = (0.25 + gust * 1.3) * sway * _SwayAmp * s * h * _Grow * focusScale * crownFade;
                float2 dir = normalize(_GrassWindParams.xz + float2(0.001, 0.001));
                posWS.xz += dir * amt;
                posWS.xz += float2(-dir.y, dir.x) * amt * 0.25;
            }
            return posWS;
        }
        ENDHLSL

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode"="UniversalForward" }

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.5
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fragment _ _SHADOWS_SOFT

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS   : NORMAL;
                float2 uv1        : TEXCOORD1;
                float2 uv2        : TEXCOORD2;
                float2 uv3        : TEXCOORD3;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float3 normalWS   : TEXCOORD1;
                float3 baseWS     : TEXCOORD2;   // the un-swayed (baked) position, so marks do not swim with the wind
            };

            Varyings vert(Attributes input)
            {
                Varyings o;
                float3 posWS = VegWorldPos(input.positionOS.xyz, input.uv1, input.uv2, input.uv3);
                o.positionWS = posWS;
                o.positionCS = TransformWorldToHClip(posWS);
                o.normalWS = TransformObjectToWorldNormal(input.normalOS);
                o.baseWS = input.positionOS.xyz;
                return o;
            }

            half4 frag(Varyings input) : SV_Target
            {
                float3 n = normalize(input.normalWS);
                half3 col = _BaseColor.rgb;

                // Dark horizontal marks on the bark (birch): cells flat in y and wide round the trunk, hashed per cell.
                if (_Spots > 0.5)
                {
                    float3 q = input.baseWS * float3(3.2, 7.0, 3.2);
                    float h = frac(sin(dot(floor(q), float3(127.1, 311.7, 74.7))) * 43758.5453);
                    float2 f = frac(q.xy + q.zz * 0.0);
                    float inside = step(0.12, frac(q.y)) * step(frac(q.y), 0.62) * step(0.1, frac(q.x + q.z)) * step(frac(q.x + q.z), 0.85);
                    col = lerp(col, _SpotColor.rgb, step(0.72, h) * inside);
                }

                // Snow settles on upward faces; rain darkens.
                float snow = saturate(_WeatherGroundEffects.x) * _SnowAmount * saturate(n.y * 1.4 - 0.15);
                col = lerp(col, half3(0.93, 0.95, 0.98), snow);
                col *= 1.0 - 0.22 * saturate(_WeatherGroundEffects.y);

                float4 shadowCoord = TransformWorldToShadowCoord(input.positionWS);
                Light mainLight = GetMainLight(shadowCoord);
                half ndl = saturate(dot(n, mainLight.direction));
                half3 lit = mainLight.color * (ndl * mainLight.shadowAttenuation);
                half3 ambient = SampleSH(n);
                return half4(col * (lit + ambient) * CloudShadowFactor(input.positionWS), 1);
            }
            ENDHLSL
        }

        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode"="ShadowCaster" }
            ZWrite On
            ZTest LEqual
            ColorMask 0

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.5

            float3 _LightDirection;

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS   : NORMAL;
                float2 uv1        : TEXCOORD1;
                float2 uv2        : TEXCOORD2;
                float2 uv3        : TEXCOORD3;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
            };

            Varyings vert(Attributes input)
            {
                Varyings o;
                // Same sway as the visible mesh, so a swaying crown never slides in and out of its own shadow (flicker).
                float3 posWS = VegWorldPos(input.positionOS.xyz, input.uv1, input.uv2, input.uv3);
                float3 nWS = TransformObjectToWorldNormal(input.normalOS);
                float4 cs = TransformWorldToHClip(ApplyShadowBias(posWS, nWS, _LightDirection));
                #if UNITY_REVERSED_Z
                    cs.z = min(cs.z, UNITY_NEAR_CLIP_VALUE);
                #else
                    cs.z = max(cs.z, UNITY_NEAR_CLIP_VALUE);
                #endif
                o.positionCS = cs;
                return o;
            }

            half4 frag(Varyings input) : SV_Target { return 0; }
            ENDHLSL
        }

        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode"="DepthOnly" }
            ZWrite On
            ColorMask R

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.5

            struct Attributes { float4 positionOS : POSITION; float2 uv1 : TEXCOORD1; float2 uv2 : TEXCOORD2; float2 uv3 : TEXCOORD3; };
            struct Varyings { float4 positionCS : SV_POSITION; };

            Varyings vert(Attributes input)
            {
                Varyings o;
                o.positionCS = TransformWorldToHClip(VegWorldPos(input.positionOS.xyz, input.uv1, input.uv2, input.uv3));
                return o;
            }

            half frag(Varyings input) : SV_Target { return input.positionCS.z; }
            ENDHLSL
        }
    }
}
