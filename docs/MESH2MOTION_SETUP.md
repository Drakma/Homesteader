# Mesh2Motion — Local Free Rigging Pipeline

Free, local, offline character rigging with **animal support** (biped, quadruped,
bird, dragon, spider, snake, kaiju). This is the Homesteader replacement for
paid rigging services.

- Upstream: [Mesh2Motion/mesh2motion-app](https://github.com/Mesh2Motion/mesh2motion-app)
  (MIT code, CC0 art assets)
- Live reference: <https://app.mesh2motion.org/>
- Local checkout: `tools/mesh2motion/`
- MCP server: `tools/mesh2motion_mcp.py`
- Registered in `.mcp.json` as `mesh2motion`

---

## 0. Read this first — what is and is not automated

Mesh2Motion is a **Three.js browser application**, not a headless rigging
service. Upstream ships no rigging API, no CLI, and no headless mode. Its core
value is the interactive step where you drag skeleton handles until the rig sits
inside the mesh — that is the whole reason it beats Mixamo on fit quality.

So the pipeline is **semi-automated**, and the MCP server is honest about it:

| Step | Who does it | Tool |
| --- | --- | --- |
| Serve the app locally | Agent | `mesh2motion_start` |
| Stage the model + pick skeleton | Agent | `mesh2motion_open_model` |
| **Fit the skeleton to the mesh** | **Human (browser, ~30s)** | — |
| Tick animations + Export | Human | — |
| Verify the exported GLB | Agent | `mesh2motion_check_export` |
| Retarget to Unity Mecanim | Agent | `tools/retarget_to_mecanim` (see §5) |

An agent must never report a model as "rigged" until
`mesh2motion_check_export` confirms a GLB with both a skin **and** animation
clips.

---

## 1. Prerequisites

| Requirement | Status on this machine | Fix if missing |
| --- | --- | --- |
| Node.js + npm | Installed at `C:\Program Files\nodejs` (v22.13.0, npm 10.9.2) but **not on PATH** | MCP server probes the absolute path itself — no fix needed to use the tools. For manual use add `C:\Program Files\nodejs` to PATH. |
| git | `C:\Program Files\Git\cmd\git.exe` (2.47.0) — also not on PATH | Use the absolute path, as below. |
| Python `mcp` SDK | Installed (`C:\Python313\python.exe`) | `C:\Python313\python.exe -m pip install mcp` |
| Docker | **Not installed** | Optional. Only needed if you prefer container isolation. |

Because `node`, `npm`, and `git` are not on PATH, `tools/mesh2motion_mcp.py`
resolves Node/npm by absolute path internally. You never need to fix PATH to use
the MCP tools.

---

## 2. The checkout (already done)

```powershell
Set-Location "C:\Users\casey\Desktop\Homesteader\tools"
& "C:\Program Files\Git\cmd\git.exe" clone --depth 1 https://github.com/Mesh2Motion/mesh2motion-app.git mesh2motion
```

To update later:

```powershell
Set-Location "C:\Users\casey\Desktop\Homesteader\tools\mesh2motion"
& "C:\Program Files\Git\cmd\git.exe" pull
```

First run triggers `npm install` automatically (a few minutes, ~400 MB in
`node_modules`). To pre-install manually:

```powershell
Set-Location "C:\Users\casey\Desktop\Homesteader\tools\mesh2motion"
& "C:\Program Files\nodejs\npm.cmd" install
```

---

## 3. Running it

### Via MCP (normal path)

```
mesh2motion_status        -> is the server up? what's staged? what can I rig?
mesh2motion_start         -> npm install (once) + npm run dev, waits for port 3000
mesh2motion_open_model    -> stage model + skeleton guidance + open browser
mesh2motion_check_export  -> verify exported GLB, move it into the project
mesh2motion_list_skeletons-> available rig presets + Homesteader usage hints
```

Typical session:

1. `mesh2motion_open_model(model_path="assets/livestock/cow/cow.glb", skeleton="fox")`
2. Fit the skeleton in the browser, tick `Walk` + `Idle`, press **Export**.
3. `mesh2motion_check_export()` — confirms skin + clips, moves the GLB to
   `mesh_output/rigged/`.
4. Retarget to Mecanim (§5).

### Manually (without the agent)

```powershell
Set-Location "C:\Users\casey\Desktop\Homesteader\tools\mesh2motion"
& "C:\Program Files\nodejs\npm.cmd" run dev
```

Then open <http://localhost:3000>.

### Docker alternative

`docker-compose.yaml` maps host port **3000** to container **5173**:

```yaml
services:
  mesh2motion-app:
    build: .
    container_name: mesh2motion-app
    ports:
      - "3000:5173"
```

```powershell
Set-Location "C:\Users\casey\Desktop\Homesteader\tools\mesh2motion"
docker-compose up -d
```

Docker is not installed here, so the native dev-server path is what the MCP
server uses.

---

## 4. Where files go

| Location | Purpose |
| --- | --- |
| `tools/mesh2motion/static/staged/` | Models the agent copies in. Served by Vite at `http://localhost:3000/staged/<name>`. |
| `~/Downloads` | Where the browser writes exports. `mesh2motion_check_export` scans here. |
| `mesh_output/rigged/` | Project landing zone for verified rigged GLBs. |
| `logs/mesh2motion_server.log` | Dev-server stdout/stderr. |

Import formats: **GLB, GLTF, DAE, FBX**. Export: **GLB/GLTF**.

> Note: the upstream README says GLB/GLTF only, but the app's own UI and
> release notes list DAE and FBX import as well. The MCP server accepts all
> four; if an FBX import fails in your checked-out version, convert to GLB
> first with `tools/convert_models_to_glb.py`.

---

## 5. Retargeting the export to Unity Mecanim

**This is a required step, not optional.** Mesh2Motion exports a GLB with *its
own* skeleton. That is not a Unity Mecanim Humanoid avatar and not a Generic
rig — dropping it into the project produces a static prop that animates
incorrectly.

Add the model to the Homesteader project as follows:

1. **Import the GLB** into `Homesteader/Assets/Models/Characters/` (or the
   appropriate category folder).
2. **Humanoids** — select the model, set `Rig > Animation Type` to
   **Humanoid**, `Avatar Definition` to **Create From This Model**, then
   **Configure** and verify each required bone is auto-mapped. Mesh2Motion's
   human rig is Mixamo-like, so auto-mapping usually lands cleanly; fix any red
   bones by hand.
3. **Animals** — set `Animation Type` to **Generic** and `Avatar Definition`
   to **Create From This Model**. Quadrupeds, birds, dragons, spiders, and
   snakes all use Generic.
4. **Extract the animation clips** — in the Rig tab, expand the animation list
   and confirm `Walk`, `Idle`, etc. are present with sensible frame ranges.
5. **Wire up the Animator** per `docs/UNITY_INTEGRATION_GUIDE.md`.

Per-item manifests should point at the rigged model, and the item's icon should
still be re-rendered from the model per the standing rule
(`tools/render_icon_from_model.py`).

### Bone-count sanity check

`mesh2motion_check_export` reports `joint_count`. Use it as a fast health check:
a human rig should land in the ~50-70 joint range, and a quadruped lower. A
`joint_count` of 0 means the skeleton never bound and the fit must be redone.

---

## 6. Skeleton presets

| Preset | Homesteader use |
| --- | --- |
| `human` | Farmers, NPCs, humanoid enemies → Mecanim **Humanoid** |
| `fox` | Foxes, dogs, cats, wolves → **Generic**. Also a workable base for cows, pigs, sheep with leg-length tweaks |
| `horse` | Horses, donkeys, mules → **Generic** |
| `bird` | Chickens, ducks, geese → **Generic** |
| `dragon` | Winged quadruped → **Generic** |
| `spider` | Multi-leg arthropod → **Generic** |
| `snake` | Serpentine → **Generic** |
| `kaiju` | Large hybrid → **Generic** |

Rig availability evolves upstream — `mesh2motion_status` and the app's own
skeleton dropdown are authoritative for your checked-out version.

---

## 7. Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `node/npm not found` | Node not on PATH | The server probes `C:\Program Files\nodejs` automatically. If it still fails, install Node LTS. |
| Server exits immediately | npm install incomplete, or port 3000 taken | Read `logs/mesh2motion_server.log`. The server uses `--strictPort`, so it refuses to silently move ports. |
| `mesh2motion_check_export` finds nothing | Export never pressed, or it went somewhere other than `~/Downloads` | Check your browser's download location; pass `expected_name` to target a specific file. |
| Export has 0 animations | Exported before ticking clips | Re-export with animations selected. |
| Export has 0 joints | Skeleton never bound | Redo the skeleton fit; the handles must sit *inside* the mesh. |
| Rig looks wrong in Unity | GLB used as-is | Retarget per §5 — Mecanim needs the avatar configured. |
| `git` / `npm` not recognized | Not on PATH | Use absolute paths: `C:\Program Files\Git\cmd\git.exe`, `C:\Program Files\nodejs\npm.cmd`. |

---

## 8. License

Code is **MIT**; art assets (models, rigs, animations) are **CC0**. Both permit
commercial use and modification. This project is MIT-licensed generally, so
there is no license conflict.

---

## 9. Retargeting an A-pose rig ("Use Your Rigged Model") - arms clip into the body

**Symptom:** clips retargeted onto a rig that rests in an A-pose (arms angled down, e.g. Meshy output)
pull the arms into the torso. The Expand/Contract Arms slider does not fix it (range -120..+20;
negative pulls arms in, +20 barely changes anything).

**Cause:** `Rig.fromConfig` (`src/retarget/human-retargeting/Rig.ts`) hardcodes the arm swing/twist
axes as pure +/-X (a T-pose) for both source and target. An A-pose target is off by its arm angle
(~45 deg), so every arm direction the retargeter writes is rotated into the body.

**Fix (in this checkout):** `Rig.align_arms_to_rest` (default false). When true, arm chains derive their
swing from each bone's actual rest direction and rotate the twist axis by the same arc.
`AnimationRetargetService` sets it on the **target** rig only; the source M2M rig is a true T-pose.
If you `git pull` upstream, re-apply this patch.

**Verify an export numerically** (do not trust screenshots of a moving 3D view): evaluate the skeleton
per frame and measure hand/forearm distance to the hips-to-neck axis as a fraction of torso length.
Healthy is roughly 0.4 or more (Meshy's own walk/run: 0.43-0.60); inside the body is under ~0.15.
A wrong export also shows an asymmetric stored rest pose (left hand ~0.16 vs right ~0.65).

**Export settings:** Bone Naming Pattern = Mixamo (Meshy rigs use Mixamo-style names), Format = GLB.
The setting resets to Default when the page reloads.
