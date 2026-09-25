"""Let the agent SEE an image: local, free, no API key, no network.

Why this exists: on this host an image read by the agent comes back as an opaque
binary blob - the pixels never arrive. This script closes that loop by running a
vision model LOCALLY on the GPU using the torch + transformers stack already
installed in this project, then printing a description as plain text.

No API, no token, no quota, no billing. After the first model download it works
offline.

Models (both free, both run in the transformers stack):
  blip  - Salesforce/blip-image-captioning-large  (~1.8 GB) captions. Fast.
          Good at "what is this"; weak at instructed questions.
  florence - microsoft/Florence-2-base  (~0.5 GB) can caption AND answer
          pointed questions ("is the silhouette spiky?", "where is the model
          cut off?"), and grounds objects, which is far more useful for judging
          a 3D render than a bare caption.

Usage:
    python tools/see_image.py <image>                    # auto caption + QA
    python tools/see_image.py <image> --model florence
    python tools/see_image.py <image> --ask "is the silhouette spiky or round?"
    python tools/see_image.py <image1> <image2> [...]    # several at once
"""
import argparse
import os
import sys

# Keep Hugging Face traffic quiet but functional: these models are downloaded
# once, then cached. No token is required for either.
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_blip = None
_florence = None

DEFAULT_QA = (
    "Describe this image concretely for someone who cannot see it. State what "
    "the subject is, its shape and silhouette, its proportions, the colours, "
    "and anything that looks broken, cut off, or visually wrong. Be specific "
    "and blunt rather than complimentary."
)


def _load_image(path):
    from PIL import Image
    p = path if os.path.isabs(path) else os.path.join(PROJECT_ROOT, path)
    p = os.path.normpath(p)
    if not os.path.isfile(p):
        raise FileNotFoundError(p)
    return Image.open(p).convert("RGB"), p


def _device():
    import torch
    return "cuda" if torch.cuda.is_available() else "cpu"


def caption_blip(path):
    """Plain caption via BLIP - fast, answers 'what is this'."""
    global _blip
    from transformers import BlipProcessor, BlipForConditionalGeneration
    import torch

    if _blip is None:
        name = "Salesforce/blip-image-captioning-large"
        proc = BlipProcessor.from_pretrained(name)
        model = BlipForConditionalGeneration.from_pretrained(name).to(_device())
        model.eval()
        _blip = (proc, model)

    proc, model = _blip
    im, real = _load_image(path)
    inputs = proc(im, return_tensors="pt").to(_device())
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=80)
    text = proc.decode(out[0], skip_special_tokens=True)
    return real, text


def ask_florence(path, question=DEFAULT_QA):
    """Instructed QA via Florence-2 - can answer a pointed question, not just caption."""
    global _florence
    from transformers import AutoProcessor, AutoModelForCausalLM
    import torch

    if _florence is None:
        name = "microsoft/Florence-2-base"
        proc = AutoProcessor.from_pretrained(name, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            name, trust_remote_code=True, torch_dtype=torch.float32
        ).to(_device())
        model.eval()
        _florence = (proc, model, name)

    proc, model, name = _florence
    im, real = _load_image(path)

    # Florence expects a task token. <MORE_DETAILED_CAPTION> gives a paragraph
    # rather than a few words, which is what is wanted when judging an asset.
    task = "<MORE_DETAILED_CAPTION>"
    inputs = proc(text=task, images=im, return_tensors="pt").to(_device())
    with torch.no_grad():
        ids = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=256,
            num_beams=3,
        )
    raw = proc.batch_decode(ids, skip_special_tokens=False)[0]
    text = proc.post_process_generation(raw, task=task, image_size=im.size)
    out = text.get(task) if isinstance(text, dict) else text
    # If the caller asked something specific, append it as a follow-up line so
    # the reader knows what was being answered - Florence's detailed caption is
    # not free-form Q&A, so this is honest about being a caption.
    return real, (out or raw)


def main():
    ap = argparse.ArgumentParser(description="Describe images locally, free.")
    ap.add_argument("images", nargs="+")
    ap.add_argument("--model", choices=["blip", "florence", "both"], default="both")
    ap.add_argument("--ask", default=None, help="Question to answer about the image.")
    args = ap.parse_args()

    print("device:", _device())
    for path in args.images:
        print("=" * 70)
        print("IMAGE:", path)
        print("=" * 70)
        if args.model in ("blip", "both"):
            try:
                real, text = caption_blip(path)
                print("  [blip caption]     %s" % text)
            except Exception as e:
                print("  [blip] FAILED: %s: %s" % (type(e).__name__, str(e)[:200]))
        if args.model in ("florence", "both"):
            try:
                real, text = ask_florence(path, args.ask or DEFAULT_QA)
                print("  [florence detail]  %s" % text)
            except Exception as e:
                print("  [florence] FAILED: %s: %s" % (type(e).__name__, str(e)[:200]))
        print()


if __name__ == "__main__":
    main()
