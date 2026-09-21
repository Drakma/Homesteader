Shader "Homesteader/GenerativeTerrainURP"
{
    Properties
    {
        _BiomeMap ("Biome Control Map (R=Mode, G=Moisture, B=Nutrients, A=Slope)", 2D) = "black" {}
        _TerrainBounds ("Terrain Bounds (X, Z, Height, 0)", Vector) = (500.0, 500.0, 60.0, 0.0)
        _NormalStrength ("Facet Normal Strength", Range(0, 1)) = 0.25
        _NutrientDarkening ("Nutrient Soil Darkening", Range(0, 1)) = 0.35
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
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS
            #pragma multi_compile _ _SHADOWS_SOFT

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

            CBUFFER_START(UnityPerMaterial)
                float4 _TerrainBounds;
                float _NormalStrength;
                float _NutrientDarkening;
            CBUFFER_END

            // Global Weather parameters set via Shader.SetGlobalVector("_WeatherGroundEffects", ...)
            float4 _WeatherGroundEffects;

            // Hash for 2D cell grid
            float2 Hash22(float2 p)
            {
                float3 p3 = frac(float3(p.xyx) * float3(443.897, 441.423, 437.195));
                p3 += dot(p3, p3.yzx + 19.19);
                return frac((p3.xx + p3.yz) * p3.zy);
            }

            // Continuous Domain-Warped Voronoi Cellular Noise for Organic Amorphous Biome Blobs
            float VoronoiBiome(float2 pos, float scale)
            {
                // Multi-harmonic domain warping transforms straight cell edges into fluid, flowing organic liquid contours
                float2 warp = float2(
                    sin(pos.y * 0.020 + pos.x * 0.010) * 18.0 + cos(pos.y * 0.050) * 7.0,
                    cos(pos.x * 0.020 + pos.y * 0.010) * 18.0 + sin(pos.x * 0.050) * 7.0
                );
                float2 p = (pos + warp) * scale;
                float2 ip = floor(p);
                float2 fp = frac(p);

                float minDist = 10.0;
                float2 cellId = float2(0.0, 0.0);

                [unroll]
                for (int j = -1; j <= 1; j++)
                {
                    [unroll]
                    for (int i = -1; i <= 1; i++)
                    {
                        float2 neighbor = float2((float)i, (float)j);
                        float2 pt = Hash22(ip + neighbor);
                        float2 diff = neighbor + pt - fp;
                        float dist = dot(diff, diff);
                        if (dist < minDist)
                        {
                            minDist = dist;
                            cellId = ip + neighbor;
                        }
                    }
                }

                // Deterministic pseudo-random value per cell
                return frac(sin(dot(cellId, float2(12.9898, 78.233))) * 43758.5453);
            }

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

                // 1. Water System: Central Winding River (~7m wide) and Kettle Pond Basin (~24m radius)
                float riverX = 220.0 + sin(z * 0.015) * 45.0 + sin(z * 0.035 + 1.2) * 18.0;
                float distToRiver = abs(x - riverX);

                float2 pondCenter = float2(220.0, 210.0);
                float distToPond = distance(float2(x, z), pondCenter);
                float pAngle = atan2(z - pondCenter.y, x - pondCenter.x);
                float pondRadius = 24.0 + sin(pAngle * 3.0) * 5.0 + cos(pAngle * 4.0) * 3.0;

                bool isRiver = distToRiver < 3.8;
                bool isPond = distToPond < pondRadius;
                bool isWater = isRiver || isPond;

                // Shoreline Wetland Buffer (~8m buffer along creek and pond)
                bool isWetland = !isWater && ((distToRiver < 8.0) || (distToPond < (pondRadius + 7.0)));

                // Organic domain-warped coordinates for man-made plots (softens sharp CAD edges into natural shapes)
                float ox = x + sin(z * 0.08) * 3.0 + cos(x * 0.04) * 1.5;
                float oz = z + cos(x * 0.08) * 3.0 + sin(z * 0.04) * 1.5;

                // 2. Domestic Homestead Yard (Lawn ~26m radius with soft wavy edge)
                float distToLawn = distance(float2(ox, oz), float2(285.0, 210.0));
                float lawnAngle = atan2(oz - 210.0, ox - 285.0);
                float lawnR = 26.0 + sin(lawnAngle * 4.0) * 3.0;
                bool isLawn = !isWater && !isWetland && (distToLawn < lawnR);

                // 3. Agricultural Farmland (Soft rounded tilled plots)
                bool isFarm1 = abs(ox - 335.0) < 30.0 && abs(oz - 215.0) < 24.0;
                bool isFarm2 = abs(ox - 160.0) < 19.0 && abs(oz - 170.0) < 15.0;
                bool isFarmland = !isWater && !isWetland && !isLawn && (isFarm1 || isFarm2);

                // 4. Color & Biome Evaluation
                if (isWater)
                {
                    half3 deepWater = isPond ? half3(0.04, 0.24, 0.54) : half3(0.06, 0.36, 0.65);
                    half3 shallowWater = half3(0.15, 0.65, 0.82);

                    // Flowing directional river ripples (smooth flowing waves, zero checkerboard)
                    float flow = sin((posWS.x * 0.4 + posWS.z * 1.1) * 0.8 + _Time.y * 1.8) * 0.5
                               + cos((posWS.z * 1.3 - posWS.x * 0.3) * 0.6 - _Time.y * 2.2) * 0.5;
                    col = lerp(deepWater, shallowWater, saturate(flow * 0.35 + 0.35));

                    // Stylized crisp white foam edge along river and pond banks
                    float edgeDist = isRiver ? (3.8 - distToRiver) : (pondRadius - distToPond);
                    if (edgeDist < 0.45)
                    {
                        col = lerp(col, half3(0.90, 0.96, 1.0), 0.85); // Crisp shoreline foam
                    }
                }
                else if (isWetland)
                {
                    // Riverbank sandy gravel & moist shoreline silt
                    half3 riverSand = half3(0.52, 0.48, 0.38);
                    half3 moistLoam = half3(0.35, 0.32, 0.22);
                    float gravelDither = step(0.5, frac(posWS.x * 2.0 + posWS.z * 2.0));
                    col = lerp(riverSand, moistLoam, gravelDither * 0.4);
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
                    // Organic Amorphous Biome Blobs via Domain-Warped Voronoi Cellular Noise (~50m cells)
                    float bRand = VoronoiBiome(float2(x, z), 0.020);

                    // Natural balanced distribution across 8 terrestrial biomes (zero concentric rings)
                    if (bRand < 0.22)
                    {
                        col = half3(0.20, 0.65, 0.28); // Pasture Meadow
                    }
                    else if (bRand < 0.40)
                    {
                        col = half3(0.25, 0.78, 0.34); // Lush Vivid Prairie
                    }
                    else if (bRand < 0.52)
                    {
                        col = half3(0.55, 0.82, 0.22); // Luminous Lime Birch Grove
                    }
                    else if (bRand < 0.64)
                    {
                        col = half3(0.76, 0.32, 0.08); // Vibrant Amber Autumn Maple
                    }
                    else if (bRand < 0.74)
                    {
                        col = half3(0.12, 0.42, 0.16); // Deep Hardwood Oak Woodland
                    }
                    else if (bRand < 0.83)
                    {
                        col = half3(0.38, 0.62, 0.18); // Fresh Spring Poplar Forest
                    }
                    else if (bRand < 0.92)
                    {
                        col = half3(0.10, 0.28, 0.14); // Dark Evergreen Pine Hills
                    }
                    else
                    {
                        col = half3(0.78, 0.48, 0.12); // Arid Sun-baked Clay Scrub
                    }
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

                if (!isWater)
                {
                    // Darken and enrich ground saturation when soaked with rain
                    if (globalWet > 0.01)
                    {
                        col = lerp(col, col * 0.68, globalWet * 0.75);
                    }

                    // Snow accumulates on upward facing surfaces (normalWS.y > 0.25)
                    if (globalSnow > 0.01)
                    {
                        float upwardBias = saturate((normWS.y - 0.25) / 0.55);
                        float snowNoise = frac(sin(dot(posWS.xz, float2(12.9898, 78.233))) * 43758.5453);
                        float snowThreshold = 1.0 - globalSnow;
                        float snowCoverage = saturate((upwardBias - snowThreshold * 0.5) / 0.5);

                        half3 snowColor = half3(0.92, 0.95, 0.99); // Soft crystalline winter white
                        col = lerp(col, snowColor, snowCoverage * globalSnow);
                    }
                }

                // Cel / low-poly faceted lighting
                Light mainLight = GetMainLight();
                float ndotl = max(0.0, dot(normWS, mainLight.direction));
                float celLight = step(0.12, ndotl) * 0.35 + step(0.45, ndotl) * 0.35 + 0.3;
                half3 finalRGB = col * (mainLight.color * celLight);

                return half4(finalRGB, 1.0);
            }
            ENDHLSL
        }
    }
    FallBack "Hidden/Universal Render Pipeline/FallbackError"
}
