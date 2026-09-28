Shader "Homesteader/GenerativeTerrainURP"
{
    Properties
    {
        _BiomeMap ("Biome Control Map (R=Mode, G=Moisture, B=Nutrients, A=Slope)", 2D) = "black" {}
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
            // Pre-computed border factor: 0 = biome interior, 1 = biome border.
            // Bilinear-filtered for smooth transitions.
            TEXTURE2D(_BiomeBorderTex);
            SAMPLER(sampler_BiomeBorderTex);

            CBUFFER_START(UnityPerMaterial)
                float4 _TerrainBounds;
                float _NormalStrength;
                float _NutrientDarkening;
                half4 _GridColor;
                float _GridLineWidth;
                float _GridOpacity;

            CBUFFER_END

            // Global Weather parameters set via Shader.SetGlobalVector("_WeatherGroundEffects", ...)
            float4 _WeatherGroundEffects;

            // Smooth 2D value noise in [0,1] (used for patchy snow accumulation).
            float SnowHash(float2 p)
            {
                return frac(sin(dot(p, float2(127.1, 311.7))) * 43758.5453);
            }

            // Better hash for value noise - avoids axis-aligned grid artifacts
            float2 SnowHash2(float2 p)
            {
                float2 h = float2(
                    frac(sin(dot(p, float2(127.1, 311.7)) + 17.0) * 43758.5453),
                    frac(sin(dot(p, float2(269.5, 183.3)) + 23.0) * 43758.5453)
                );
                return h;
            }

            float SnowValueNoise(float2 p)
            {
                float2 i = floor(p);
                float2 f = frac(p);
                float2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0); // quintic for smoother results
                float2 a = SnowHash2(i);
                float2 b = SnowHash2(i + float2(1, 0));
                float2 c = SnowHash2(i + float2(0, 1));
                float2 d = SnowHash2(i + float2(1, 1));
                float r1 = lerp(lerp(a.x, b.x, u.x), lerp(c.x, d.x, u.x), u.y);
                float r2 = lerp(lerp(a.y, b.y, u.x), lerp(c.y, d.y, u.x), u.y);
                return (r1 + r2) * 0.5;
            }

            // FBM (fractal Brownian motion) for natural multi-octave noise
            float FBM(float2 p, int octaves)
            {
                float val = 0.0;
                float amp = 0.5;
                float freq = 1.0;
                for (int i = 0; i < 4; i++)
                {
                    if (i >= octaves) break;
                    val += amp * SnowValueNoise(p * freq);
                    freq *= 2.0;
                    amp *= 0.5;
                }
                return val;
            }

            // --- Procedural grass texture (no extra geometry, no extra draw calls) ---
            // Short grass + flowers for meadows/pasture (biomeMode 0).
            // Tall dense grass for lush prairies (biomeMode 13).

            // Hash-based per-cell random for flower placement.
            float2 GrassHash2(float2 p)
            {
                float2 h = float2(
                    frac(sin(dot(p, float2(127.1, 311.7))) * 43758.5453),
                    frac(sin(dot(p, float2(269.5, 183.3))) * 43758.5453)
                );
                return h;
            }

            // Short grass texture: fine noise variation + scattered flower dots.
            // Returns rgb grass color (base tint already applied by caller).
            half3 ShortGrassTexture(float2 pos, half3 baseTint)
            {
                half3 grassBase = half3(0.35, 0.50, 0.18);
                half3 grassDark = half3(0.22, 0.38, 0.12);
                half3 grassLight = half3(0.48, 0.62, 0.24);
                // Smooth FBM variation
                float n = FBM(pos * 0.15, 3);
                half3 col = lerp(grassDark, grassLight, n);
                col = lerp(grassBase, col, 0.7);
                // Sparse flowers
                float2 cell = floor(pos / 2.0);
                float2 fpos = frac(pos / 2.0) - 0.5;
                float2 rnd = GrassHash2(cell);
                if (rnd.x < 0.08)
                {
                    float2 foff = (rnd - 0.5) * 0.6;
                    float fd = length(fpos - foff);
                    if (fd < 0.12)
                    {
                        half3 flowerCol;
                        if (rnd.y < 0.3)       flowerCol = half3(0.95, 0.85, 0.25);
                        else if (rnd.y < 0.55) flowerCol = half3(0.92, 0.35, 0.45);
                        else if (rnd.y < 0.75) flowerCol = half3(0.75, 0.55, 0.95);
                        else                   flowerCol = half3(0.98, 0.98, 0.95);
                        col = lerp(col, flowerCol, smoothstep(0.12, 0.06, fd));
                    }
                }
                return col;
            }

            // Tall grass texture: denser, darker, more vertical streaks for prairies.
            half3 TallGrassTexture(float2 pos, half3 baseTint)
            {
                half3 grassBase = half3(0.20, 0.32, 0.10);
                half3 grassDark = half3(0.12, 0.22, 0.06);
                half3 grassLight = half3(0.30, 0.45, 0.14);
                float n = FBM(pos * 0.12, 3);
                half3 col = lerp(grassDark, grassLight, n);
                col = lerp(grassBase, col, 0.7);
                // Dry golden patches
                float dry = SnowValueNoise(pos * 0.08 + 100.0);
                half3 dryCol = half3(0.65, 0.55, 0.25);
                col = lerp(col, dryCol, smoothstep(0.7, 0.9, dry) * 0.4);
                return col;
            }

            // --- Forest floor textures (procedural, no extra geometry) ---

            // Hash for per-cell random on forest floors.
            float2 ForestHash2(float2 p)
            {
                float2 h = float2(
                    frac(sin(dot(p, float2(191.7, 241.3))) * 43758.5453),
                    frac(sin(dot(p, float2(334.2, 127.1))) * 43758.5453)
                );
                return h;
            }

            // Fallen-leaf texture for deciduous forests.
            // leafTintA/B are the two dominant leaf colors for this biome.
            // Maple forest floor: broad leaves, maple keys (helicopter seeds), twigs, moss
            half3 MapleForestTexture(float2 pos, half3 baseTint)
            {
                half3 soil = half3(0.20, 0.14, 0.08);
                half3 leafOrange = half3(0.50, 0.28, 0.10);
                half3 leafBrown  = half3(0.35, 0.20, 0.08);
                half3 leafRed    = half3(0.45, 0.15, 0.08);
                half3 moss       = half3(0.18, 0.30, 0.12);
                half3 twig      = half3(0.15, 0.10, 0.05);
                half3 mapleKey  = half3(0.40, 0.25, 0.12);

                float n = FBM(pos * 0.08, 3);
                half3 leafCol = lerp(leafBrown, leafOrange, n);
                leafCol = lerp(leafCol, leafRed, SnowValueNoise(pos * 0.06 + 12.0) * 0.3);
                half3 col = lerp(soil, leafCol, smoothstep(0.2, 0.8, n) * 0.85);

                // Broad leaves on 3m grid
                float2 lcell = floor(pos / 3.0);
                float2 lfpos = frac(pos / 3.0) - 0.5;
                float2 lrnd = ForestHash2(lcell);
                float2 loff = (lrnd - 0.5) * 0.3;
                float ld = length(lfpos - loff);
                col = lerp(col, leafCol, smoothstep(0.35, 0.15, ld) * 0.6);

                // Maple keys (helicopter seeds) on 2.5m grid
                float2 kcell = floor(pos / 2.5 + 7.3);
                float2 kfpos = frac(pos / 2.5 + 7.3) - 0.5;
                float2 krnd = ForestHash2(kcell);
                if (krnd.x < 0.15)
                {
                    float2 koff = (krnd - 0.5) * 0.4;
                    float kd = length(kfpos - koff);
                    col = lerp(col, mapleKey, smoothstep(0.12, 0.06, kd) * 0.7);
                }

                // Twigs on 4m grid
                float2 tcell = floor(pos / 4.0 + 3.1);
                float2 trnd = ForestHash2(tcell);
                if (trnd.x < 0.12)
                {
                    float twigLine = abs(frac(pos.x / 4.0 + 3.1) - trnd.x);
                    col = lerp(col, twig, smoothstep(0.04, 0.0, twigLine) * 0.5);
                }

                // Moss patches
                float mossN = SnowValueNoise(pos * 0.05 + 50.0);
                col = lerp(col, moss, smoothstep(0.65, 0.85, mossN) * 0.3);
                return col;
            }

            // Birch grove floor: pale yellow leaves, white birch bark strips, catkins, sparse ferns
            half3 BirchGroveTexture(float2 pos, half3 baseTint)
            {
                half3 soil = half3(0.25, 0.22, 0.16);
                half3 leafPale  = half3(0.68, 0.60, 0.28);
                half3 leafYellow = half3(0.55, 0.48, 0.18);
                half3 barkWhite  = half3(0.72, 0.68, 0.58);
                half3 barkDark   = half3(0.35, 0.30, 0.22);
                half3 catkin     = half3(0.45, 0.38, 0.20);
                half3 fern       = half3(0.15, 0.28, 0.10);

                float n = FBM(pos * 0.1, 3);
                half3 leafCol = lerp(leafYellow, leafPale, n);
                half3 col = lerp(soil, leafCol, smoothstep(0.2, 0.8, n) * 0.8);

                // Small leaves on 1.5m grid
                float2 lcell = floor(pos / 1.5);
                float2 lfpos = frac(pos / 1.5) - 0.5;
                float2 lrnd = ForestHash2(lcell);
                float2 loff = (lrnd - 0.5) * 0.3;
                float ld = length(lfpos - loff);
                col = lerp(col, leafCol, smoothstep(0.25, 0.1, ld) * 0.5);

                // Birch bark strips on 3m grid
                float2 bcell = floor(pos / 3.0 + 5.7);
                float2 brnd = ForestHash2(bcell);
                if (brnd.x < 0.2)
                {
                    float2 bfpos = frac(pos / 3.0 + 5.7) - 0.5;
                    float barkShape = abs(bfpos.y - (brnd.y - 0.5) * 0.4);
                    col = lerp(col, barkWhite, smoothstep(0.08, 0.02, barkShape) * 0.6);
                    // Dark bark markings
                    float mark = abs(frac(pos.y / 3.0 + 5.7) - brnd.x);
                    col = lerp(col, barkDark, smoothstep(0.03, 0.0, mark) * 0.4);
                }

                // Catkins on 2m grid
                float2 ccell = floor(pos / 2.0 + 11.2);
                float2 crnd = ForestHash2(ccell);
                if (crnd.x < 0.1)
                {
                    float2 cfpos = frac(pos / 2.0 + 11.2) - 0.5;
                    float2 coff = (crnd - 0.5) * 0.3;
                    float cd = length(cfpos - coff);
                    col = lerp(col, catkin, smoothstep(0.08, 0.04, cd) * 0.5);
                }

                // Sparse fern undergrowth
                float fernN = SnowValueNoise(pos * 0.06 + 33.0);
                col = lerp(col, fern, smoothstep(0.7, 0.88, fernN) * 0.25);
                return col;
            }

            // Oak woodland floor: deep brown leaves, acorns, exposed roots, dappled light, moss
            half3 OakWoodlandTexture(float2 pos, half3 baseTint)
            {
                half3 soil = half3(0.18, 0.12, 0.06);
                half3 leafDeep  = half3(0.28, 0.16, 0.06);
                half3 leafBrown = half3(0.40, 0.24, 0.10);
                half3 leafOlive = half3(0.35, 0.30, 0.12);
                half3 acorn     = half3(0.30, 0.18, 0.08);
                half3 acornCap  = half3(0.20, 0.12, 0.04);
                half3 root      = half3(0.25, 0.18, 0.10);
                half3 moss      = half3(0.20, 0.32, 0.14);

                float n = FBM(pos * 0.07, 3);
                float n2 = SnowValueNoise(pos * 0.15 + 29.0);
                half3 leafCol = lerp(leafDeep, leafBrown, n);
                leafCol = lerp(leafCol, leafOlive, n2 * 0.3);
                half3 col = lerp(soil, leafCol, smoothstep(0.15, 0.85, n) * 0.85);

                // Large leaves on 2.5m grid
                float2 lcell = floor(pos / 2.5);
                float2 lfpos = frac(pos / 2.5) - 0.5;
                float2 lrnd = ForestHash2(lcell);
                float2 loff = (lrnd - 0.5) * 0.3;
                float ld = length(lfpos - loff);
                col = lerp(col, leafCol, smoothstep(0.3, 0.12, ld) * 0.55);

                // Acorns on 1.5m grid
                float2 acell = floor(pos / 1.5 + 8.4);
                float2 afpos = frac(pos / 1.5 + 8.4) - 0.5;
                float2 arnd = ForestHash2(acell);
                if (arnd.x < 0.18)
                {
                    float2 aoff = (arnd - 0.5) * 0.3;
                    float ad = length(afpos - aoff);
                    col = lerp(col, acorn, smoothstep(0.1, 0.05, ad) * 0.6);
                    // Acorn cap (darker top)
                    float capD = length(afpos - aoff - float2(0, 0.04));
                    col = lerp(col, acornCap, smoothstep(0.05, 0.02, capD) * 0.5);
                }

                // Exposed roots on 5m grid
                float2 rcell = floor(pos / 5.0 + 2.1);
                float2 rrnd = ForestHash2(rcell);
                if (rrnd.x < 0.15)
                {
                    float rootLine = abs(frac(pos.x / 5.0 + 2.1) - rrnd.y);
                    col = lerp(col, root, smoothstep(0.03, 0.0, rootLine) * 0.5);
                }

                // Dappled light
                float dapple = SnowValueNoise(pos * 0.04 + 70.0);
                col = lerp(col, half3(0.50, 0.40, 0.20), smoothstep(0.8, 0.92, dapple) * 0.15);

                // Moss patches
                float mossN = SnowValueNoise(pos * 0.05 + 60.0);
                col = lerp(col, moss, smoothstep(0.7, 0.88, mossN) * 0.25);
                return col;
            }

            // Poplar stand floor: golden-yellow leaves, catkins, smooth bark pieces, wind drifts
            half3 PoplarStandTexture(float2 pos, half3 baseTint)
            {
                half3 soil = half3(0.22, 0.16, 0.08);
                half3 leafGold   = half3(0.60, 0.46, 0.12);
                half3 leafYellow = half3(0.52, 0.40, 0.10);
                half3 leafOrange = half3(0.48, 0.32, 0.08);
                half3 catkin    = half3(0.35, 0.28, 0.12);
                half3 barkPiece = half3(0.30, 0.25, 0.15);

                float n = FBM(pos * 0.09, 3);
                float n2 = SnowValueNoise(pos * 0.2 + 4.0);
                half3 leafCol = lerp(leafYellow, leafGold, n);
                leafCol = lerp(leafCol, leafOrange, n2 * 0.2);
                half3 col = lerp(soil, leafCol, smoothstep(0.15, 0.7, n) * 0.85);

                // Leaves on 1.5m grid (poplar leaves are small/round)
                float2 lcell = floor(pos / 1.5);
                float2 lfpos = frac(pos / 1.5) - 0.5;
                float2 lrnd = ForestHash2(lcell);
                float2 loff = (lrnd - 0.5) * 0.3;
                float ld = length(lfpos - loff);
                col = lerp(col, leafCol, smoothstep(0.22, 0.08, ld) * 0.5);

                // Catkins on 2m grid
                float2 ccell = floor(pos / 2.0 + 6.8);
                float2 crnd = ForestHash2(ccell);
                if (crnd.x < 0.12)
                {
                    float2 cfpos = frac(pos / 2.0 + 6.8) - 0.5;
                    float2 coff = (crnd - 0.5) * 0.3;
                    float cd = length(cfpos - coff);
                    col = lerp(col, catkin, smoothstep(0.06, 0.03, cd) * 0.5);
                }

                // Smooth bark pieces on 3m grid
                float2 bcell = floor(pos / 3.0 + 14.2);
                float2 brnd = ForestHash2(bcell);
                if (brnd.x < 0.1)
                {
                    float2 bfpos = frac(pos / 3.0 + 14.2) - 0.5;
                    float barkShape = abs(bfpos.x - (brnd.y - 0.5) * 0.4);
                    col = lerp(col, barkPiece, smoothstep(0.06, 0.02, barkShape) * 0.4);
                }

                // Wind-blown leaf drifts
                float drift = SnowValueNoise(pos * 0.03 + 22.0);
                col = lerp(col, leafGold, smoothstep(0.75, 0.9, drift) * 0.2);
                return col;
            }

            // Pine needle texture: pine cones, needle clumps, small branches, moss
            half3 PineNeedleTexture(float2 pos, half3 baseTint)
            {
                half3 needleBase = half3(0.28, 0.18, 0.10);
                half3 soil = half3(0.18, 0.12, 0.06);
                half3 moss = half3(0.20, 0.35, 0.15);
                half3 cone = half3(0.25, 0.15, 0.06);
                half3 coneDark = half3(0.15, 0.08, 0.03);
                half3 branch = half3(0.12, 0.08, 0.04);

                float n = FBM(pos * 0.1, 3);
                half3 col = lerp(soil, needleBase, smoothstep(0.2, 0.8, n) * 0.8);

                // Pine cones on 2m grid
                float2 ccell = floor(pos / 2.0 + 4.5);
                float2 cfpos = frac(pos / 2.0 + 4.5) - 0.5;
                float2 crnd = ForestHash2(ccell);
                if (crnd.x < 0.15)
                {
                    float2 coff = (crnd - 0.5) * 0.3;
                    float cd = length(cfpos - coff);
                    col = lerp(col, cone, smoothstep(0.12, 0.06, cd) * 0.6);
                    // Cone scale pattern
                    float scale = abs(frac(cfpos.y * 4.0 + crnd.x * 3.0) - 0.5);
                    col = lerp(col, coneDark, smoothstep(0.15, 0.05, scale) * 0.3);
                }

                // Small branches on 3m grid
                float2 bcell = floor(pos / 3.0 + 9.1);
                float2 brnd = ForestHash2(bcell);
                if (brnd.x < 0.12)
                {
                    float branchLine = abs(frac(pos.y / 3.0 + 9.1) - brnd.y);
                    col = lerp(col, branch, smoothstep(0.03, 0.0, branchLine) * 0.4);
                }

                // Green moss patches
                float mossN = SnowValueNoise(pos * 0.05 + 50.0);
                col = lerp(col, moss, smoothstep(0.7, 0.88, mossN) * 0.3);
                return col;
            }

            // Rocky terrain texture: cracked stone with moss in crevices.
            half3 RockyTexture(float2 pos, half3 baseTint)
            {
                half3 stoneBase = half3(0.45, 0.43, 0.40);
                half3 stoneDark = half3(0.30, 0.28, 0.26);
                half3 stoneLight = half3(0.58, 0.55, 0.52);
                float n = FBM(pos * 0.06, 3);
                half3 col = lerp(stoneDark, stoneLight, n);
                col = lerp(stoneBase, col, 0.7);
                // Moss in crevices
                float moss = SnowValueNoise(pos * 0.04 + 30.0);
                col = lerp(col, half3(0.22, 0.33, 0.14), smoothstep(0.7, 0.88, moss) * 0.25);
                return col;
            }

            // Arid/dry terrain: cracked dirt with sand patches and sparse dead grass.
            half3 AridTexture(float2 pos, half3 baseTint)
            {
                half3 sand = half3(0.78, 0.68, 0.45);
                half3 dirt = half3(0.55, 0.40, 0.25);
                half3 dryGrass = half3(0.60, 0.52, 0.28);
                float n = FBM(pos * 0.05, 3);
                half3 col = lerp(dirt, sand, smoothstep(0.3, 0.7, n));
                // Dry grass patches
                float grass = SnowValueNoise(pos * 0.03 + 42.0);
                col = lerp(col, dryGrass, smoothstep(0.6, 0.85, grass) * 0.3);
                return col;
            }

            // Riverbed: muddy banks with smooth water-worn stones
            half3 RiverbedTexture(float2 pos, half3 baseTint)
            {
                half3 mud = half3(0.32, 0.26, 0.18);
                half3 mudDark = half3(0.22, 0.17, 0.12);
                half3 sand = half3(0.55, 0.45, 0.30);
                float n = FBM(pos * 0.08, 3);
                half3 col = lerp(mudDark, mud, n);
                col = lerp(col, sand, smoothstep(0.6, 0.85, n) * 0.4);
                return col;
            }

            // Lakebed: deeper silt and smooth sediment
            half3 LakebedTexture(float2 pos, half3 baseTint)
            {
                half3 silt = half3(0.28, 0.24, 0.16);
                half3 siltDark = half3(0.18, 0.15, 0.10);
                half3 clay = half3(0.38, 0.32, 0.22);
                float n = FBM(pos * 0.06, 3);
                half3 col = lerp(siltDark, silt, n);
                col = lerp(col, clay, smoothstep(0.7, 0.9, n) * 0.3);
                return col;
            }

            // Pondbed: organic muck with reed patches
            half3 PondbedTexture(float2 pos, half3 baseTint)
            {
                half3 muck = half3(0.25, 0.20, 0.12);
                half3 muckDark = half3(0.15, 0.12, 0.08);
                half3 reed = half3(0.35, 0.32, 0.18);
                float n = FBM(pos * 0.07, 3);
                half3 col = lerp(muckDark, muck, n);
                float reedNoise = SnowValueNoise(pos * 0.04 + 15.0);
                col = lerp(col, reed, smoothstep(0.65, 0.85, reedNoise) * 0.3);
                return col;
            }

            // Farmland: tilled soil rows
            half3 FarmlandTexture(float2 pos, half3 baseTint)
            {
                half3 soil = half3(0.35, 0.22, 0.10);
                half3 soilDark = half3(0.25, 0.15, 0.06);
                half3 soilLight = half3(0.45, 0.30, 0.15);
                float n = FBM(pos * 0.05, 3);
                half3 col = lerp(soilDark, soilLight, n);
                col = lerp(soil, col, 0.7);
                // Tilled rows every 2m
                float row = abs(frac(pos.x * 0.5) - 0.5);
                col *= lerp(0.85, 1.0, smoothstep(0.0, 0.4, row));
                return col;
            }

            // Maintained grass: manicured lawn with mower stripes
            half3 LawnTexture(float2 pos, half3 baseTint)
            {
                half3 grassBase = half3(0.38, 0.52, 0.20);
                half3 grassDark = half3(0.30, 0.45, 0.16);
                half3 grassLight = half3(0.45, 0.58, 0.24);
                float n = FBM(pos * 0.12, 3);
                half3 col = lerp(grassDark, grassLight, n);
                col = lerp(grassBase, col, 0.6);
                // Mower stripes every 4m
                float stripe = step(0.5, frac(pos.x * 0.25));
                col *= lerp(0.92, 1.0, stripe);
                return col;
            }

            // Wetland marsh: dark muddy ground with water pools and reeds
            half3 WetlandTexture(float2 pos, half3 baseTint)
            {
                half3 muck = half3(0.20, 0.18, 0.12);
                half3 water = half3(0.12, 0.18, 0.15);
                half3 reed = half3(0.30, 0.32, 0.14);
                float n = FBM(pos * 0.05, 3);
                half3 col = lerp(muck, reed, smoothstep(0.3, 0.7, n));
                // Dark water pools
                float pool = SnowValueNoise(pos * 0.03 + 25.0);
                col = lerp(col, water, smoothstep(0.6, 0.85, pool) * 0.5);
                return col;
            }

            // Get procedural texture for a given biome mode
            half3 GetBiomeTexture(float mode, float2 pos)
            {
                half3 c;
                if (mode < 0.5)
                    c = ShortGrassTexture(pos, half3(0,0,0));        // 0: meadow
                else if (mode < 1.5)
                    c = RiverbedTexture(pos, half3(0,0,0));          // 1: river
                else if (mode < 2.5)
                    c = LakebedTexture(pos, half3(0,0,0));           // 2: lake
                else if (mode < 3.5)
                    c = PondbedTexture(pos, half3(0,0,0));           // 3: pond
                else if (mode < 4.5)
                    c = FarmlandTexture(pos, half3(0,0,0));          // 4: farmland
                else if (mode < 5.5)
                    c = LawnTexture(pos, half3(0,0,0));              // 5: maintained grass
                else if (mode < 6.5)
                    c = WetlandTexture(pos, half3(0,0,0));           // 6: wetland marsh
                else if (mode < 7.5)
                    c = MapleForestTexture(pos, half3(0,0,0));       // 7: maple
                else if (mode < 8.5)
                    c = BirchGroveTexture(pos, half3(0,0,0));        // 8: birch
                else if (mode < 9.5)
                    c = OakWoodlandTexture(pos, half3(0,0,0));      // 9: oak
                else if (mode < 10.5)
                    c = PineNeedleTexture(pos, half3(0,0,0));        // 10: pine
                else if (mode < 11.5)
                    c = RockyTexture(pos, half3(0,0,0));             // 11: rocky
                else if (mode < 12.5)
                    c = AridTexture(pos, half3(0,0,0));              // 12: dry/arid
                else if (mode < 13.5)
                    c = TallGrassTexture(pos, half3(0,0,0));        // 13: prairie
                else if (mode < 14.5)
                    c = PoplarStandTexture(pos, half3(0,0,0));      // 14: poplar
                else if (mode < 15.5)
                    c = PoplarStandTexture(pos, half3(0,0,0));      // 15: mixed (use poplar as base)
                else
                    c = ShortGrassTexture(pos, half3(0,0,0));      // fallback
                return c;
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

                // Water is now rendered by a separate vertex-displaced water mesh (WaterSurface.shader).
                // The terrain shader just paints biome colors — under water, the baked biome map's
                // river/lake/pond tint shows through as the riverbed/pondbed color.
                bool isWater = (biomeMode >= 1 && biomeMode <= 3); // river=1, lake=2, pond=3
                bool isWetland = (biomeMode == 6);
                bool isLawn = !isWater && !isWetland && biomeMode == 5;
                bool isFarmland = !isWater && !isWetland && biomeMode == 4;

                // Color & Biome Evaluation
                if (isWater)
                {
                    // Riverbed/pondbed: dark, wet ground — the water mesh renders the actual
                    // water surface on top. Just read the biome tint darkened.
                    half3 bedColor = SAMPLE_TEXTURE2D(_BiomeMap, sampler_linear_clamp, biomeUv).rgb;
                    col = bedColor * 0.35; // dark wet riverbed
                }
                else if (isWetland)
                {
                    half3 shoreColor = SAMPLE_TEXTURE2D(_BiomeMap, sampler_linear_clamp, biomeUv).rgb;
                    float gravelDither = step(0.5, frac(posWS.x * 2.0 + posWS.z * 2.0));
                    col = shoreColor * lerp(0.86, 0.96, gravelDither);
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
                    // --- Biome texture blending ---
                    // At biome borders, blend between the two adjacent biomes' procedural
                    // textures (not flat colors) for smooth transitions without square edges.

                    // Procedural texture for this biome (no blending)
                    col = GetBiomeTexture(biomeMode, posWS.xz);
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
