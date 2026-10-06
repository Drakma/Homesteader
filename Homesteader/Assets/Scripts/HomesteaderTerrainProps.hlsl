// The terrain shader's per-material constants. Every pass of GenerativeTerrainURP.shader includes this, so all passes share ONE UnityPerMaterial
// layout (a pass that lacks it makes the shader SRP-batcher incompatible).
            CBUFFER_START(UnityPerMaterial)
                float4 _TerrainBounds;
                float4 _RoadParams; // x = lateral range (m), y = road half width (m)
                float _NormalStrength;
                float _NutrientDarkening;
                half4 _GridColor;
                float _GridLineWidth;
                float _GridOpacity;

            CBUFFER_END
