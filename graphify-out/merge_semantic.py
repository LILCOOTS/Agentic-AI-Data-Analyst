import json
from pathlib import Path

chunk = json.loads(Path('graphify-out/.graphify_chunk_01.json').read_text())

# No cache — just use the one chunk
all_nodes = chunk['nodes']
all_edges = chunk['edges']
all_hyperedges = chunk.get('hyperedges', [])

merged = {
    'nodes': all_nodes,
    'edges': all_edges,
    'hyperedges': all_hyperedges,
    'input_tokens': 0,
    'output_tokens': 0,
}
Path('graphify-out/.graphify_semantic.json').write_text(json.dumps(merged, indent=2))
print(f'Semantic: {len(all_nodes)} nodes, {len(all_edges)} edges')
