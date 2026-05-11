"""Export graph diagram to Mermaid."""

from __future__ import annotations

from pathlib import Path
from .graph import build_graph

def export_diagram(output_path: str = "outputs/graph.md"):
    """Export the graph as a Mermaid diagram."""
    # Build graph without checkpointer for diagram generation
    graph = build_graph()
    
    # Get mermaid string
    try:
        mermaid_text = graph.get_graph().draw_mermaid()
    except Exception as e:
        mermaid_text = f"Error generating diagram: {e}"
        
    # Create directory if it doesn't exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# LangGraph Workflow Diagram\n\n")
        f.write("```mermaid\n")
        f.write(mermaid_text)
        f.write("\n```\n")
        
    print(f"Exported diagram to {output_path}")

if __name__ == "__main__":
    export_diagram()
