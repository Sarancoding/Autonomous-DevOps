import { FileCode } from "lucide-react";

interface DiffViewerProps {
  diff: string;
  filename?: string;
}

export function DiffViewer({ diff, filename }: DiffViewerProps) {
  if (!diff) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-surface-500 gap-3">
        <FileCode className="w-10 h-10" />
        <p className="text-sm">No diff generated yet</p>
      </div>
    );
  }

  const lines = diff.split("\n");

  return (
    <div className="glass-card overflow-hidden">
      {filename && (
        <div className="px-4 py-2 border-b border-surface-700 bg-surface-900/80">
          <span className="text-xs font-mono text-surface-400">{filename}</span>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full font-mono text-xs leading-relaxed">
          <tbody>
            {lines.map((line, i) => {
              let bgColor = "";
              let prefix = " ";
              let textColor = "text-surface-300";

              if (line.startsWith("+")) {
                bgColor = "bg-success/10";
                prefix = "+";
                textColor = "text-success";
              } else if (line.startsWith("-")) {
                bgColor = "bg-danger/10";
                prefix = "-";
                textColor = "text-danger";
              } else if (line.startsWith("@@")) {
                bgColor = "bg-primary-400/10";
                textColor = "text-primary-400";
                prefix = "@";
              } else if (line.startsWith("diff --git") || line.startsWith("---") || line.startsWith("+++")) {
                bgColor = "bg-surface-800/50";
                textColor = "text-surface-500";
                prefix = " ";
              }

              return (
                <tr key={i} className={bgColor}>
                  <td className="text-surface-600 text-right pr-4 select-none w-12 text-[10px]">
                    {i + 1}
                  </td>
                  <td className="text-surface-600 select-none w-4 text-center">{prefix}</td>
                  <td className={`${textColor} whitespace-pre`}>{line}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
