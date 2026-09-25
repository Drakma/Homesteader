// SPIKE (go/no-go): can Mesh2Motion's core rigging modules load and run
// headless in Node, without a browser DOM?
//
// Hypothesis under test: UI.getInstance() throws in Node because its
// constructor calls document.querySelector, but every consumer of UI fields
// already null-checks them, and `| null` is the declared type throughout.
// If so, a trivial global `document` stub is enough to run the real pipeline.
//
// This is a diagnostic, not production code. Run:
//   node tools/mesh2motion_headless/spike_probe.mjs

import { readFileSync } from 'node:fs'
import { pathToFileURL } from 'node:url'
import path from 'node:path'

const APP = path.resolve('tools/mesh2motion')
const SRC = path.join(APP, 'src')

const results = []
function record(name, status, detail) {
  results.push({ name, status, detail })
  const tag = status === 'PASS' ? 'PASS' : status === 'FAIL' ? 'FAIL' : 'INFO'
  console.log(`[${tag}] ${name}${detail ? ' :: ' + detail : ''}`)
}

// --- Step 1: does importing each module work with NO global stubs at all? ---
const modules = [
  'lib/enums/SkeletonType.ts',
  'lib/RigConfig.ts',
  'lib/UI.ts',
  'lib/processes/load-model/StepLoadModel.ts',
  'lib/processes/load-skeleton/StepLoadSkeleton.ts',
  'lib/processes/weight-skin/StepWeightSkin.ts',
  'lib/processes/export-to-file/StepExportToFile.ts',
  'lib/solvers/SkinningAlgorithm.ts',
]

console.log('=== Step 1: bare import (no DOM stubs) ===')
const imported = {}
for (const rel of modules) {
  try {
    imported[rel] = await import(pathToFileURL(path.join(SRC, rel)).href)
    record(`import ${rel}`, 'PASS')
  } catch (err) {
    record(`import ${rel}`, 'FAIL', err.constructor.name + ': ' + err.message.split('\n')[0])
  }
}

// --- Step 2: can UI.getInstance() be called at all? ---
console.log('\n=== Step 2: UI.getInstance() with no DOM ===')
try {
  const { UI } = imported['lib/UI.ts'] ?? {}
  if (!UI) {
    record('UI.getInstance (no stub)', 'INFO', 'UI module did not import; skipped')
  } else {
    UI.getInstance()
    record('UI.getInstance (no stub)', 'PASS', 'did not throw')
  }
} catch (err) {
  record('UI.getInstance (no stub)', 'FAIL', err.constructor.name + ': ' + err.message.split('\n')[0])
}

// --- Step 3: install a minimal document stub and retry ---
console.log('\n=== Step 3: UI.getInstance() with minimal document stub ===')
const queryLog = []
globalThis.document = {
  querySelector: (sel) => {
    queryLog.push(sel)
    return null
  },
  querySelectorAll: () => [],
  getElementById: () => null,
}
globalThis.window = globalThis
globalThis.self = globalThis

try {
  const { UI } = imported['lib/UI.ts'] ?? {}
  // Reset the singleton so the constructor re-runs against the stub.
  try { UI.instance = undefined } catch { /* private static, ignore */ }
  const inst = UI.getInstance()
  record('UI.getInstance (stubbed)', inst ? 'PASS' : 'FAIL',
    inst ? `constructed; ${queryLog.length} selectors queried, all returned null` : 'returned undefined')
  record('UI fields are null-safe', inst && inst.dom_upload_model_button === null ? 'PASS' : 'INFO',
    'dom_upload_model_button = ' + String(inst && inst.dom_upload_model_button))
} catch (err) {
  record('UI.getInstance (stubbed)', 'FAIL', err.constructor.name + ': ' + err.message.split('\n')[0])
}

// --- Step 4: does three.js itself work headless? ---
console.log('\n=== Step 4: three.js core + GLTFLoader in Node ===')
try {
  const THREE = await import('three')
  record('import three', typeof THREE.Scene === 'function' ? 'PASS' : 'FAIL', 'r' + (THREE.REVISION ?? '?'))
} catch (err) {
  record('import three', 'FAIL', err.message.split('\n')[0])
}

try {
  await import('three/examples/jsm/loaders/GLTFLoader.js')
  record('import GLTFLoader', 'PASS')
} catch (err) {
  record('import GLTFLoader', 'FAIL', err.message.split('\n')[0])
}

// --- Step 5: can we actually parse a real rig GLB? ---
console.log('\n=== Step 5: parse a real Mesh2Motion rig GLB ===')
try {
  const THREE = await import('three')
  const { GLTFLoader } = await import('three/examples/jsm/loaders/GLTFLoader.js')
  const rigPath = path.join(APP, 'static', 'rigs', 'rig-human.glb')
  const buf = readFileSync(rigPath)
  const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength)

  const loader = new GLTFLoader()
  const gltf = await new Promise((resolve, reject) => {
    loader.parse(ab, '', resolve, reject)
  })

  let bones = 0
  let armatureName = null
  gltf.scene.traverse((child) => {
    if (child.type === 'Bone') {
      bones++
      if (!armatureName && child.parent) armatureName = child.parent.name || child.parent.type
    }
  })
  record('parse rig-human.glb', bones > 0 ? 'PASS' : 'FAIL',
    `${bones} bones, armature parent = ${armatureName}`)
} catch (err) {
  record('parse rig-human.glb', 'FAIL', err.constructor.name + ': ' + err.message.split('\n')[0])
}

// --- Step 6: does the FBX exporter work headless? ---
console.log('\n=== Step 6: FBX exporter in Node ===')
try {
  const mod = await import('@comfyorg/fbx-exporter-three')
  const keys = Object.keys(mod)
  record('import FBXExporter', keys.length > 0 ? 'PASS' : 'FAIL', 'exports: ' + keys.join(', '))
} catch (err) {
  record('import FBXExporter', 'FAIL', err.message.split('\n')[0])
}

// --- Verdict ---
console.log('\n=== VERDICT ===')
const fails = results.filter((r) => r.status === 'FAIL')
console.log(`${results.filter((r) => r.status === 'PASS').length} pass, ${fails.length} fail`)
if (fails.length === 0) {
  console.log('GO: core pipeline appears runnable headless.')
} else {
  console.log('NO-GO blockers:')
  for (const f of fails) console.log('  - ' + f.name + ' :: ' + f.detail)
}
