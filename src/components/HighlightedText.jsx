import React, { useMemo } from "react";

export default function HighlightedText({ text, dict, onWordClick }) {
  const normDict = useMemo(() => {
    const m = new Map();
    // console.log("🔍 Processing dictionary entries:");
    for (const [k, v] of Object.entries(dict || {})) {
      // Extract only the part before parentheses for matching
      const keyBeforeParens = k.toLowerCase().split("(")[0].trim();
      // console.log(`  "${k}" → "${keyBeforeParens}"`);
      // Store the original key and value, but use cleaned key for lookup
      m.set(keyBeforeParens, { originalKey: k, value: v });
    }
    return m;
  }, [dict]);

  const tokens = useMemo(() => {
    // console.log("🔤 Original text:", `"${text}"`);
    
    // Split the original text (keeping parentheses) into tokens
    const splitTokens = text.split(/(\b[\p{L}\p{N}_']+\b)/u);
    // console.log("✂️ Split tokens:", splitTokens.map((token, i) => `[${i}]: "${token}"`));
    return splitTokens;
  }, [text]);

  return (
    <span className="hl-wrap">
      {tokens.map((tok, i) => {
        const isWord = /\w/.test(tok);
        const key = tok.toLowerCase();
        const hit = isWord && normDict.has(key);
        
        // Log each token processing
        if (isWord) {
          // console.log(`🔍 Token "${tok}" (key: "${key}") → isWord: ${isWord}, hit: ${hit}`);
        }
        
        return hit ? (
          <button
            key={i}
            type="button"
            className="hl-word"
            onClick={() => {
              const entry = normDict.get(key);
              // console.log(`🎯 Clicked word "${tok}" → entry:`, entry);
              onWordClick?.(tok, entry.value);
            }}
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
