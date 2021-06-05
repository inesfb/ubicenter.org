from pathlib import Path
import json
from argparse_prompt import PromptParser
from typing import IO
import yaml

HEADER = """
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<script src="https://requirejs.org/docs/release/2.3.5/minified/require.js"></script>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
"""

CODE_BLOCK = """
<button onclick="show_code_{id}()">Click to show code</button>
<div id="code_block_{id}" style="display: none;">
  <pre>
    <code>
{code}
    </code>
  </pre>
</div>

<script>
function show_code_{id}() {
  var x = document.getElementById("code_block_{id}");
  if (x.style.display === "none") {
    x.style.display = "block";
  } else {
    x.style.display = "none";
  }
}
</script> \n"""

class NotebookCell:
    def __init__(self, data):
        self.data = data
        self.id = self.data["id"].replace("-", "_")
        self.cell_type = self.data["cell_type"]
    
    def render(self, out_file: IO):
        if self.cell_type == "markdown":
            # write markdown to file
            for line in self.data["source"]:
                out_file.write(line)
        elif self.cell_type == "code":
            # write code block with show-code button
            formatted_code_block = CODE_BLOCK.replace("{id}", self.id).replace("{code}", "".join(self.data["source"]))
            for line in formatted_code_block:
                out_file.write(line)
            # write outputs
            for output in self.data["outputs"]:
                # write text/html
                for line in output["data"]["text/html"]:
                    out_file.write(line.lstrip())


class NotebookPost:
    def __init__(self, path: Path, metadata: dict):
        self.metadata = metadata
        with open(path) as f:
            self.data = json.load(f)
        self.cells = map(NotebookCell, self.data["cells"])
    
    def render(self, out_file_path: Path):
        if isinstance(out_file_path, str):
            out_file_path = Path(out_file_path)
        if not out_file_path.parent.exists():
            out_file_path.parent.mkdir(parents=True, exist_ok=True) 
        with open(out_file_path, "w+") as f:
            f.write("---\n")
            yaml.safe_dump(self.metadata, f)
            f.write("---\n")
            f.write(HEADER)
            for cell in self.cells:
                cell.render(f)

if __name__ == "__main__":
    parser = PromptParser(description="A utility for converting Jupyter Notebooks into UBI Center posts.")
    parser.add_argument("notebook", help="The notebook file to convert.")
    parser.add_argument("--layout", default="post", help="The layout style")
    parser.add_argument("--current", default="post")
    parser.add_argument("--cover", default="assets/images/bear.jpg", help="The cover image path")
    parser.add_argument("--navigation", default=True)
    parser.add_argument("--title", default="Title goes here", help="The title")
    parser.add_argument("--date", default="2012-09-01 10:00:00", help="The publishing date")
    parser.add_argument("--tags", default="", help="The tags")
    parser.add_argument("--class_", default="post-template")
    parser.add_argument("--subclass", default="'post'")
    parser.add_argument("--author", default="max", help="The author name")
    parser.add_argument("--output-file", default="post.md")
    args = parser.parse_args()

    metadata = dict(
        layout=args.layout,
        current=args.current,
        cover=args.cover,
        navigation=args.navigation,
        title=args.title,
        date=args.date,
        tags=args.tags,
        subclass=args.subclass,
        author=args.author
    )
    metadata["class"] = args.class_

    notebook = NotebookPost(args.notebook, metadata)
    notebook.render(args.output_file)