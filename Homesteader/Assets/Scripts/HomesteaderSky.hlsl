#ifndef HOMESTEADER_SKY_INCLUDED
#define HOMESTEADER_SKY_INCLUDED

// Shared sky helpers: procedural drifting clouds (their shadows on the ground, their reflection in water)
// and a procedural star field. Everything is driven by globals set from C# (CloudSystem, DayNightCycle).
// Include after Core.hlsl (uses _MainLightPosition).

float4 _CloudParams;   // x = coverage 0..1, y = shadow strength 0..1 (0 = Cloud Shadows off), z/w = scroll offset in metres
float4 _SkyParams;     // x = night amount 0 (day) .. 1 (night)

#define HS_CLOUD_HEIGHT 140.0

float SkyHash21(float2 p)
{
    p = frac(p * float2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return frac(p.x * p.y);
}

float SkyNoise(float2 p)
{
    float2 i = floor(p);
    float2 f = frac(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = SkyHash21(i);
    float b = SkyHash21(i + float2(1, 0));
    float c = SkyHash21(i + float2(0, 1));
    float d = SkyHash21(i + float2(1, 1));
    return lerp(lerp(a, b, f.x), lerp(c, d, f.x), f.y);
}

// Cloud thickness 0..1 over a world XZ position. Coverage moves the threshold: none when clear, nearly solid when overcast.
float CloudDensity(float2 xz)
{
    float2 q = (xz + _CloudParams.zw) * 0.012;
    float n = SkyNoise(q) * 0.55 + SkyNoise(q * 2.1 + 7.3) * 0.3 + SkyNoise(q * 4.3 + 3.1) * 0.15;
    float t = lerp(0.98, 0.30, saturate(_CloudParams.x));
    return saturate((n - t) / 0.18);
}

// 1 = in sun, lower = under a cloud's shadow. The sun's ray is followed up to the cloud layer.
float CloudShadowFactor(float3 posWS)
{
    if (_CloudParams.y <= 0.001) return 1.0;
    float3 L = _MainLightPosition.xyz;
    float2 xz = posWS.xz + L.xz / max(L.y, 0.25) * HS_CLOUD_HEIGHT;
    float strength = _CloudParams.y * (1.0 - 0.7 * _SkyParams.x);
    return 1.0 - strength * CloudDensity(xz);
}

// Cloud thickness seen along a ray that leaves the surface (for the reflection in water).
float CloudDensityAlongRay(float3 posWS, float3 dir)
{
    if (dir.y < 0.04) return 0.0;
    float t = (HS_CLOUD_HEIGHT - posWS.y) / dir.y;
    return CloudDensity(posWS.xz + dir.xz * t) * smoothstep(0.04, 0.22, dir.y);
}

// Stars in a direction (hashed cells with a jittered point and a slow twinkle).
float3 SkyStars(float3 d, float time)
{
    if (d.y < 0.05) return 0;
    float2 p = d.xz / (d.y + 0.35) * 55.0;
    float2 c = floor(p);
    float2 f = frac(p) - 0.5;
    float h = SkyHash21(c);
    float2 jit = float2(SkyHash21(c + 1.7), SkyHash21(c + 5.3)) - 0.5;
    float dist = length(f - jit * 0.6);
    float tw = 0.65 + 0.35 * sin(time * (1.5 + h * 3.0) + h * 40.0);
    float s = step(0.965, h) * smoothstep(0.14, 0.0, dist) * tw;
    float3 tint = lerp(float3(0.8, 0.9, 1.0), float3(1.0, 0.95, 0.85), frac(h * 17.0));
    return s * tint * smoothstep(0.05, 0.3, d.y);
}

#endif
