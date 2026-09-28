$ErrorActionPreference = 'Continue'
Set-Location C:\Users\casey\Desktop\Homesteader

# Only the scratch files this session created.
$mine = @(
 '_mods_size_probe.ps1','_pre_rewrite_backup.ps1','_filter_repo_probe.ps1','_filter_repo_scratch_test.ps1',
 '_stage_mods.ps1','_purge_mods_history.ps1','_purge_mods_pass2.ps1','_purge_mods_pass3.ps1',
 '_restore_mods_and_remotes.ps1','_verify_purge.ps1','_verify_leak.ps1','_final_leak_check.ps1',
 '_leak_weight.ps1','_leak_weight2.ps1','_pack_breakdown.ps1','_push_preflight.ps1',
 '_stage_schema_edits.ps1','_commit_schema_edits.ps1','_lfs_bigfile.ps1','_lfs_missing_probe.ps1',
 '_lfs_find_missing.ps1','_post_push_state.ps1','_push_slice_plan.ps1','_push_connectivity_test.ps1',
 '_push_delta_analysis.ps1','_push_detached.ps1','_do_push.ps1','_fbx_inventory.ps1',
 '_mesh_inventory.ps1','_build_mesh_exclude.ps1','_stage_meshes.ps1','_commit_gitignore.ps1',
 '_purge_meshes.ps1','_restore_meshes.ps1','_post_purge_size.ps1','_diagnose_survivors.ps1',
 '_purge_meshes_glob.ps1','_verify_glob_purge.ps1','_hud_mods_weight.ps1','_restore_all_meshes.ps1',
 '_push2.ps1','_lfs_push_all.ps1','_lfs_gap_diagnose.ps1','_find_all_missing_lfs.ps1',
 '_lfs_hash_compare.ps1','_lfs_oldroot_probe.ps1','_locate_missing_refs.ps1','_hunt_missing_refs.ps1',
 '_check_leak_commits.ps1','_purge_hudtree_old.ps1','_verify_oid_clean.ps1','_push3.ps1',
 '_verify_push_landed.ps1',
 '_all_current_mesh_paths.txt','_lfs_missing_oids.txt','_mesh_exclude_paths.txt',
 '_lfs_push.log','_push2.log','_push3.log','_push_detached.log','_push_origin.log','_push_result.log',
 '_lfs_push.done','_push2.done','_push3.done','_push_detached.done'
)

$removed = 0
foreach ($f in $mine) {
    $p = Join-Path "tools" $f
    if (Test-Path $p) { Remove-Item -LiteralPath $p -Force; $removed++ }
}
Write-Output ("removed {0} scratch files" -f $removed)

# The scratch test repo created to learn filter-repo's behavior.
$scratch = "tools\_scratch"
if (Test-Path $scratch) { Remove-Item -Recurse -Force $scratch; Write-Output "removed tools\_scratch" }

Write-Output ""
Write-Output "=== Security: are any tokens exposed in the repo's git config or remote URLs? ==="
$cfg = Get-Content ".git\config" -Raw
if ($cfg -match 'ghp_|github_pat_|x-access-token:[^@]+@') { Write-Output "WARNING: token found in .git/config" }
else { Write-Output "No tokens embedded in .git/config." }
