import React, { useMemo } from "react";

export default function HighlightedText({ text, dict, onWordClick }) {
  const normDict = useMemo(() => {
    const m = new Map();
    for (const [k, v] of Object.entries(dict || {})) m.set(k.toLowerCase(), v);
    return m;
  }, [dict]);

  const tokens = useMemo(() => text.split(/(\b[\p{L}\p{N}_']+\b)/u), [text]);

  return (
    <span className="hl-wrap">
      {tokens.map((tok, i) => {
        const isWord = /\w/.test(tok);
        const key = tok.toLowerCase();
        const hit = isWord && normDict.has(key);
        return hit ? (
          <button
            key={i}
            type="button"
            className="hl-word"
            onClick={() => onWordClick?.(tok, normDict.get(key))}
          >
            {tok}
          </button>
        ) : (
          <span key={i}>{tok}</span>
        );
      })}
      <style>{`
        .hl-word {
          appearance: none;
          background: none;
          border: 0;
          padding: 0 1px;
          margin: 0;
          color: #3b82f6;
          text-decoration: underline dotted;
          cursor: pointer;
          border-radius: 4px;
          font-family: inherit;
          font-size: inherit;
        }
        .hl-word:hover {
          background-color: rgba(59, 130, 246, 0.1);
          color: #60a5fa;
        }
        .hl-word:focus {
          outline: 2px solid rgba(59,130,246,.35);
          outline-offset: 2px;
        }
      `}</style>
    </span>
  );
}
