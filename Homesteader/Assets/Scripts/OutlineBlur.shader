Shader "Homesteader/OutlineBlur"
{
    // Separable box blur of the silhouette mask. Sparse foliage (many gapped
    // leaf-card triangles) leaves real gaps in the sharp mask, which would
    // otherwise outline each leaf cluster individually. Blurring first merges
    // those small gaps so the composite pass's edge test sees one solid blob
    // for the whole canopy instead of dozens of tiny ones.
    Properties
    {
        _BlurRadiusPx ("Blur Radius (px)", Range(0, 24)) = 8
    }

    SubShader
    {
        Tags { "RenderPipeline" = "UniversalPipeline" }

        Pass
        {
            Name "BlurHorizontal"
            ZTest Always
            ZWrite Off
            Cull Off
            Blend Off

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.core/Runtime/Utilities/Blit.hlsl"

            float _BlurRadiusPx;

            half4 Frag(Varyings input) : SV_Target
            {
                float2 texel = _BlitTexture_TexelSize.xy;
                const int kTaps = 9;
                half sum = 0;
                [unroll]
                for (int i = 0; i < kTaps; i++)
                {
                    float t = (i / (float)(kTaps - 1)) * 2.0 - 1.0; // -1..1
                    float2 uv = input.texcoord + float2(t * _BlurRadiusPx * texel.x, 0);
                    sum += SAMPLE_TEXTURE2D_X(_BlitTexture, sampler_LinearClamp, uv).a;
                }
                return half4(0, 0, 0, sum / kTaps);
            }
            ENDHLSL
        }

        Pass
        {
            Name "BlurVertical"
            ZTest Always
            ZWrite Off
            Cull Off
            Blend Off

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.core/Runtime/Utilities/Blit.hlsl"

            float _BlurRadiusPx;

            half4 Frag(Varyings input) : SV_Target
            {
                float2 texel = _BlitTexture_TexelSize.xy;
                const int kTaps = 9;
                half sum = 0;
                [unroll]
                for (int i = 0; i < kTaps; i++)
                {
                    float t = (i / (float)(kTaps - 1)) * 2.0 - 1.0;
                    float2 uv = input.texcoord + float2(0, t * _BlurRadiusPx * texel.y);
                    sum += SAMPLE_TEXTURE2D_X(_BlitTexture, sampler_LinearClamp, uv).a;
                }
                return half4(0, 0, 0, sum / kTaps);
            }
            ENDHLSL
        }
    }
}
