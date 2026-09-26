Shader "Homesteader/GenerativeTerrainURP"
{
    Properties
    {
        _BiomeMap ("Biome Control Map (R=Mode, G=Moisture, B=Nutrients, A=Slope)", 2D) = "black" {}
        _TerrainBounds ("Terrain Bounds (X, Z, Height, 0)", Vector) = (500.0, 500.0, 60.0, 0.0)
        _NormalStrength ("Facet Normal Strength", Range(0, 1)) = 0.25
        _NutrientDarkening ("Nutrient Soil Darkening", Range(0, 1)) = 0.35
        _GridColor ("Ground Grid Color", Color) = (0.90, 0.90, 0.90, 1)
        _GridLineWidth ("Ground Grid Line Width (m)", Range(0, 0.2)) = 0.031
        _GridOpacity ("Ground Grid Opacity", Range(0, 1)) = 1
        _HasIsland ("Pond Has Island (0 or 1)", Range(0, 1)) = 0
        _HasBranch ("River Has Branch (0 or 1)", Range(0, 1)) = 0
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
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE
            #pragma multi_compile _ _SHADOWS_SOFT
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

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

            TEXTURE2D(_BiomeMap);
            SAMPLER(sampler_BiomeMap);
            // Unity inline sampler state: point filtering + clamp. The biome map's alpha channel
            // stores a biome mode id, so it must not be interpolated (that would invent
            // in-between ids that don't correspond to any real biome).
            SAMPLER(sampler_point_clamp);
            // A second sampler over the SAME texture, but bilinear: used for the map's RGB
            // (the biome's actual tint color), so adjacent biomes blend smoothly at their
            // border instead of stair-stepping at the texel grid.
            SAMPLER(sampler_linear_clamp);

            CBUFFER_START(UnityPerMaterial)
                float4 _TerrainBounds;
                float _NormalStrength;
                float _NutrientDarkening;
                half4 _GridColor;
                float _GridLineWidth;
                float _GridOpacity;
                float _HasIsland;
                float _HasBranch;
            CBUFFER_END

            // Global Weather parameters set via Shader.SetGlobalVector("_WeatherGroundEffects", ...)
            float4 _WeatherGroundEffects;

            // Smooth 2D value noise in [0,1] (used for patchy snow accumulation).
            float SnowHash(float2 p)
            {
                return frac(sin(dot(p, float2(127.1, 311.7))) * 43758.5453);
            }

            float SnowValueNoise(float2 p)
            {
                float2 i = floor(p);
                float2 f = frac(p);
                float2 u = f * f * (3.0 - 2.0 * f);
                return lerp(lerp(SnowHash(i), SnowHash(i + float2(1, 0)), u.x),
                            lerp(SnowHash(i + float2(0, 1)), SnowHash(i + float2(1, 1)), u.x), u.y);
            }

            // Footprint mask written by SnowFootprints.cs: R = print strength, top-down over the terrain.
            // _SnowFootprintRect = (originX, originZ, 1/sizeX, 1/sizeZ).
            TEXTURE2D(_SnowFootprintTex);
            float4 _SnowFootprintRect;
            // Cleared-snow mask (shovel / plow / vehicles), same coverage rect. R = 1 where snow was removed.
            TEXTURE2D(_SnowClearedTex);
            // Terrain basin map from PuddleBasinMap.cs: 1 = hollow / low ground (puddles collect), 0 = high ground.
            TEXTURE2D(_PuddleBasinTex);
            float4 _PuddleBasinRect;

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
                // A encodes (biomeMode + 0.5) / 16 (point-sampled: mode ids must never blend into
                // each other), RGB is the biome's actual tint color (bilinear-sampled below, so
                // adjacent biomes fade smoothly across their shared texel border instead of
                // stair-stepping). See HomesteaderTerrainGenerator.GenerateTerrain.
                float2 biomeUv = float2(x / _TerrainBounds.x, z / _TerrainBounds.y);
                half4 biomeSample = SAMPLE_TEXTURE2D(_BiomeMap, sampler_point_clamp, biomeUv);
                int biomeMode = (int)floor(biomeSample.a * 16.0);

                // 1. Water System: Central Winding River (~7m wide) and Kettle Pond Basin (~24m radius).
                // Shape is entirely analytic (the same distance fields HomesteaderTerrainGenerator
                // uses), not read from the 1-texel/metre baked map, so the shoreline is a smooth
                // curve instead of stair-stepping at the texel grid. Pond wins where the river's
                // path runs through it, exactly mirroring HomesteaderTerrainGenerator.EvaluateBiomeAt's
                // pond-before-river priority, so there's no seam where they meet.
                // Mirrors HomesteaderTerrainGenerator.GetRiverCenterX/GetRiverHalfWidth/GetPondRadius
                // exactly (layered, unrelated-frequency harmonics) so the river meanders and
                // varies in width, and the pond's shoreline is lumpy rather than a smooth curve,
                // matching the baked classification pixel for pixel.
                float riverX = 220.0
                    + sin(z * 0.015) * 45.0
                    + sin(z * 0.035 + 1.2) * 18.0
                    + sin(z * 0.006 + 2.7) * 30.0
                    + sin(z * 0.07 + 0.4) * 8.0;
                float distMainRiver = abs(x - riverX);

                // Optional tributary branch: mirrors HomesteaderTerrainGenerator.RiverHasBranch/
                // GetBranchCenterX exactly - starts AT the main river's centerline (offset 0) and
                // diverges from there, so it visibly splits off instead of appearing out of
                // nowhere a fixed distance away. _HasBranch is 0 or 1, set from C# to match.
                float branchTLinear = saturate((z - 260.0) / 140.0);
                // Smoothstep (zero slope at t=0) instead of linear, so the branch leaves tangent
                // to the main river instead of veering away at a sharp corner right at the split.
                float branchT = branchTLinear * branchTLinear * (3.0 - 2.0 * branchTLinear);
                float branchX = riverX + branchT * 90.0 + sin(z * 0.02 + 1.0) * 12.0 * branchT;
                float distBranchRiver = abs(x - branchX);
                bool branchActive = (_HasBranch > 0.5) && (z > 260.0);
                // Tapers the branch's width from a small-but-visible width up to full over the
                // first 25m past the split.
                float branchWidthTaper = saturate((z - 260.0) / 25.0);

                float2 pondCenter = float2(220.0, 210.0);
                // River flares into a wide funnel-shaped mouth as it nears the pond, so the two
                // water bodies erode into one smooth entrance instead of a narrow channel butting
                // into the pond's edge. Mirrors GetRiverHalfWidth exactly.
                float distToPondCenter = distance(float2(x, z), pondCenter);
                float mouthT = 1.0 - saturate((distToPondCenter - 20.0) / 35.0);
                float mouthWiden = smoothstep(0.0, 1.0, mouthT) * 16.0;
                float riverBaseHalfWidth = clamp(4.0 + sin(z * 0.04) * 1.8 + sin(z * 0.11 + 1.0) * 1.2, 2.2, 6.5) + mouthWiden;

                // Cheap value-noise (hash + bilinear) - not bit-exact with HomesteaderTerrainGenerator's
                // Mathf.PerlinNoise, but same amplitude/frequency, so the analytic mask and the baked
                // map agree to well under a metre. Reused for both the pond's coastline and the
                // river's banks, each with its own coordinate scale, for visible inlets/points on
                // both, not just a smooth width wobble.
                #define VALUE_NOISE2(coord) (lerp(lerp(frac(sin(dot(floor(coord), float2(12.9898,78.233)))*43758.5453), frac(sin(dot(floor(coord)+float2(1,0), float2(12.9898,78.233)))*43758.5453), frac(coord).x), lerp(frac(sin(dot(floor(coord)+float2(0,1), float2(12.9898,78.233)))*43758.5453), frac(sin(dot(floor(coord)+float2(1,1), float2(12.9898,78.233)))*43758.5453), frac(coord).x), frac(coord).y))

                // Matches GetRiverHalfWidth exactly: base + mouth-widen + per-position inlet wobble.
                float riverInlet = (VALUE_NOISE2(float2(x * 0.12, z * 0.12) + 15.0) - 0.5) * 5.0;
                float mainHalfWidth = riverBaseHalfWidth + riverInlet;

                float distToRiver = distMainRiver;
                float riverHalfWidth = mainHalfWidth;
                if (branchActive)
                {
                    float branchHalfWidth = lerp(1.2, clamp(mainHalfWidth * 0.6, 1.8, 4.5), branchWidthTaper);
                    // Smooth-min (polynomial), not a hard "whichever is closer": a strict nearest
                    // pick always leaves a sharp crease along the line where the two distance
                    // fields are equal, no matter how smoothly the branch's own centerline curves
                    // away. This rounds that seam off over a `blend` metre radius instead.
                    // Mirrors HomesteaderTerrainGenerator.GetNearestRiverDistance exactly.
                    const float blend = 6.0;
                    float h = saturate(0.5 + 0.5 * (distMainRiver - distBranchRiver) / blend);
                    distToRiver = lerp(distMainRiver, distBranchRiver, h) - blend * h * (1.0 - h);
                    riverHalfWidth = lerp(mainHalfWidth, branchHalfWidth, h);
                }

                float distToPond = distToPondCenter;
                float pAngle = atan2(z - pondCenter.y, x - pondCenter.x);
                float2 inletCoord = float2(cos(pAngle) * 3.0 + 40.0, sin(pAngle) * 3.0 + 40.0);
                float2 inletCoord2 = float2(cos(pAngle) * 8.0 + 70.0, sin(pAngle) * 8.0 + 70.0);
                float inlets = (VALUE_NOISE2(inletCoord) - 0.5) * 16.0 + (VALUE_NOISE2(inletCoord2) - 0.5) * 8.0;
                float pondRadius = 24.0
                    + sin(pAngle * 2.0) * 7.0
                    + cos(pAngle * 3.0) * 5.0
                    + sin(pAngle * 5.0 + 1.3) * 3.0
                    + cos(pAngle * 7.0 + 0.7) * 2.0
                    + inlets;

                float aaWidth = max(fwidth(distToPond), fwidth(distToRiver)) + 1e-4;
                // Raw pond boundary, NOT yet reduced by the island carve-out below - this is what
                // guards the river funnel from claiming the island. HomesteaderTerrainGenerator's
                // CalculateElevationAt keeps this same priority (isRiverWater is gated by
                // !isPondWater using the outer pond radius, before the island special-case ever
                // runs), so the river funnel must use the same un-carved boundary here too -
                // otherwise the wide river mouth (it flares out right around the pond) reads the
                // island as "not pond" and paints it as flowing river water anyway.
                float pondMaskRaw = 1.0 - smoothstep(pondRadius - aaWidth, pondRadius + aaWidth, distToPond);
                float pondMask = pondMaskRaw;

                // Optional island: mirrors HomesteaderTerrainGenerator.PondHasIsland/GetIslandRadius
                // exactly (deterministic from worldSeed, no noise needed) so the shape it carves
                // out of the pond matches the baked land/beach classification there precisely.
                // _HasIsland is 0 or 1, set from C# (GenerateTerrain) to match PondHasIsland - a
                // plain float switch rather than a shader keyword, since it only needs one variant.
                float2 islandCenter = pondCenter + float2(7.0, -5.0);
                float distToIsland = distance(float2(x, z), islandCenter);
                float iAngle = atan2(z - islandCenter.y, x - islandCenter.x);
                float islandRadius = 6.0 + sin(iAngle * 3.0) * 2.0 + cos(iAngle * 5.0 + 0.5) * 1.2;
                float islandMask = (1.0 - smoothstep(islandRadius + 2.5 - aaWidth, islandRadius + 2.5 + aaWidth, distToIsland)) * _HasIsland;
                pondMask *= (1.0 - islandMask);

                float riverMask = (1.0 - smoothstep(riverHalfWidth - aaWidth, riverHalfWidth + aaWidth, distToRiver)) * (1.0 - pondMaskRaw);
                bool isPond = pondMask > 0.5;
                bool isRiver = riverMask > 0.5 && !isPond;
                bool isWater = isPond || isRiver;

                // Fringe outer edge gets its own small noise wobble (inlets/coves) via the same
                // hash noise, and crucially uses a HARD boundary (step, not a fractional multiply)
                // against the pond/river masks - a fractional (1-mask) leaves a thin anti-aliased
                // sliver where the two water features are tangent, which is what showed up as a
                // beach line visibly crossing through open water.
                float fringeNoise = (frac(sin(dot(float2(x, z) * 0.05, float2(12.9898, 78.233))) * 43758.5453) - 0.5) * 3.0;
                float riverWetT = saturate(((riverHalfWidth + 1.5 + fringeNoise) - distToRiver) / 2.0) * step(pondRadius, distToPond);
                float pondWetT = saturate(((pondRadius + 2.5 + fringeNoise) - distToPond) / 2.0) * (1.0 - islandMask);
                float wetlandT = saturate(max(riverWetT, pondWetT)) * (1.0 - step(0.5, riverMask)) * (1.0 - step(0.5, pondMask));
                bool isWetland = wetlandT > 0.02;
                bool isLawn = !isWater && !isWetland && biomeMode == 5;
                bool isFarmland = !isWater && !isWetland && biomeMode == 4;

                // 4. Color & Biome Evaluation
                if (isWater)
                {
                    // One shared water look (river/lake/pond) so the whole hydrological network
                    // reads as a single flowing body instead of separate differently-colored ponds.
                    half3 deepWater = half3(0.05, 0.30, 0.62);
                    half3 shallowWater = half3(0.15, 0.65, 0.82);

                    // Flowing directional ripples (smooth flowing waves, zero checkerboard) - same
                    // formula everywhere, so river/lake/pond all flow the same direction.
                    float flow = sin((posWS.x * 0.4 + posWS.z * 1.1) * 0.8 + _Time.y * 1.8) * 0.5
                               + cos((posWS.z * 1.3 - posWS.x * 0.3) * 0.6 - _Time.y * 2.2) * 0.5;
                    col = lerp(deepWater, shallowWater, saturate(flow * 0.35 + 0.35));

                    // Stylized crisp white foam edge along river and pond banks. Skipped across
                    // the river's mouth opening (still isPond there once inside pondRadius, since
                    // pond wins) - otherwise the pond's own shoreline foam ring traces straight
                    // across the open entrance, looking like the pond's outline crosses the river.
                    bool inRiverMouth = distToRiver < riverHalfWidth;
                    float edgeDist = isPond ? (pondRadius - distToPond) : (riverHalfWidth - distToRiver);
                    if (edgeDist < 0.45 && !(isPond && inRiverMouth))
                    {
                        col = lerp(col, half3(0.90, 0.96, 1.0), 0.85); // Crisp shoreline foam
                    }
                }
                else if (isWetland)
                {
                    // The shore fringe isn't just bog any more - HomesteaderTerrainGenerator picks
                    // sand, grass, or a boggy patch per-spot and bakes whichever it chose into the
                    // map, so just read that back (bilinear, so it still blends smoothly at its
                    // own edges) instead of hardcoding one wet-sand look for the whole shoreline.
                    half3 shoreColor = SAMPLE_TEXTURE2D(_BiomeMap, sampler_linear_clamp, biomeUv).rgb;
                    float gravelDither = step(0.5, frac(posWS.x * 2.0 + posWS.z * 2.0));
                    col = shoreColor * lerp(0.86, 0.96, gravelDither); // subtle damp-ground sheen
                }
                else if (isLawn)
                {
                    half3 lawnLight = half3(0.18, 0.82, 0.36);
                    half3 lawnDark = half3(0.10, 0.60, 0.22);
                    float stripe = step(0.5, frac(posWS.z / 1.2)); // 1.2m mower pass
                    col = lerp(lawnDark, lawnLight, stripe);
                }
                else if (isFarmland)
                {
                    half3 richLoam = half3(0.24, 0.11, 0.03);
                    half3 furrowShadow = half3(0.12, 0.05, 0.01);
                    float furrow = sin(posWS.x * 3.14159 / 1.0); // 1-meter tilled rows
                    col = lerp(richLoam, furrowShadow, step(0.0, furrow) * 0.65);
                }
                else
                {
                    // Remaining terrestrial biomes: bilinear-sampled straight from the baked map's
                    // RGB (the biome's actual color_hex tint), so a maple/birch/meadow/etc border
                    // fades smoothly across the texel grid instead of stair-stepping. A light
                    // per-pixel dither keeps large single-biome areas from looking like flat,
                    // textureless fills.
                    half3 biomeColor = SAMPLE_TEXTURE2D(_BiomeMap, sampler_linear_clamp, biomeUv).rgb;
                    float dither = frac(sin(dot(posWS.xz, float2(12.9898, 78.233))) * 43758.5453) * 0.06 - 0.03;
                    col = saturate(biomeColor + dither);
                }

                // Automatic cliffs on steep slopes (for non-water)
                if (!isWater && slope > 0.38)
                {
                    col = cliffColor;
                }

                // Global Weather Ground Effects (Wetness & Snow Accumulation)
                // _WeatherGroundEffects: (X = SnowCoverage [0..1], Y = GroundWetness [0..1], Z = reserved, W = reserved)
                float globalSnow = saturate(_WeatherGroundEffects.x);
                float globalWet = saturate(_WeatherGroundEffects.y);
                half3 puddleGlint = half3(0, 0, 0); // added after lighting so it stays a bright highlight
                float snowMask = 0.0; // how much of this pixel is snow-covered (drives neutral lighting below)

                if (!isWater)
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
                            float ph = frac(_Time.y * 0.9 + SnowHash(cell + 3.1));
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
    }
    FallBack "Hidden/Universal Render Pipeline/FallbackError"
}
