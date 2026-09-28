# Tripo3D Sweep Workflow

Quick-start:

1. **Install Node 22 LTS** (Windows installer):
   <https://nodejs.org/dist/v22.11.0/node-v22.11.0-x64.msi>

2. **Install the CLI**:

   ```powershell
   npm install -g tripo-cli
   ```

3. **Sign in**:

   ```powershell
   tripo login
   ```

   (device-flow: copies a code to clipboard then opens browser.)

4. **Verify**:

   ```powershell
   tripo doctor
   ```

5. **Smoke test (1 mesh, ~$0.10)**:

   ```powershell
   python _procgen_test\_smoke_via_cli.py "small wooden log cabin"
   ```

6. **Generate the manifest**:

   ```powershell
   python _procgen_test\_emit_tripo_manifest.py --mode both
   ```

7. **Run the catalog sweep**:

   ```powershell
   tripo batch run assets\_tripo_manifest.yaml
   ```

   ~274 items × $0.10 = ~$27 total. Run time depends on Tripo3D's
   queue and accounts for our 2x concurrency.

8. **If something goes wrong** (CLI spec mismatch, auth issue), the
   REST-API fallback scripts are still there:

   - `_sweep_text_to_3d.py` — walks the catalog, posts text prompts.
   - `_sweep_image_to_3d.py` — uploads each item's existing icon.
   - `_smoke_tripo_text.py` — single-item API validation.

   These use `TRIPO_API_KEY` env var instead of the CLI's device
   login.

## When sweeps are complete

`_summarize_sweep.py` reports per-category success rates. Then we move
to a Blender iso re-render step: take each `.glb`, render it under
the strict 30° iso camera, output a 128×128 RGBA icon ready for the
catalog.

That Blender step is local (no API calls). Code lives in
`_render_models_to_iso.py` once we wire it up.
