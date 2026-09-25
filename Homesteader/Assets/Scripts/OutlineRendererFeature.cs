using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.RenderGraphModule;
using UnityEngine.Rendering.RenderGraphModule.Util;
using UnityEngine.Rendering.Universal;

namespace Homesteader
{
    /// <summary>
    /// Screen-space glow outline for whatever is on <see cref="outlineLayer"/>
    /// (see HoverOutline.cs, which puts the hovered object's renderers on that
    /// layer). Four passes per frame:
    ///   1. Mask: render the Outline layer into a small offscreen texture with
    ///      OutlineMaskUnlit (solid white), everything else stays black.
    ///   2-3. Blur (OutlineBlur, horizontal then vertical): sparse foliage has
    ///      real gaps between disconnected leaf-card triangles in the sharp
    ///      mask, which would otherwise outline each leaf. Blurring merges
    ///      those gaps into one solid blob per object.
    ///   4. Composite: a fullscreen pass (OutlineComposite) thresholds the
    ///      blurred coverage back to a clean silhouette and dilates it by a few
    ///      pixels, blending the glow color only in the ring just outside it -
    ///      one clean rim around the whole object, not per-triangle edges.
    /// </summary>
    public sealed class OutlineRendererFeature : ScriptableRendererFeature
    {
        public LayerMask outlineLayer = 1 << 8; // "Outline" layer
        public Shader maskShader;
        public Shader blurShader;
        public Shader compositeShader;
        [ColorUsage(true, true)] public Color outlineColor = new(0.35f, 0.9f, 1.0f, 0.9f);
        // These are pixels in the QUARTER-resolution mask texture, so 1 unit
        // here = ~4 screen pixels. Divide the full-res-equivalent target by 4
        // (e.g. a 3px full-res outline -> 0.75 here), not by ~2.
        [Range(0, 6)] public float outlineWidthPx = 0.75f;
        [Range(0, 12)] public float blurRadiusPx = 2f;
        [Range(0, 1)] public float coverageThreshold = 0.12f;
        [Range(0, 10)] public float pulseSpeed = 2.5f;
        [Range(0, 1)] public float pulseAmount = 0.25f;

        private OutlinePass pass;

        public override void Create()
        {
            pass = new OutlinePass(this)
            {
                renderPassEvent = RenderPassEvent.AfterRenderingTransparents,
            };
        }

        public override void AddRenderPasses(ScriptableRenderer renderer, ref RenderingData renderingData)
        {
            // The overwhelming majority of frames have nothing hovered - skip
            // enqueueing all 4 passes entirely rather than running fullscreen
            // mask/blur/composite shaders for nothing every single frame.
            if (!HoverOutline.AnyHovered) return;
            if (maskShader == null || blurShader == null || compositeShader == null) return;
            renderer.EnqueuePass(pass);
        }

        private sealed class OutlinePass : ScriptableRenderPass
        {
            private readonly OutlineRendererFeature owner;
            private readonly List<ShaderTagId> shaderTags;
            private Material maskMaterial;
            private Material blurMaterial;
            private Material compositeMaterial;

            public OutlinePass(OutlineRendererFeature owner)
            {
                this.owner = owner;
                shaderTags = new List<ShaderTagId>
                {
                    new ShaderTagId("SRPDefaultUnlit"),
                    new ShaderTagId("UniversalForward"),
                    new ShaderTagId("UniversalForwardOnly"),
                };
            }

            private class MaskPassData
            {
                public RendererListHandle rendererListHandle;
            }

            public override void RecordRenderGraph(RenderGraph renderGraph, ContextContainer frameData)
            {
                if (owner.maskShader == null || owner.blurShader == null || owner.compositeShader == null) return;
                if (maskMaterial == null) maskMaterial = CoreUtils.CreateEngineMaterial(owner.maskShader);
                if (blurMaterial == null) blurMaterial = CoreUtils.CreateEngineMaterial(owner.blurShader);
                if (compositeMaterial == null) compositeMaterial = CoreUtils.CreateEngineMaterial(owner.compositeShader);

                blurMaterial.SetFloat("_BlurRadiusPx", owner.blurRadiusPx);

                compositeMaterial.SetColor("_OutlineColor", owner.outlineColor);
                compositeMaterial.SetFloat("_OutlineWidthPx", owner.outlineWidthPx);
                compositeMaterial.SetFloat("_CoverageThreshold", owner.coverageThreshold);
                compositeMaterial.SetFloat("_PulseSpeed", owner.pulseSpeed);
                compositeMaterial.SetFloat("_PulseAmount", owner.pulseAmount);

                UniversalResourceData resourceData = frameData.Get<UniversalResourceData>();
                UniversalRenderingData renderingData = frameData.Get<UniversalRenderingData>();
                UniversalCameraData cameraData = frameData.Get<UniversalCameraData>();
                UniversalLightData lightData = frameData.Get<UniversalLightData>();

                // Quarter resolution: this is a blurred glow effect, not a crisp
                // mask, so full camera resolution buys nothing but cost - 3
                // fullscreen passes at 1/16th the pixel count each.
                var camDesc = cameraData.cameraTargetDescriptor;
                int maskWidth = Mathf.Max(camDesc.width / 4, 1);
                int maskHeight = Mathf.Max(camDesc.height / 4, 1);
                var maskDesc = new TextureDesc(maskWidth, maskHeight)
                {
                    colorFormat = UnityEngine.Experimental.Rendering.GraphicsFormat.R8G8B8A8_UNorm,
                    clearBuffer = true,
                    clearColor = Color.clear,
                    filterMode = FilterMode.Bilinear,
                    wrapMode = TextureWrapMode.Clamp,
                    name = "_OutlineMask",
                };
                TextureHandle maskTex = renderGraph.CreateTexture(maskDesc);

                using (var builder = renderGraph.AddRasterRenderPass<MaskPassData>("Outline Mask", out var passData))
                {
                    var filter = new FilteringSettings(RenderQueueRange.all, owner.outlineLayer);
                    var drawSettings = RenderingUtils.CreateDrawingSettings(shaderTags, renderingData, cameraData, lightData, SortingCriteria.CommonOpaque);
                    drawSettings.overrideMaterial = maskMaterial;
                    drawSettings.overrideMaterialPassIndex = 0;

                    var param = new RendererListParams(renderingData.cullResults, drawSettings, filter);
                    passData.rendererListHandle = renderGraph.CreateRendererList(param);

                    if (passData.rendererListHandle.IsValid())
                        builder.UseRendererList(passData.rendererListHandle);
                    builder.SetRenderAttachment(maskTex, 0);
                    builder.SetRenderFunc(static (MaskPassData data, RasterGraphContext ctx) =>
                    {
                        if (data.rendererListHandle.IsValid())
                            ctx.cmd.DrawRendererList(data.rendererListHandle);
                    });
                }

                var blurDesc = maskDesc;
                blurDesc.name = "_OutlineMaskBlurH";
                blurDesc.clearBuffer = false;
                TextureHandle blurH = renderGraph.CreateTexture(blurDesc);
                blurDesc.name = "_OutlineMaskBlurV";
                TextureHandle blurV = renderGraph.CreateTexture(blurDesc);

                renderGraph.AddBlitPass(new RenderGraphUtils.BlitMaterialParameters(maskTex, blurH, blurMaterial, 0), "Outline Blur H");
                renderGraph.AddBlitPass(new RenderGraphUtils.BlitMaterialParameters(blurH, blurV, blurMaterial, 1), "Outline Blur V");

                var blitParams = new RenderGraphUtils.BlitMaterialParameters(blurV, resourceData.activeColorTexture, compositeMaterial, 0);
                renderGraph.AddBlitPass(blitParams, "Outline Composite");
            }
        }
    }
}
