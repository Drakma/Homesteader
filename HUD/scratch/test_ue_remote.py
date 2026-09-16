import sys
import time

sys.path.append(r'C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python')
from remote_execution import RemoteExecution

remote_exec = RemoteExecution()
remote_exec.start()

# Discover nodes
print("Discovering Unreal Editor remote nodes...")
for _ in range(10):
    if remote_exec.remote_nodes:
        break
    time.sleep(0.2)

print(f"Found nodes: {len(remote_exec.remote_nodes)}")
if remote_exec.remote_nodes:
    node = remote_exec.remote_nodes[0]
    print(f"Connecting to node: {node['node_id']} ({node.get('project_name')})...")
    remote_exec.open_command_connection(node)
    
    cmd = """
import unreal
print("CONNECTED TO UNREAL ENGINE!")
print("Project Dir:", unreal.SystemLibrary.get_project_directory())
"""
    res = remote_exec.run_command(cmd)
    print("Execution output:", res)

remote_exec.stop()
