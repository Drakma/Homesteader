Shader "Homesteader/OutlineComposite"
{
    // Fullscreen blit shader: samples the ALREADY-BLURRED silhouette coverage
    // (_BlitTexture, written by OutlineBlur.shader's two passes - the blur
    // merges small gaps between disconnected leaf-card triangles etc. into one
    // solid blob) and dilates it by _OutlineWidthPx. A pixel outside the
    // silhouette but within that radius of an inside pixel gets the outline
    // glow; pixels fully inside or far outside stay untouched (alpha 0 ->
    // normal alpha blend leaves the camera color as-is), so only the true
    // screen-space rim glows - no per-triangle edges.
    Properties
    {
        _OutlineColor ("Outline Color", Color) = (0.35, 0.9, 1.0, 0.9)
        _OutlineWidthPx ("Outline Width (px)", Range(0, 12)) = 3
        _CoverageThreshold ("Coverage Threshold", Range(0, 1)) = 0.12
        _PulseSpeed ("Pulse Speed", Range(0, 10)) = 2.5
        _PulseAmount ("Pulse Amount", Range(0, 1)) = 0.25
    }

    SubShader
    {
        Tags { "RenderPipeline" = "UniversalPipeline" }

        Pass
        {
            Name "OutlineComposite"
            ZTest Always
            ZWrite Off
            Cull Off
            Blend SrcAlpha OneMinusSrcAlpha

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.core/Runtime/Utilities/Blit.hlsl"

            half4 _OutlineColor;
            float _OutlineWidthPx;
            float _CoverageThreshold;
            float _PulseSpeed;
            float _PulseAmount;

            // Blurred coverage -> a near-binary "is this blob interior" test. The
            // blur pass already merged small gaps, so a modest threshold turns
            // the soft gradient back into a clean solid silhouette to dilate.
            float Filled(float2 uv)
            {
                float coverage = SAMPLE_TEXTURE2D_X(_BlitTexture, sampler_LinearClamp, uv).a;
                return smoothstep(_CoverageThreshold, _CoverageThreshold + 0.05, coverage);
            }

            half4 Frag(Varyings input) : SV_Target
            {
                float2 uv = input.texcoord;
                float2 texel = _BlitTexture_TexelSize.xy;
                float pulse = 1.0 + sin(_Time.y * _PulseSpeed) * _PulseAmount;
                float r = max(_OutlineWidthPx * pulse, 0.001);

                float center = Filled(uv);
                float maxN = center;

                const int kSamples = 8;
                [unroll]
                for (int i = 0; i < kSamples; i++)
                {
                    float ang = (i / (float)kSamples) * 6.2831853;
                    float2 off = float2(cos(ang), sin(ang)) * texel * r;
                    maxN = max(maxN, Filled(uv + off));
                }

                float edge = saturate(maxN - center);
                return half4(_OutlineColor.rgb, _OutlineColor.a * edge);
            }
            ENDHLSL
        }
    }
}
