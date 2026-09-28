import os, shutil, uuid

src_assets = r"C:\Users\casey\Desktop\Homesteader\assets"
dst_icons = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\Icons"
os.makedirs(dst_icons, exist_ok=True)

meta_template = """fileFormatVersion: 2
guid: {guid}
TextureImporter:
  internalIDToNameTable: []
  externalObjects: {}
  serializedVersion: 13
  mipmaps:
    mipMapMode: 0
    enableMipMap: 0
    sRGBTexture: 1
    linearTexture: 0
    fadeOut: 0
    borderMipMap: 0
    mipMapsPreserveCoverage: 0
    alphaTestReferenceValue: 0.5
    mipMapFadeDistanceStart: 1
    mipMapFadeDistanceEnd: 3
  bumpmap:
    convertToNormalMap: 0
    externalNormalMap: 0
    heightScale: 0.25
    normalMapFilter: 0
    flipGreenChannel: 0
  isReadable: 1
  streamingMipmaps: 0
  streamingMipmapsPriority: 0
  vTOnly: 0
  ignoreMipmapLimit: 0
  grayScaleToAlpha: 0
  generateCubemap: 6
  cubemapConvolution: 0
  seamlessCubemap: 0
  textureFormat: 1
  maxTextureSize: 2048
  textureSettings:
    serializedVersion: 2
    filterMode: 1
    aniso: 1
    mipBias: 0
    wrapU: 1
    wrapV: 1
    wrapW: 1
  nPOTScale: 0
  lightmap: 0
  compressionQuality: 50
  spriteMode: 1
  spriteExtrude: 1
  spriteMeshType: 1
  alignment: 0
  spritePivot: {x: 0.5, y: 0.5}
  spritePixelsToUnits: 100
  spriteBorder: {x: 0, y: 0, z: 0, w: 0}
  spriteGenerateFallbackPhysicsShape: 1
  alphaUsage: 1
  alphaIsTransparency: 1
  spriteTessellationDetail: -1
  textureType: 8
  textureShape: 1
  singleChannelComponent: 0
  flipbook: 0
  ignorePngGamma: 0
  cookieLightType: 0
  platformSettings: []
  assetBundleName: 
  assetBundleVariant: 
"""

copied = 0
for cat in os.listdir(src_assets):
    cat_dir = os.path.join(src_assets, cat)
    if not os.path.isdir(cat_dir): continue
    for item in os.listdir(cat_dir):
        item_dir = os.path.join(cat_dir, item)
        if not os.path.isdir(item_dir): continue
        png_path = os.path.join(item_dir, f"{item}.png")
        if os.path.isfile(png_path):
            dst_png = os.path.join(dst_icons, f"{item}.png")
            if not os.path.isfile(dst_png):
                shutil.copy2(png_path, dst_png)
                meta_path = dst_png + ".meta"
                if not os.path.isfile(meta_path):
                    with open(meta_path, "w") as f:
                        f.write(meta_template.replace("{guid}", uuid.uuid4().hex))
                copied += 1

print(f"Copied {copied} new PNG icons into {dst_icons}.")
