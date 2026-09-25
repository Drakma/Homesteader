// Draws footprints into / fades the top-down snow footprint mask (R8 RenderTexture).
// Driven by SnowFootprints.cs through Graphics.Blit. The terrain shader reads the mask
// (_SnowFootprintTex) and un-covers snow wherever it is > 0.
Shader "Hidden/Homesteader/FootprintStamp"
{
    SubShader
    {
        Cull Off ZWrite Off ZTest Always

        // Pass 0: stamp one boot print. Max blend so overlapping prints don't add up.
        Pass
        {
            BlendOp Max
            Blend One One
            CGPROGRAM
            #pragma vertex vert_img
            #pragma fragment frag
            #include "UnityCG.cginc"

            float4 _StampCenter;   // xy = centre in mask UV
            float4 _StampDir;      // xy = unit forward direction in world XZ
            float4 _StampHalf;     // xy = half extents in metres (x = width/2, y = length/2)
            float4 _WorldSize;     // xy = mask coverage in metres

            float4 frag(v2f_img i) : SV_Target
            {
                float2 p = (i.uv - _StampCenter.xy) * _WorldSize.xy; // metres from centre
                float2 fwd = _StampDir.xy;
                float2 right = float2(fwd.y, -fwd.x);
                float2 q = float2(dot(p, right), dot(p, fwd)) / _StampHalf.xy;
                // Boot shape: narrower toward the heel, softly rounded edge.
                float narrow = lerp(0.72, 1.0, saturate(q.y * 0.5 + 0.5));
                q.x /= narrow;
                float r = pow(abs(q.x), 2.6) + pow(abs(q.y), 2.6);
                float a = 1.0 - smoothstep(0.55, 1.0, r);
                return float4(a, a, a, a);
            }
            ENDCG
        }

        // Pass 2: stamp a capsule (line segment with radius; a circle when A == B).
        // Used for snow removal (shovel, plow, vehicles).
        Pass
        {
            BlendOp Max
            Blend One One
            CGPROGRAM
            #pragma vertex vert_img
            #pragma fragment frag
            #include "UnityCG.cginc"

            float4 _SegA;        // xy = segment start in mask UV
            float4 _SegB;        // xy = segment end in mask UV
            float4 _CapsuleR;    // x = radius in metres
            float4 _WorldSize;   // xy = mask coverage in metres

            float4 frag(v2f_img i) : SV_Target
            {
                float2 p = (i.uv - _SegA.xy) * _WorldSize.xy;
                float2 ab = (_SegB.xy - _SegA.xy) * _WorldSize.xy;
                float len2 = dot(ab, ab);
                float t = len2 > 1e-8 ? saturate(dot(p, ab) / len2) : 0.0;
                float d = length(p - ab * t);
                float a = 1.0 - smoothstep(_CapsuleR.x * 0.8, _CapsuleR.x, d);
                return float4(a, a, a, a);
            }
            ENDCG
        }

        // Pass 1: fade the whole mask by _FadeAmount (snow slowly refilling the prints).
        Pass
        {
            BlendOp RevSub
            Blend One One
            CGPROGRAM
            #pragma vertex vert_img
            #pragma fragment frag
            #include "UnityCG.cginc"

            float _FadeAmount;

            float4 frag(v2f_img i) : SV_Target
            {
                return float4(_FadeAmount, _FadeAmount, _FadeAmount, _FadeAmount);
            }
            ENDCG
        }
    }
}
