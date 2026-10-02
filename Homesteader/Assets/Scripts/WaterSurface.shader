Shader "Homesteader/WaterSurface"
{
    Properties
    {
        _WaterMask ("Water Mask (R=depth, G=water flag)", 2D) = "white" {}
        _TerrainBounds ("Terrain Bounds (X, Z, Height, 0)", Vector) = (500.0, 500.0, 60.0, 0.0)
        _BaseColor ("Base Water Color", Color) = (0.02, 0.10, 0.19, 0.92)
        _DeepDarken ("Deep Darken Amount", Range(0, 1)) = 0.7
        _RippleAmplitude ("Ripple Amplitude", Range(0, 0.3)) = 0.12
        _WaveSpeed ("Wave Speed (1 = physical)", Range(0.02, 1.5)) = 0.2
        _RippleFrequency ("Ripple Frequency", Range(0.5, 5.0)) = 1.8
        _FoamWidth ("Foam Width (metres)", Range(0.3, 3.0)) = 0.8
        _FoamColor ("Foam Color", Color) = (0.85, 0.92, 0.98, 1.0)
    }

    SubShader
    {
        Tags { "RenderType"="Transparent" "RenderPipeline"="UniversalPipeline" "Queue"="Transparent" }
        LOD 200

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode"="UniversalForward" }

            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
            Cull Back

            HLSLPROGRAM
            // Real (wall-clock) time, set by RealTimeClock - unaffected by pausing/timeScale.
            float _RealTime;
            float _WaterReflectionQuality;   // set globally by the graphics preset: 0 = just the sun glint, 1 = the sky is reflected too
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE
            #pragma multi_compile _ _SHADOWS_SOFT

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "HomesteaderSky.hlsl"

            TEXTURE2D(_WaterMask);
            SAMPLER(sampler_WaterMask);

            struct Attributes
            {
                float4 positionOS : POSITION;
                float2 uv         : TEXCOORD0;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float2 uv         : TEXCOORD1;
            };

            CBUFFER_START(UnityPerMaterial)
                float4 _TerrainBounds;
                half4 _BaseColor;
                float _DeepDarken;
                float _RippleAmplitude;
                float _RippleFrequency;
                float _WaveSpeed;
                float _FoamWidth;
                half4 _FoamColor;
            CBUFFER_END

            // Hash-based value noise for ripples (GPU-side, cheap)
            float hash21(float2 p)
            {
                return frac(sin(dot(p, float2(127.1, 311.7))) * 43758.5453);
            }

            float valueNoise2D(float2 p)
            {
                float2 i = floor(p);
                float2 f = frac(p);
                float2 u = f * f * (3.0 - 2.0 * f);
                return lerp(lerp(hash21(i), hash21(i + float2(1, 0)), u.x),
                            lerp(hash21(i + float2(0, 1)), hash21(i + float2(1, 1)), u.x), u.y);
            }

            // Global wind, set every frame by WeatherEffectsManager and shared with the grass:
            // (dirX, dirZ, speed, gust 0..1). Zero when nothing is driving it, so a calm default applies.
            float4 _GrassWindParams;

            // (snowCoverage, groundWetness, rainNow 0..1, unused) - set by WeatherEffectsManager. rainNow is the
            // smoothed "raining right now" value, so ripples fade in and out with the weather.
            float4 _WeatherGroundEffects;
            float RainNow() { return saturate(_WeatherGroundEffects.z); }

            // The water's own wind, from RealTimeClock: (dirX, dirZ, gust, waveClock). Direction turns very slowly
            // and the clock ACCUMULATES the gust's speed factor - both are what stop the waves racing when the
            // gameplay wind changes (see RealTimeClock). Zero before it is set, so a calm default applies.
            float4 _WaterWind;

            void GetWind(out float2 dir, out float gust)
            {
                float2 d = _WaterWind.xy;
                if (dot(d, d) < 1e-4) { dir = float2(1, 0); gust = 0.3; return; }
                dir = normalize(d);
                gust = saturate(_WaterWind.z);
            }

            // WIND-DRIVEN WAVES. Three travelling sine waves (long swell, mid chop, short ripple) whose
            // headings are spread around the wind direction and drift slowly, so the surface is never a
            // clean grid. Wind changes them three ways: amplitude grows with the gust strength, waves
            // travel faster in stronger wind, and a patchy "gust front" noise advected DOWNWIND makes some
            // stretches of water rougher than others. Returns (height, dh/dx, dh/dz) so the fragment stage
            // can light the same surface it displaced.
            float3 WindWaves(float2 p, float tIgnored)
            {
                // Wave clock: real seconds, with the wind's speed factor already integrated in (RealTimeClock).
                float t = _WaterWind.w;
                float2 wd; float gust;
                GetWind(wd, gust);

                // Rain roughens the surface too, on top of whatever the wind is doing.
                float roughness = 0.25 + 1.5 * gust + 0.6 * RainNow();
                // Rougher patches move with the wind at a fraction of its speed.
                // THE FAST FLICKER WAS HERE. The noise is sampled at p * 0.06, so its coordinate moves 1/0.06 =
                // 16.7 world metres per unit of offset: an offset rate of 0.29/s was a 4.8 m/s sweep, and the
                // roughness patches raced across the water. The offset is now specified in WORLD metres per
                // second (a slow drift, ~0.4 m/s) and scaled into noise space.
                float patchSpeed = 0.7 * _WaveSpeed * 2.0;
                // Wide calm and choppy stretches (the old 0.7 to 1.3 range made the whole surface equally busy).
                float patch = 0.3 + 1.2 * valueNoise2D((p - wd * t * patchSpeed) * 0.035);
                float scale = _RippleAmplitude * roughness * patch;

                const float wavelength[3] = { 9.0, 5.0, 2.8 };   // longer waves: fewer crests across the same water
                const float spread[3]     = { 0.0, 0.45, -0.6 };
                const float amp[3]        = { 0.60, 0.20, 0.06 };   // the short ripples were what made the surface look busy

                float3 acc = float3(0, 0, 0);
                [unroll]
                for (int i = 0; i < 3; i++)
                {
                    // Heading drift kept ~0.0006 rad/s: phase error grows with distance from the origin (see RealTimeClock).
                    float ang = spread[i] + sin(t * 0.004 + i * 2.1) * 0.15;
                    float cs = cos(ang), sn = sin(ang);
                    float2 dir = float2(wd.x * cs - wd.y * sn, wd.x * sn + wd.y * cs);
                    float k = 6.2832 / wavelength[i] * (_RippleFrequency / 1.8);
                    float omega = sqrt(9.81 * k) * _WaveSpeed; // the gust's speed factor lives in the accumulated clock
                    float phase = dot(p, dir) * k - omega * t;
                    float h = amp[i] * sin(phase);
                    float dh = amp[i] * k * cos(phase);
                    acc += float3(h, dh * dir.x, dh * dir.y);
                }
                return acc * scale;
            }

            // 0..1 how much of the water is frozen over. Set by WeatherEffectsManager from the temperature.
            float _WaterFreeze;

            // ICE. Freezes from the SHORE INWARDS: the mask's B channel is the distance from the bank in
            // metres (0..32), and the ice front sits at `_WaterFreeze * reach` metres in from it, with a ragged
            // noise-perturbed edge. How far in the front can ever get depends on the kind of water (mask A):
            //   pond  (A=1): still water, reach is far larger than any pond, so it freezes across.
            //   river (A=0): moving water keeps an open channel - the front stops ~3.5 m from each bank, so a
            //                narrow river (<~7 m across) freezes solid and a wide one stays open in the middle.
            float IceAmount(float4 mask, float2 xz)
            {
                float freeze = saturate(_WaterFreeze);
                if (freeze <= 0.001) return 0.0;
                float dist = mask.b * 32.0;
                dist += (valueNoise2D(xz * 0.45) - 0.5) * 1.6 + (valueNoise2D(xz * 1.7) - 0.5) * 0.5;
                float reach = lerp(3.5, 80.0, step(0.5, mask.a));
                float front = freeze * reach;
                return smoothstep(0.0, 0.6, front - dist);
            }

            float2 hash22(float2 p)
            {
                return float2(hash21(p), hash21(p + 47.31));
            }

            // RAINDROP IMPACT RINGS. The surface is cut into cells; each cell owns one drop that lands at a
            // random spot, sends out an expanding ring, and fades over its life before the next one starts
            // (staggered per cell so they never pulse in sync). `rain` decides how many cells are active at
            // all, so a drizzle is a few scattered rings and a storm covers the water. Returns
            // (ring height, dh/dx, dh/dz) in the same form as WindWaves, plus the ring mask in w.
            float4 RainRings(float2 p, float rain, float cellSize, float seed)
            {
                float2 q = p / cellSize;
                float2 base = floor(q);
                float2 f = frac(q);
                float4 acc = float4(0, 0, 0, 0);
                [unroll]
                for (int oz = -1; oz <= 1; oz++)
                {
                    [unroll]
                    for (int ox = -1; ox <= 1; ox++)
                    {
                        float2 o = float2(ox, oz);
                        float2 id = base + o + seed;
                        float2 h = hash22(id);
                        if (h.x > rain) continue; // this cell has no drop right now
                        float2 centre = o + 0.15 + 0.7 * hash22(id + 13.7);
                        float phase = frac(_RealTime * (0.7 + 0.5 * h.y) * (_WaveSpeed * 1.6) + hash21(id + 5.3));
                        float radius = phase * 0.55;
                        float2 d = f - centre;
                        float dist = max(length(d), 1e-4);
                        float w = 0.05;
                        float x = (dist - radius) / w;
                        float ring = exp(-x * x);
                        float fade = (1.0 - phase) * (1.0 - phase);
                        float dhdd = -2.0 * x / w * ring * fade;   // slope across the ring
                        float2 dir = d / dist;
                        acc.x += ring * fade;
                        acc.yz += dir * dhdd / cellSize;
                        acc.w = max(acc.w, ring * fade);
                    }
                }
                return acc;
            }

            Varyings vert(Attributes input)
            {
                Varyings output;
                float3 posOS = input.positionOS.xyz;

                // Vertex displacement: wind-driven waves (see WindWaves).
                float t = _RealTime;
                float displacement = WindWaves(posOS.xz, t).x;
                float4 iceMask = SAMPLE_TEXTURE2D_LOD(_WaterMask, sampler_WaterMask, input.uv, 0);
                displacement *= 1.0 - IceAmount(iceMask, posOS.xz); // ice is flat

                // Fade ripples out right at the shore: the ripple wavelength (a few metres) is close to the
                // shoreline's own tooth spacing, so undamped ripples bob the edge vertices up and down enough
                // to read as a sharp zigzag in an isometric near-edge-on view - the water's XZ outline was
                // already smooth, it was the ripple HEIGHT wobbling along that outline that looked jagged.
                float shoreCoverage = SAMPLE_TEXTURE2D_LOD(_WaterMask, sampler_WaterMask, input.uv, 0).g;
                displacement *= smoothstep(0.4, 0.9, shoreCoverage);
                // Ripples must never dip the surface below the bed. Near the shore the water is only a few
                // centimetres deep, so an undamped +-0.15m ripple lifted the bed clear of the surface and the
                // terrain showed through. The mask's R channel is depth/4m; scale the ripple with it.
                float bedDepthN = SAMPLE_TEXTURE2D_LOD(_WaterMask, sampler_WaterMask, input.uv, 0).r;
                displacement *= smoothstep(0.03, 0.10, bedDepthN);
                // What is left of the ripple can only push the surface UP, never below the flat water level.
                displacement = max(displacement, -0.02);

                posOS.y += displacement;

                float3 posWS = TransformObjectToWorld(posOS);
                output.positionWS = posWS;
                output.positionCS = TransformWorldToHClip(posWS);
                output.uv = input.uv;
                return output;
            }

            half4 frag(Varyings input) : SV_Target
            {
                float3 posWS = input.positionWS;
                float2 uv = input.uv;

                // Sample water mask: R = depth (0-1), G = smoothed shore coverage (0..1, blurred on the CPU
                // side - see BlurCoverage in HomesteaderTerrainGenerator.cs). Used to be a hard 0/1 flag that
                // this shader discarded on, which - combined with the mesh being built one quad per whole
                // metre cell - gave a literal staircase shoreline. Fading alpha across the blurred band
                // instead of cutting on it is what actually makes the edge read as smooth.
                float4 mask = SAMPLE_TEXTURE2D(_WaterMask, sampler_WaterMask, uv);
                clip(mask.g - 0.02); // still skip fully-dry pixels outright, cheap early-out
                float depth = mask.r; // 0 = shallow, 1 = deep
                float ice = IceAmount(mask, posWS.xz);

                // THE SHORELINE IS THE 0.5 CONTOUR OF A SMOOTH FIELD. The mask is a Gaussian blur of the fine
                // water mask (see GaussianCoverage), and the mesh extends past that contour, so the visible edge
                // is drawn here - an anti-aliased ramp across the contour - and never by a polygon boundary.
                float g = mask.g;
                float2 wdirEdge; float wgustEdge;
                GetWind(wdirEdge, wgustEdge);
                wgustEdge = saturate(wgustEdge);
                // The waterline laps in and out: a slow swell, offset along the shore by noise so it is not in
                // lockstep, moves the contour a few tenths of a metre. It stays on the smooth field, so the
                // edge is still never jagged. Livelier in wind.
                float lapPhase = _RealTime * (0.55 + 0.25 * wgustEdge) + valueNoise2D(posWS.xz * 0.22) * 6.2831;
                float lap = sin(lapPhase) * 0.6 + sin(lapPhase * 2.1 + 1.3) * 0.25;
                // Only ever RECEDE from the smooth shoreline, never advance past it: out beyond the contour the bank sits
                // within centimetres of the water plane, and water drawn there washes the bank a cyan glow.
                float lapIn = saturate(lap * 0.5 + 0.5);
                float contour = 0.5 + lapIn * (0.06 + 0.03 * wgustEdge);
                float edgeAlpha = smoothstep(contour - 0.08, contour + 0.08, g);
                float shoreAlpha = saturate((g - 0.5) * 4.0); // damps ripple normals right at the edge


                // Single base color, darkened by depth
                half4 waterCol = _BaseColor;
                waterCol.rgb *= (1.0 - depth * _DeepDarken);

                // Colour variation that travels WITH the wind, so the water visibly streams downwind.
                float2 wdir; float wgust;
                GetWind(wdir, wgust);
                float flow = valueNoise2D((posWS.xz - wdir * _WaterWind.w * 0.7 * _WaveSpeed * 2.0) * 0.5) * 2.0 - 1.0;
                waterCol.rgb = lerp(waterCol.rgb * 0.85, waterCol.rgb * 1.15, saturate(flow * 0.3 + 0.5));
                // The base colour is not lit by the sun, so without this the water stayed daytime blue after dark.
                waterCol.rgb *= lerp(1.0, 0.14, _SkyParams.x);

                // Celestial reflection: specular highlight from the main light
                Light mainLight = GetMainLight();
                float3 viewDir = normalize(_WorldSpaceCameraPos - posWS);
                // Perturb normal with the same ripple function, faded at the shore for the same reason the
                // vertex displacement is (see vert()) - an undamped perturbation here reads as a speckled
                // sparkle pattern right along the edge instead of a smooth specular sheen.
                // Slope of the very waves the vertices were displaced by, so the sheen follows the wind.
                float3 wave = WindWaves(posWS.xz, _RealTime);
                float damp = shoreAlpha * smoothstep(0.03, 0.10, depth) * (1.0 - ice);
                // Rain: two layers of drop rings at different scales, bent into the normal.
                float rain = RainNow();
                float4 rings = float4(0, 0, 0, 0);
                if (rain > 0.001)
                {
                    rings = RainRings(posWS.xz, rain, 1.3, 0.0) + RainRings(posWS.xz + 9.1, rain * 0.8, 0.85, 31.0);
                }
                float2 slope = wave.yz + rings.yz * 0.12;
                float3 normal = normalize(float3(-slope.x * damp, 1.0, -slope.y * damp));

                float3 halfDir = normalize(viewDir + mainLight.direction);
                float spec = pow(max(0.0, dot(normal, halfDir)), 64.0);
                half3 reflection = mainLight.color * spec * 0.6;
                waterCol.rgb += reflection;
                half3 nightAdd = half3(0, 0, 0);
                // Sky reflection (High and Ultra): the environment reflected by the rippled surface, strongest at grazing angles (Fresnel).
                if (_WaterReflectionQuality > 0.5)
                {
                    float3 vdir = GetWorldSpaceNormalizeViewDir(posWS);   // right for the orthographic game camera too
                    // The game camera looks down at about 45 degrees, so plain Fresnel is tiny; start from a visible base.
                    // The sky and clouds are seen through a heavily smoothed normal (only the broad swell tilts them), the
                    // stars through an almost flat one, so the reflection does not shimmer with every small ripple.
                    float3 up = float3(0, 1, 0);
                    float3 rdir = reflect(-vdir, normalize(lerp(up, normal, 0.35)));
                    float3 sdir = reflect(-vdir, normalize(lerp(up, normal, 0.10)));
                    float fresnel = pow(1.0 - saturate(dot(normal, vdir)), 2.0);
                    float night = _SkyParams.x;
                    half3 sky = GlossyEnvironmentReflection(rdir, 0.0, 1.0);
                    sky = sky * lerp(1.0, 0.03, night) + half3(0.015, 0.025, 0.05) * night;   // the sky is dark at night
                    // Drifting clouds, lit by the sun and greyer the thicker the weather.
                    float cloud = CloudDensityAlongRay(posWS, rdir);
                    half3 cloudCol = saturate(mainLight.color * 0.85 + unity_AmbientSky.rgb * 0.4) * lerp(1.0, 0.6, _CloudParams.x);
                    sky = lerp(sky, cloudCol, cloud * 0.85);
                    // Calm and choppy stretches: the reflection is stronger where the water is smooth.
                    float calm = 0.55 + 0.9 * valueNoise2D(posWS.xz * 0.045 + 17.0);
                    float reflW = saturate((0.3 + fresnel * 0.6) * calm) * (1.0 - ice);
                    waterCol.rgb = lerp(waterCol.rgb, sky, reflW);
                    // Night: a few stars and the moon's glitter, hidden behind clouds.
                    if (night > 0.02)
                    {
                        float cd = saturate(dot(reflect(-vdir, normalize(lerp(up, normal, 0.5))), mainLight.direction));
                        float moon = pow(cd, 900.0) * 2.0 + pow(cd, 60.0) * 0.12;
                        half3 nightRefl = WaterStars(posWS.xz, sdir.xz, _RealTime) * 1.6 + mainLight.color * (moon * 4.0);
                        nightAdd = nightRefl * night * (1.0 - cloud * 0.85) * (1.0 - ice);   // added after the cel lighting so it is not dimmed by it
                    }
                }
                // Rain greys and darkens the water a little, and each ring catches a faint light.
                waterCol.rgb = lerp(waterCol.rgb, waterCol.rgb * 0.8 + 0.03, rain * 0.5);
                waterCol.rgb += rings.w * rain * 0.06 * damp;

                // No shoreline foam: it read as a white fringe around the water and is intentionally gone.

                // Simple cel lighting
                // The steps below turn every small tilt into a hard band, which is what made the surface look covered in
                // ripples; the light is taken from a mostly flat normal so only the broad swell shows.
                float ndotl = max(0.0, dot(normalize(lerp(float3(0, 1, 0), normal, 0.3)), mainLight.direction));
                float celLight = step(0.12, ndotl) * 0.35 + step(0.45, ndotl) * 0.35 + 0.3;
                waterCol.rgb *= celLight;
                waterCol.rgb *= CloudShadowFactor(posWS);   // drifting cloud shadows cross the water too
                waterCol.rgb += nightAdd;

                // Ice: opaque pale blue-white with a crack network, flat and unlit by waves.
                if (ice > 0.001)
                {
                    float2 cp = posWS.xz * 0.55;
                    float2 ci = floor(cp), cf = frac(cp);
                    float f1 = 9.0, f2 = 9.0;
                    [unroll]
                    for (int cz = -1; cz <= 1; cz++)
                    {
                        [unroll]
                        for (int cx = -1; cx <= 1; cx++)
                        {
                            float2 o = float2(cx, cz);
                            float2 pt = o + 0.15 + 0.7 * hash22(ci + o);
                            float dd = length(cf - pt);
                            if (dd < f1) { f2 = f1; f1 = dd; } else if (dd < f2) { f2 = dd; }
                        }
                    }
                    float crack = 1.0 - smoothstep(0.0, 0.07, f2 - f1);
                    float mottling = valueNoise2D(posWS.xz * 0.9);
                    half3 iceCol = lerp(half3(0.60, 0.78, 0.88), half3(0.86, 0.94, 0.98), mottling);
                    iceCol *= 1.0 - crack * 0.28;
                    // Deeper water shows through the ice a little, so it is not a flat sticker on the bed.
                    iceCol = lerp(iceCol, waterCol.rgb, depth * 0.25);
                    iceCol *= 0.8 + 0.2 * saturate(dot(float3(0, 1, 0), mainLight.direction));
                    waterCol.rgb = lerp(waterCol.rgb, iceCol, ice);
                    waterCol.a = lerp(waterCol.a, 0.97, ice);
                }

                // Fade out across the shore blur band instead of the old hard cutoff - this is what actually
                // turns the boundary into a smooth edge rather than a crisp (and thus staircase-shaped) one.
                waterCol.a *= edgeAlpha;

                return waterCol;
            }
            ENDHLSL
        }
    }
    FallBack "Hidden/Universal Render Pipeline/FallbackError"
}
