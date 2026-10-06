Shader "Homesteader/GenerativeTerrainURP"
{
    Properties
    {
        _BiomeMap ("Biome Control Map (R=Mode, G=Moisture, B=Nutrients, A=Slope)", 2D) = "black" {}
        _RoadMask ("Road Mask (R=coverage, G=lateral offset)", 2D) = "black" {}
        _RoadParams ("Road Params (lateral range, half width)", Vector) = (6, 1.7, 0, 0)
        _BiomeBorderTex ("Biome Border Factor", 2D) = "black" {}
        _TerrainBounds ("Terrain Bounds (X, Z, Height, 0)", Vector) = (500.0, 500.0, 60.0, 0.0)
        _NormalStrength ("Facet Normal Strength", Range(0, 1)) = 0.25
        _NutrientDarkening ("Nutrient Soil Darkening", Range(0, 1)) = 0.35
        _GridColor ("Ground Grid Color", Color) = (0.90, 0.90, 0.90, 1)
        _GridLineWidth ("Ground Grid Line Width (m)", Range(0, 0.2)) = 0.031
        _GridOpacity ("Ground Grid Opacity", Range(0, 1)) = 1

    }

    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        LOD 200

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode"="UniversalForward" }

            HLSLPROGRAM
            // Real (wall-clock) time, set by RealTimeClock - unaffected by pausing/timeScale.
            float _RealTime;
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE
            #pragma multi_compile _ _SHADOWS_SOFT
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "HomesteaderSky.hlsl"

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
            };

            #include "HomesteaderTerrainProps.hlsl"
            #include "HomesteaderTerrainGround.hlsl"

            Varyings vert(Attributes input)
            {
                Varyings output;
                VertexPositionInputs vertexInput = GetVertexPositionInputs(input.positionOS.xyz);
                VertexNormalInputs normalInput = GetVertexNormalInputs(input.normalOS);

                output.positionCS = vertexInput.positionCS;
                output.positionWS = vertexInput.positionWS;
                output.normalWS = normalInput.normalWS;

                // Directly compute exact, normalized 0..1 UV coordinate from Terrain object-space bounds
                float mapSizeX = max(1.0, _TerrainBounds.x);
                float mapSizeZ = max(1.0, _TerrainBounds.y);
                output.uv = float2(input.positionOS.x / mapSizeX, input.positionOS.z / mapSizeZ);
                return output;
            }

            half4 frag(Varyings input) : SV_Target
            {
                float3 posWS = input.positionWS;
                float3 normWS = normalize(input.normalWS);
                float slope = 1.0 - max(0.0, normWS.y); // 0 = flat, 1 = vertical cliff

                float x = posWS.x;
                float z = posWS.z;

                half3 col = half3(0.20, 0.65, 0.28); // Default pasture meadow
                half3 cliffColor = half3(0.38, 0.40, 0.44); // Weathered granite bedrock

                // The baked biome map (written by HomesteaderTerrainGenerator.GenerateTerrain) is the
                // single source of truth for what grows where - it already ran the real biome
                // evaluation (water/wetland/lawn/farmland placement, elevation-based highlands, and
                // the domain-warped forest/meadow noise fields) once on the CPU. The shader's job is
                // just to decode and paint it, not to re-derive placement with its own noise.
                // A encodes (biomeMode + 0.5) / 18 (point-sampled: mode ids must never blend into
                // each other), RGB is the biome's actual tint color (bilinear-sampled below, so
                // adjacent biomes fade smoothly across their shared texel border instead of
                // stair-stepping). See HomesteaderTerrainGenerator.GenerateTerrain.
                float2 biomeUv = float2(x / _TerrainBounds.x, z / _TerrainBounds.y);
                half4 biomeSample = SAMPLE_TEXTURE2D(_BiomeMap, sampler_point_clamp, biomeUv);
                int biomeMode = (int)floor(biomeSample.a * 18.0);

                // Water is now rendered by a separate vertex-displaced water mesh (WaterSurface.shader).
                // The terrain shader just paints biome colors — under water, the baked biome map's
                // river/lake/pond tint shows through as the riverbed/pondbed color.
                //
                // isWater itself is still a hard, point-sampled switch (biomeMode ids can't blend), but the
                // COLOR either side of it doesn't have to snap with it: sample the same smoothly-blurred
                // coverage texture WaterSurface.shader fades its own alpha across, compute both the water-bed
                // color and the land color unconditionally, and lerp between them by that coverage. That's
                // what actually removes the visible seam - blending the branch condition itself is impossible
                // since mode ids are discrete, but blending its two outcomes isn't.
                bool isWater = (biomeMode >= 1 && biomeMode <= 3); // river=1, lake=2, pond=3
                bool isWetland = (biomeMode == 6);
                bool isLawn = !isWater && !isWetland && biomeMode == 5;
                bool isFarmland = !isWater && !isWetland && biomeMode == 4;

                // The ground colour (biome texture, soft biome blend, water bed and shore): sampled from the texture TerrainGroundBake.cs rendered once
                // when the world was made, or (until that exists) worked out here per pixel exactly as the bake does.
                float waterCoverage = SAMPLE_TEXTURE2D(_WaterMask, sampler_linear_clamp, biomeUv).g;
                [branch] if (_GroundBakeOn > 0.5)
                    col = SAMPLE_TEXTURE2D(_GroundBake, sampler_GroundBake, biomeUv).rgb;
                else
                    col = TerrainGroundBase(float2(x, z), biomeUv);

                // Automatic cliffs on steep slopes (for non-water)
                if (!isWater && slope > 0.38)
                {
                    col = cliffColor;
                }

                // The starter road, painted over whatever biome it crosses (before weather, so snow and rain reach it too).
                half4 road = SAMPLE_TEXTURE2D(_RoadMask, sampler_linear_clamp, biomeUv);
                if (road.r > 0.004)
                {
                    float roadCover = road.r * (1.0 - smoothstep(0.38, 0.55, slope)) * (1.0 - smoothstep(0.1, 0.5, waterCoverage));
                    col = lerp(col, RoadTexture(posWS.xz, road.g, road.r), roadCover);
                }

                // Global Weather Ground Effects (Wetness & Snow Accumulation)
                // _WeatherGroundEffects: (X = SnowCoverage [0..1], Y = GroundWetness [0..1], Z = reserved, W = reserved)
                float globalSnow = saturate(_WeatherGroundEffects.x);
                float globalWet = saturate(_WeatherGroundEffects.y);
                half3 puddleGlint = half3(0, 0, 0); // added after lighting so it stays a bright highlight
                float snowMask = 0.0; // how much of this pixel is snow-covered (drives neutral lighting below)

                // WEATHER REACHES THE SHORE. This block used to be gated on the hard, point-sampled `!isWater`
                // biome flag, so the whole river/pond biome - including the dirt shore band - skipped snow and
                // rain and stayed brown in a blocky per-texel outline while the land around it turned white.
                // It is now weighted by the smooth water coverage instead: full on land and on the bank
                // (coverage < ~0.35), fading out only where real water sits (>= ~0.6), so the shoreline takes
                // snow and wetness with a soft edge and the submerged bed stays clear.
                float weatherW = 1.0 - smoothstep(0.35, 0.6, waterCoverage);
                half3 colBeforeWeather = col;
                if (weatherW > 0.01)
                {
                    // Darken and enrich ground saturation when soaked with rain
                    if (globalWet > 0.01)
                    {
                        // 1) Progressive darkening: the ground darkens as it soaks (wetness rises slowly).
                        col = lerp(col, col * 0.52, smoothstep(0.0, 1.0, globalWet) * 0.9);

                        // 2) Puddles: appear once the ground is damp, start as small pools, grow, then
                        //    merge into larger ones. Only on flat ground.
                        float level = smoothstep(0.35, 1.0, globalWet);
                        float flatness = smoothstep(0.90, 0.985, normWS.y);
                        float2 pp = posWS.xz;
                        float pnSmall = SnowValueNoise(pp * 0.35) * 0.5 + SnowValueNoise(pp * 0.9) * 0.3 + SnowValueNoise(pp * 2.3) * 0.2;
                        float pnBig = SnowValueNoise(pp * 0.09) * 0.6 + SnowValueNoise(pp * 0.22) * 0.4;
                        float pn = lerp(pnSmall, pnBig, smoothstep(0.4, 0.9, level) * 0.6);
                        // Water collects in low ground first: hollows get a big head start, so as it rains
                        // puddles appear in the basins, then spread outward and uphill as the level rises,
                        // and retreat back into the basins as the ground dries.
                        float2 basinUv = (posWS.xz - _PuddleBasinRect.xy) * _PuddleBasinRect.zw;
                        float basin = SAMPLE_TEXTURE2D(_PuddleBasinTex, sampler_linear_clamp, basinUv).r;
                        basin *= step(1e-6, _PuddleBasinRect.z); // no map yet -> no bias
                        pn = pn - basin * 0.32 + 0.10;
                        float threshold = 0.28 + level * 0.22;
                        float puddle = saturate((threshold - pn) / 0.05) * flatness * smoothstep(0.0, 0.15, level);
                        puddle *= 1.0 - saturate(globalSnow * 2.0); // snow covers puddles

                        if (puddle > 0.001)
                        {
                            // Dark, cool, glossy water over the wet ground.
                            half3 pudCol = lerp(col * 0.30, half3(0.10, 0.15, 0.22), 0.55);

                            // Raindrop ripples: expanding rings on a jittered grid, only while it rains.
                            float rainNow = saturate(_WeatherGroundEffects.z);
                            float2 g = pp * 1.6;
                            float2 cell = floor(g);
                            float2 fcell = frac(g) - 0.5;
                            float2 rc = (float2(SnowHash(cell), SnowHash(cell + 7.3)) - 0.5) * 0.6;
                            float ph = frac(_RealTime * 0.9 + SnowHash(cell + 3.1));
                            float ring = (1.0 - smoothstep(0.0, 0.03, abs(length(fcell - rc) - ph * 0.45))) * (1.0 - ph);
                            pudCol += ring * rainNow * 0.22;

                            col = lerp(col, pudCol, puddle * 0.9);

                            // Sun glint on the water surface.
                            Light glintLight = GetMainLight();
                            float3 viewDirW = normalize(_WorldSpaceCameraPos - posWS);
                            float3 refl = reflect(-viewDirW, float3(0, 1, 0));
                            float glint = pow(saturate(dot(refl, glintLight.direction)), 48.0);
                            puddleGlint = half3(glintLight.color) * (glint * puddle * 0.5);
                        }
                    }

                    // Snow accumulates on upward facing surfaces (normalWS.y > 0.25)
                    if (globalSnow > 0.01)
                    {
                        float upwardBias = saturate((normWS.y - 0.25) / 0.55);
                        // Accumulation stages, driven by globalSnow (0..1):
                        //   thin dusting  -> a faint, even veil
                        //   splotchy      -> small patches (fine noise) appear and spread
                        //   large clumps  -> the patches merge into big drifts (noise scale grows)
                        //   full          -> everything covered
                        float c = globalSnow;
                        float2 sp = posWS.xz;
                        float nFine  = SnowValueNoise(sp * 1.3) * 0.6 + SnowValueNoise(sp * 3.1) * 0.4;
                        float nLarge = SnowValueNoise(sp * 0.11) * 0.65 + SnowValueNoise(sp * 0.3) * 0.35;
                        float n = lerp(nFine, nLarge, smoothstep(0.35, 0.75, c));
                        float patchy = saturate((c * 1.3 - n) / 0.10);
                        float thin = smoothstep(0.0, 0.3, c) * 0.35;
                        float snowCoverage = max(thin, patchy) * upwardBias;

                        half3 snowColor = half3(0.92, 0.95, 0.99); // Soft crystalline winter white
                        // Ramp coverage up faster than the raw accumulation value so the ground turns
                        // white early in a snowfall instead of staying brown until it is near 1.0.
                        // Snow removal: cleared areas stay bare until new snow refills them.
                        float2 clUv = (posWS.xz - _SnowFootprintRect.xy) * _SnowFootprintRect.zw;
                        float cleared = SAMPLE_TEXTURE2D(_SnowClearedTex, sampler_linear_clamp, clUv).r;
                        cleared *= step(1e-6, _SnowFootprintRect.z);
                        float rawSnow = snowCoverage * (1.0 - cleared);
                        float2 fpUv = (posWS.xz - _SnowFootprintRect.xy) * _SnowFootprintRect.zw;
                        float footprint = SAMPLE_TEXTURE2D(_SnowFootprintTex, sampler_linear_clamp, fpUv).r;
                        footprint *= step(1e-6, _SnowFootprintRect.z); // no mask bound yet -> no prints
                        half3 groundCol = col;
                        snowMask = rawSnow * (1.0 - footprint);
                        col = lerp(groundCol, snowColor, snowMask);
                        // Trodden snow: the ground shows through, slightly darker than untouched ground.
                        col = lerp(col, groundCol * 0.8, rawSnow * footprint);
                    }
                }

                col = lerp(colBeforeWeather, col, weatherW);
                snowMask *= weatherW;
                puddleGlint *= weatherW;

                // Cel / low-poly faceted lighting
                // Receive the sun's shadows (poles, buildings, trees fall across the ground). The cel look keeps them as a
                // flat darker step rather than a soft gradient.
                float4 shadowCoord = TransformWorldToShadowCoord(posWS);
                Light mainLight = GetMainLight(shadowCoord);
                // URP's GetMainLight().color has the light's intensity baked in - Summer's sun
                // intensity is 2.0 (see DayNightCycle._summerSunIntensity), which without this
                // clamp blows the red/green channels out toward white while blue lags behind,
                // reading as a flat yellow-white wash over every biome regardless of its real
                // color. This is a stylized/cel shader, not HDR, so the lit color is never meant
                // to exceed 1.
                half3 litColor = saturate(mainLight.color);
                // Ambient floor: with a weak sun (night, dusk, storms) the terrain would go almost black,
                // because this shader only reads the main light. Keep a cool ambient minimum.
                litColor = max(litColor, (half3)(unity_AmbientSky.rgb * 0.9));
                float ndotl = max(0.0, dot(normWS, mainLight.direction));
                float celLight = step(0.12, ndotl) * 0.35 + step(0.45, ndotl) * 0.35 + 0.3;
                // Snow must read white, not brown: the sun is dimmed and warm-tinted in winter
                // weather, and multiplying white by that gives a muddy tan. On snow-covered
                // pixels use a neutral cool-white light with a brightness floor and skip the
                // darkest cel band.
                half sunLuma = dot(litColor, half3(0.299, 0.587, 0.114));
                half3 snowLit = half3(0.96, 0.98, 1.0) * max(sunLuma, 0.9);
                litColor = lerp(litColor, snowLit, snowMask);
                celLight = lerp(celLight, max(celLight, 0.95), snowMask);
                celLight *= lerp(0.45, 1.0, step(0.5, mainLight.shadowAttenuation));   // in the sun's shadow
                half3 finalRGB = col * (litColor * celLight);
                finalRGB += puddleGlint;

                // Additional lights (player flashlight / lantern, later lamps): cel-stepped like the sun.
                #if defined(USE_CLUSTER_LIGHT_LOOP) || defined(USE_FORWARD_PLUS)
                {
                    InputData inputData = (InputData)0;
                    inputData.positionWS = posWS;
                    inputData.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(input.positionCS);
                    uint addCount = GetAdditionalLightsCount();
                    LIGHT_LOOP_BEGIN(addCount)
                        Light al = GetAdditionalLight(lightIndex, posWS, half4(1, 1, 1, 1));
                        float aNdl = saturate(dot(normWS, al.direction));
                        float aCel = step(0.05, aNdl) * 0.5 + aNdl * 0.5;
                        finalRGB += col * al.color * (al.distanceAttenuation * al.shadowAttenuation * aCel);
                    LIGHT_LOOP_END
                }
                #elif defined(_ADDITIONAL_LIGHTS)
                {
                    uint addCount = GetAdditionalLightsCount();
                    for (uint li = 0u; li < addCount; ++li)
                    {
                        Light al = GetAdditionalLight(li, posWS, half4(1, 1, 1, 1));
                        float aNdl = saturate(dot(normWS, al.direction));
                        float aCel = step(0.05, aNdl) * 0.5 + aNdl * 0.5;
                        finalRGB += col * al.color * (al.distanceAttenuation * al.shadowAttenuation * aCel);
                    }
                }
                #endif

                finalRGB *= CloudShadowFactor(posWS);

                // Ground grid: 1 m world-space lines drawn over EVERY ground texture (biomes,
                // water, snow, ...), matching the old T_Ground_GrassGrid tile (2 px of 64 = 3.1 cm).
                // Lines sit on integer world X/Z. Cliffs are skipped because the lines would smear
                // into vertical stripes on near-vertical faces.
                float2 gridUV = posWS.xz;
                float2 gridAA = max(fwidth(gridUV), 1e-4);            // anti-alias to ~1 screen pixel
                float2 gridDist = frac(gridUV);                       // 0 at a line, up to 1 across a metre
                float2 gridLine = 1.0 - smoothstep(_GridLineWidth, _GridLineWidth + gridAA, gridDist);
                float gridMask = saturate(max(gridLine.x, gridLine.y)) * _GridOpacity;
                gridMask *= (slope > 0.38) ? 0.0 : 1.0;
                // Lit by luminance only (no mainLight.color tint) so the grid stays a neutral
                // grey/white line under warm/low sun angles instead of reading as brown.
                float gridLuma = dot(litColor, half3(0.299, 0.587, 0.114)) * celLight;
                finalRGB = lerp(finalRGB, _GridColor.rgb * gridLuma, gridMask);

                return half4(finalRGB, 1.0);
            }
            ENDHLSL
        }

        // Renders the ground colour (the same TerrainGroundBase the lit pass would run per pixel) into a texture covering the whole map, once.
        // No keywords: a single variant. Drawn by TerrainGroundBake.cs, never by a camera.
        Pass
        {
            Name "GroundBake"
            Tags { "LightMode"="HomesteaderGroundBake" }
            Cull Off
            ZWrite Off
            ZTest Always

            HLSLPROGRAM
            #pragma vertex vertBake
            #pragma fragment fragBake
            #pragma target 4.5

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "HomesteaderTerrainProps.hlsl"
            #include "HomesteaderTerrainGround.hlsl"

            float2 _BakeSize;   // the texture's size in pixels

            struct VaryingsBake { float4 positionCS : SV_POSITION; };

            VaryingsBake vertBake(uint id : SV_VertexID)
            {
                VaryingsBake o;
                float2 uv = float2((id << 1) & 2, id & 2);   // one triangle that covers the whole target
                o.positionCS = float4(uv * 2.0 - 1.0, 0.0, 1.0);
                return o;
            }

            half4 fragBake(VaryingsBake i) : SV_Target
            {
                // SV_Position is the pixel centre in texture rows, which is how the lit pass samples the result back (v = z / mapSize).
                float2 worldXZ = i.positionCS.xy / _BakeSize * _TerrainBounds.xy;
                float2 biomeUv = worldXZ / _TerrainBounds.xy;
                return half4(TerrainGroundBase(worldXZ, biomeUv), 1.0);
            }
            ENDHLSL
        }

        // Without this the ground is missing from the depth texture (depth of field, soft effects read it), so the buried wires and pipes under it
        // looked like nearer objects and came out outlined.
        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode"="DepthOnly" }
            ZWrite On
            ColorMask R

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "HomesteaderTerrainProps.hlsl"

            struct Attributes { float4 positionOS : POSITION; };
            struct Varyings { float4 positionCS : SV_POSITION; };

            Varyings vert(Attributes input)
            {
                Varyings o;
                o.positionCS = TransformObjectToHClip(input.positionOS.xyz);
                return o;
            }

            half frag(Varyings input) : SV_Target { return input.positionCS.z; }
            ENDHLSL
        }
    }
    FallBack "Hidden/Universal Render Pipeline/FallbackError"
}
