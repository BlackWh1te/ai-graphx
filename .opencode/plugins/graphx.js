// graphx OpenCode plugin
// Injects a knowledge graph reminder before bash tool calls when the graph exists.
import { existsSync } from "fs";
import { join } from "path";

export const GraphXPlugin = async ({ directory }) => {
  let reminded = false;

  return {
    "tool.execute.before": async (input, output) => {
      if (reminded) return;
      if (!existsSync(join(directory, "graphx-out", "graph.json"))) return;

      if (input.tool === "bash") {
        output.args.command =
          'echo "[graphx] Knowledge graph available. Read graphx-out/GRAPH_REPORT.md for god nodes and architecture context before searching files." && ' +
          output.args.command;
        reminded = true;
      }
    },
  };
};
