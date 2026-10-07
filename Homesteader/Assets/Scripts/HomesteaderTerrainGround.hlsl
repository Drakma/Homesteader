// The terrain's procedural ground: noise, per-biome textures, the soft biome blend and the water-bed colour. Shared by the lit pass (live, used until
// the ground is baked) and the GroundBake pass (which renders it once into a texture, see TerrainGroundBake.cs). Needs Core.hlsl and HomesteaderTerrainProps.hlsl first.
            TEXTURE2D(_BiomeMap);
            SAMPLER(sampler_BiomeMap);
            // Same smooth blurred coverage texture WaterSurface.shader fades its own alpha across (R=depth,
            // G=coverage - see HomesteaderTerrainGenerator.GenerateWaterMask/BlurCoverage). Used here to blend
            // the water-bed color into the land color across that same real band, instead of switching at the
            // hard point-sampled biomeMode boundary - isWater itself can't be smooth (mode ids don't blend),
            // so the fix has to be blending the two colors rather than the branch condition.
            TEXTURE2D(_WaterMask);
            // The starter road (HomesteaderTerrainGenerator.Road.cs): R = coverage, G = lateral offset from the centreline
            // (0.5 = centre, +-_RoadParams.x metres at the ends). Painted over the biome as a procedural dirt / gravel road.
            TEXTURE2D(_RoadMask);
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

            // --- Procedural dirt and gravel road ---
            // Packed dirt with two wheel ruts and a worn crown down the middle, gravel scattered and patchy (heavier in
            // the ruts and along the shoulders), grit spilling onto the verge, a few weeds through the crown.
            half3 RoadTexture(float2 pos, float lateralN, float coverage)
            {
                float lat = (lateralN - 0.5) * 2.0 * _RoadParams.x;       // metres from the centreline, signed
                float aLat = abs(lat);

                // Dirt: two warm browns mottled by large and fine noise.
                float large = FBM(pos * 0.35, 3);
                float fine = SnowValueNoise(pos * 5.0);
                half3 dirtA = half3(0.50, 0.38, 0.22);
                half3 dirtB = half3(0.40, 0.30, 0.17);
                half3 col = lerp(dirtB, dirtA, smoothstep(0.25, 0.75, large));
                col *= 0.92 + 0.16 * fine;

                // Compacted ruts: darker, smoother tracks about 0.9 m either side of the centre.
                float rutCentre = 0.72;
                float rut = 1.0 - smoothstep(0.0, 0.36, abs(aLat - rutCentre));
                rut *= smoothstep(0.45, 0.95, coverage);   // ruts fade out where the road frays into the grass
                col = lerp(col, col * 0.72, rut * 0.75);

                // Crown between the ruts: paler, dustier, sometimes grown over with weeds.
                float crown = 1.0 - smoothstep(0.15, 0.55, aLat);
                col = lerp(col, col * 1.12 + 0.02, crown * 0.5);
                float fray = 1.0 - smoothstep(0.35, 0.95, coverage);
                float weeds = smoothstep(0.58 - 0.25 * fray, 0.8 - 0.2 * fray, FBM(pos * 1.3 + 17.0, 3)) * saturate(crown + fray);
                col = lerp(col, half3(0.26, 0.40, 0.17), weeds * 0.7);

                // Gravel: pebble cells with jittered centres, light greys and tans. More in the ruts and on the
                // shoulders, patchy along the road.
                float patch = smoothstep(0.30, 0.70, FBM(pos * 0.22 + 41.0, 3));
                float gravelAmount = saturate(0.30 + 0.45 * patch + 0.25 * rut + 0.20 * smoothstep(1.0, 1.7, aLat));
                float2 cellP = pos * 6.0;
                float2 cellId = floor(cellP);
                float2 cellF = frac(cellP);
                float2 h = SnowHash2(cellId);
                float2 centre = 0.3 + 0.4 * h;
                float pd = length(cellF - centre);
                float size = 0.18 + 0.16 * SnowHash(cellId + 7.7);
                float pebble = smoothstep(size, size * 0.55, pd) * step(1.0 - gravelAmount, SnowHash(cellId + 3.3));
                half3 stoneA = half3(0.62, 0.58, 0.50);
                half3 stoneB = half3(0.50, 0.49, 0.47);
                half3 stoneC = half3(0.70, 0.63, 0.52);
                float pick = SnowHash(cellId + 19.1);
                half3 stone = pick < 0.33 ? stoneA : (pick < 0.66 ? stoneB : stoneC);
                stone *= 0.85 + 0.25 * SnowHash(cellId + 5.5);
                col = lerp(col, stone, pebble * 0.9);

                // A scuffed, gritty rim where the road meets the verge.
                float rim = 1.0 - smoothstep(0.35, 0.95, coverage);
                col = lerp(col, col * 0.85 + half3(0.05, 0.04, 0.02), rim * 0.5);
                return col;
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
                half3 leafOrange = half3(0.42, 0.24, 0.09);
                half3 leafBrown  = half3(0.33, 0.20, 0.09);
                half3 leafRed    = half3(0.36, 0.14, 0.07);
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
                half3 soil = half3(0.19, 0.14, 0.09);
                half3 leafPale  = half3(0.42, 0.30, 0.15);
                half3 leafYellow = half3(0.34, 0.24, 0.11);
                half3 barkWhite  = half3(0.62, 0.58, 0.50);
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
                half3 leafOlive = half3(0.30, 0.24, 0.10);
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
                half3 soil = half3(0.19, 0.13, 0.08);
                half3 leafGold   = half3(0.42, 0.29, 0.12);
                half3 leafYellow = half3(0.36, 0.25, 0.10);
                half3 leafOrange = half3(0.38, 0.23, 0.09);
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
                // Peat and moss: dark brown-green ground, moss hummocks, and a few shallow dark pools - the same
                // low-contrast, large-scale noise the other biomes use, so it sits in the palette with them.
                half3 peat = half3(0.20, 0.19, 0.11);
                half3 moss = half3(0.27, 0.34, 0.14);
                half3 mossLight = half3(0.36, 0.42, 0.20);
                half3 water = half3(0.13, 0.19, 0.16);
                float n = FBM(pos * 0.05, 3);
                half3 col = lerp(peat, moss, smoothstep(0.25, 0.7, n));
                float hummock = SnowValueNoise(pos * 0.18 + 11.0);
                col = lerp(col, mossLight, smoothstep(0.62, 0.85, hummock) * 0.35);
                float pool = SnowValueNoise(pos * 0.03 + 25.0);
                col = lerp(col, water, smoothstep(0.62, 0.85, pool) * 0.4);
                return col;
            }

            // Willow grove: lush, damp, yellow-green ground with soft shaded hollows and the odd drift of fallen willow leaves
            half3 WillowGroveTexture(float2 pos, half3 baseTint)
            {
                half3 grass = half3(0.36, 0.50, 0.19);
                half3 lush = half3(0.45, 0.58, 0.22);
                half3 shade = half3(0.22, 0.34, 0.14);
                half3 leaf = half3(0.58, 0.58, 0.26);
                float n = FBM(pos * 0.07, 3);
                half3 col = lerp(shade, grass, smoothstep(0.2, 0.65, n));
                col = lerp(col, lush, smoothstep(0.55, 0.9, FBM(pos * 0.11 + 7.0, 3)) * 0.5);
                float drift = SnowValueNoise(pos * 0.16 + 33.0);
                col = lerp(col, leaf, smoothstep(0.7, 0.9, drift) * 0.3);
                return col;
            }

            // Sand: pale, fine-grained, with soft ripples and the odd darker damp streak
            half3 SandTexture(float2 pos, half3 baseTint)
            {
                half3 sand = half3(0.82, 0.72, 0.48);
                half3 pale = half3(0.90, 0.82, 0.60);
                half3 damp = half3(0.66, 0.56, 0.36);
                float n = FBM(pos * 0.09, 3);
                half3 col = lerp(sand, pale, smoothstep(0.3, 0.75, n));
                float ripple = sin((pos.x * 0.7 + pos.y * 0.35) * 1.6 + FBM(pos * 0.2, 2) * 6.0) * 0.5 + 0.5;
                col = lerp(col, damp, smoothstep(0.82, 1.0, ripple) * 0.18);
                col = lerp(col, damp, smoothstep(0.7, 0.9, SnowValueNoise(pos * 0.05 + 11.0)) * 0.25);
                col += (SnowValueNoise(pos * 6.0) - 0.5) * 0.04;   // grain
                return col;
            }

            // Get procedural texture for a given biome mode
            // Fallen sticks lying at random angles: cells of `size` metres, each with at most one stick (probability `prob`) at a random place, turned a
            // random way, between lenMin and lenMax long. The 3x3 cells round the point are searched, so a stick crosses cell borders without a cut.
            half3 ScatterSticks(float2 pos, half3 col, float size, float prob, float lenMin, float lenMax, float thMin, float thMax, float seed, half3 woodA, half3 woodB, float aa)
            {
                // one stick per cell, kept inside its cell (the centre is at least 0.2 cell from every border and lenMax is at most 0.4 cell), so only
                // the pixel's own cell has to be looked at: this runs for every forest pixel on the screen
                float2 cell = floor(pos / size);
                float2 r = ForestHash2(cell + seed);
                if (r.x > prob) return col;
                float2 r2 = ForestHash2(cell + seed * 1.7 + 17.7);
                float2 centre = (cell + 0.2 + 0.6 * r2) * size;
                float ang = r.y * 6.2832;
                float2 dir = float2(cos(ang), sin(ang));
                float halfLen = 0.5 * lerp(lenMin, lenMax, r2.x);
                float2 d = pos - centre;
                float along = clamp(dot(d, dir), -halfLen, halfLen);
                float dist = length(d - dir * along);
                float th = lerp(thMin, thMax, r2.y);
                float m = smoothstep(th, th * 0.35, dist);
                half3 wood = lerp(woodA, woodB, frac(r2.x * 7.3 + r2.y * 3.1));
                return lerp(col, wood, m * 0.9 * aa);
            }

            // Scattered forest debris over a forest floor: fallen sticks and branches at random angles, leaf clumps of two browns, flecks of bark and
            // the odd pale patch of rotting wood. Hashed per cell, so it is random, not a pattern; it fades out where a pixel covers many of them.
            half3 ForestDebris(float2 pos, half3 col)
            {
                float aa = saturate(1.0 - length(fwidth(pos)) * 3.0);
                // leaf clumps: soft blobs a few tens of centimetres across
                float2 lc = floor(pos / 2.3 + 40.0);
                float2 lr = ForestHash2(lc);
                float2 lf = frac(pos / 2.3 + 40.0) - 0.5 - (lr - 0.5) * 0.5;
                float blob = smoothstep(0.36 + 0.1 * lr.y, 0.1, length(lf) + (SnowValueNoise(pos * 3.0) - 0.5) * 0.16);
                half3 clump = lerp(half3(0.22, 0.13, 0.06), half3(0.34, 0.20, 0.08), lr.y);
                col = lerp(col, clump, blob * step(lr.x, 0.55) * 0.55);
                // pale rotting wood
                float2 rc = floor(pos / 5.3 + 13.0);
                float2 rr = ForestHash2(rc);
                float2 rf = frac(pos / 5.3 + 13.0) - 0.5 - (rr - 0.5) * 0.4;
                col = lerp(col, half3(0.42, 0.36, 0.28), smoothstep(0.1, 0.03, length(rf * float2(1.0, 2.2))) * step(rr.x, 0.18) * 0.5 * aa);
                // bark flecks
                float2 bc = floor(pos / 0.45 + 70.0);
                float2 br = ForestHash2(bc);
                float2 bf = frac(pos / 0.45 + 70.0) - 0.5 - (br - 0.5) * 0.5;
                col = lerp(col, half3(0.30, 0.15, 0.08), smoothstep(0.1, 0.04, length(bf)) * step(br.x, 0.22) * 0.8 * aa);
                // twigs and branches
                col = ScatterSticks(pos, col, 1.7, 0.6, 0.3, 0.65, 0.014, 0.03, 3.0, half3(0.14, 0.09, 0.05), half3(0.28, 0.19, 0.11), aa);
                col = ScatterSticks(pos, col, 6.0, 0.35, 1.2, 2.3, 0.04, 0.08, 9.0, half3(0.20, 0.13, 0.07), half3(0.34, 0.26, 0.17), aa);
                return col;
            }

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
                    {
                        // 15: mixed: patches of oak floor and of pine needles (ONE of the two per pixel: evaluating both doubled the cost of every mixed forest pixel)
                        if (SnowValueNoise(pos * 0.03 + 7.0) > 0.5) c = OakWoodlandTexture(pos, half3(0,0,0));
                        else c = PineNeedleTexture(pos, half3(0,0,0));
                    }
                else if (mode < 16.5)
                    c = WillowGroveTexture(pos, half3(0,0,0));      // 16: willow grove
                else if (mode < 17.5)
                    c = SandTexture(pos, half3(0,0,0));             // 17: sand
                else
                    c = ShortGrassTexture(pos, half3(0,0,0));      // fallback
                return c;
            }

            // The ground of one biome mode at a world position (water modes give their bed texture, which the water blend below covers anyway).
            half3 BiomeLandColor(float mode, float2 pos)
            {
                if (mode > 5.5 && mode < 6.5)
                    return WetlandTexture(pos, half3(0, 0, 0));
                if (mode > 4.5 && mode < 5.5)
                {
                    float stripe = step(0.5, frac(pos.y / 1.2));   // 1.2m mower pass
                    return lerp(half3(0.10, 0.60, 0.22), half3(0.18, 0.82, 0.36), stripe);
                }
                if (mode > 3.5 && mode < 4.5)
                {
                    // Two rows to every metre square (a plant sits on each: the square is sown 2 x 2), a ridge with a furrow between. The rows run
                    // along X, or along Z when the tilled square says so (mode 4.25, see BiomeModeAt): they keep their direction from square to square.
                    float across = mode > 4.1 ? pos.x : pos.y;
                    float f = frac(across * 2.0);                  // 0.5 m per row, the furrows on the whole-metre and half-metre lines
                    float ridge = smoothstep(0.0, 0.3, f) * smoothstep(1.0, 0.7, f);
                    float grain = FBM(pos * 6.0, 2);
                    return lerp(half3(0.10, 0.045, 0.01), half3(0.26, 0.125, 0.04), ridge) * lerp(0.9, 1.1, grain);
                }
                return GetBiomeTexture(mode, pos);
            }

            // Smooth biome boundaries. The baked biome map stores discrete mode ids, which cannot be filtered, so the ground texture used to switch
            // at the (blocky) texel edge. Instead the mode is point-sampled at the four corners of a small lattice cell round the pixel, every
            // distinct mode's texture is evaluated, and they are mixed with smoothed bilinear weights: the boundary becomes a soft blend a few
            // metres wide that follows the biome shapes. Away from a boundary all four taps agree and it costs one texture, as before.
            // (The loop over the distinct modes is a real loop: see below.)
            float _TerrainBlendQuality;   // set globally by the graphics preset: 0 = hard biome edges (one texture per pixel), 1 = the soft blend

            // maple, birch, oak, pine, poplar and mixed forests: the modes whose floor carries the scattered debris (added ONCE per pixel, after the blend)
            float IsForestMode(float mode) { return ((mode > 6.5 && mode < 10.5) || (mode > 13.5 && mode < 15.5)) ? 1.0 : 0.0; }

            // The mode id at a point of the biome map, point sampled. Tilled farmland whose rows run along Z (red channel painted to 1 by
            // FarmlandSoil.cs) reads as 4.25 instead of 4, so its texture turns without being a different biome.
            float BiomeModeAt(float2 uv)
            {
                half4 s = SAMPLE_TEXTURE2D_LOD(_BiomeMap, sampler_point_clamp, uv, 0);
                float m = floor(s.a * 18.0);
                if (m > 3.5 && m < 4.5 && s.r > 0.75) m += 0.25;
                return m;
            }

            half3 BlendedBiomeGround(float2 localXZ, float2 worldXZ)
            {
                if (_TerrainBlendQuality < 0.5)
                {
                    float m0 = BiomeModeAt(localXZ / _TerrainBounds.xy);
                    half3 c0 = BiomeLandColor(m0, worldXZ);
                    if (IsForestMode(m0) > 0.5) c0 = ForestDebris(worldXZ, c0);
                    return c0;
                }
                const float cell = 3.0;
                float2 g = localXZ / cell - 0.5;
                float2 i0 = floor(g);
                float2 t = frac(g);
                t = t * t * (3.0 - 2.0 * t);
                float ws[4];
                ws[0] = (1.0 - t.x) * (1.0 - t.y);
                ws[1] = t.x * (1.0 - t.y);
                ws[2] = (1.0 - t.x) * t.y;
                ws[3] = t.x * t.y;
                float ms[4];
                [unroll] for (int k = 0; k < 4; k++)
                {
                    float2 p = (i0 + float2(k % 2, k / 2) + 0.5) * cell;
                    ms[k] = BiomeModeAt(p / _TerrainBounds.xy);
                }
                // Each distinct mode's total weight (taps on the same mode share one texture evaluation); only the TWO strongest are drawn, so a
                // pixel never pays for more than two biome textures (a third or fourth only appears at a triple junction and is a few percent).
                float mw[4];
                [unroll] for (int a2 = 0; a2 < 4; a2++)
                {
                    bool seen = false;
                    float wa = ws[a2];
                    [unroll] for (int c = 0; c < 4; c++) if (c < a2 && ms[c] == ms[a2]) seen = true;
                    [unroll] for (int d = 0; d < 4; d++) if (d > a2 && ms[d] == ms[a2]) wa += ws[d];
                    mw[a2] = seen ? 0.0 : wa;
                }
                int i1 = 0;
                [unroll] for (int k1 = 1; k1 < 4; k1++) if (mw[k1] > mw[i1]) i1 = k1;
                int i2 = -1; float w2 = 0.0;
                [unroll] for (int k2 = 0; k2 < 4; k2++) if (k2 != i1 && mw[k2] > w2) { w2 = mw[k2]; i2 = k2; }
                // a real loop of at most two passes, so the big per-biome texture code is compiled once (see the note on compile time above)
                half3 col = half3(0, 0, 0);
                float used = 0.0, forestW = 0.0;
                [loop] for (int pi = 0; pi < 2; pi++)
                {
                    int idx = pi == 0 ? i1 : i2;
                    float wgt = pi == 0 ? mw[i1] : w2;
                    if (idx < 0 || wgt <= 0.02) continue;
                    col += BiomeLandColor(ms[idx], worldXZ) * wgt;
                    used += wgt;
                    forestW += IsForestMode(ms[idx]) * wgt;
                }
                half3 blended = col / max(used, 1e-4);
                float fw = forestW / max(used, 1e-4);
                if (fw > 0.02) blended = lerp(blended, ForestDebris(worldXZ, blended), fw);   // the debris, once per pixel
                return blended;
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

            // The baked ground colour (TerrainGroundBake.cs) and whether it is ready. Global, set by the baker.
            TEXTURE2D(_GroundBake);
            SAMPLER(sampler_GroundBake);
            float _GroundBakeOn;

            // The ground's colour at a world position, before cliffs, the road, weather, light and the grid: the biome texture (softly blended at the
            // edges), with the dirt of the water bed and shore blended in across the water's smooth coverage band. Depends only on the world, never
            // on the weather or time, so it can be rendered once into a texture.
            half3 TerrainGroundBase(float2 worldXZ, float2 biomeUv)
            {
                // DIRT, NOT THE BIOME TINT: one continuous dirt palette for river, lake and pond (no per-mode seam), darkened with depth.
                float sediment = FBM(worldXZ * 0.08, 3);
                half3 dirtDark = half3(0.20, 0.14, 0.09);
                half3 dirtMid = half3(0.36, 0.26, 0.16);
                half3 dirtLight = half3(0.50, 0.38, 0.24);
                half3 waterCol = lerp(dirtDark, dirtMid, sediment);
                waterCol = lerp(waterCol, dirtLight, smoothstep(0.6, 0.85, FBM(worldXZ * 0.3 + 7.0, 2)) * 0.45);
                float2 wm = SAMPLE_TEXTURE2D_LOD(_WaterMask, sampler_linear_clamp, biomeUv, 0).rg;
                waterCol *= lerp(1.0, 0.65, saturate(wm.x));
                half3 land = BlendedBiomeGround(worldXZ, worldXZ);
                return lerp(land, waterCol, smoothstep(0.02, 0.5, wm.y));
            }
