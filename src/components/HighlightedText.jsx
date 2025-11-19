import React, { useMemo, useState, useRef, useEffect } from "react";

export default function HighlightedText({ text, dict, fullWordList, onWordClick }) {
  const [selectedWord, setSelectedWord] = useState(null);
  const [selectedValue, setSelectedValue] = useState(null);
  const [isWordOverlayOpen, setIsWordOverlayOpen] = useState(false);
  const wordOverlayRef = useRef(null);

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

  // Handle word click
  const handleWordClick = (word, value) => {
    setSelectedWord(word);
    setSelectedValue(value);
    setIsWordOverlayOpen(true);
    onWordClick?.(word, value);
  };

  // Handle ESC key and click outside
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isWordOverlayOpen) {
        setIsWordOverlayOpen(false);
      }
    };

    const handleClickOutside = (e) => {
      if (isWordOverlayOpen && 
          wordOverlayRef.current && 
          !wordOverlayRef.current.contains(e.target)) {
        setIsWordOverlayOpen(false);
      }
    };

    if (isWordOverlayOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isWordOverlayOpen]);

  return (
    <>
      <span className="hl-wrap" style={{ position: 'relative' }}>
        {tokens.map((tok, i) => {
          const isWord = /\w/.test(tok);
          const key = tok.toLowerCase();
          const hit = isWord && normDict.has(key);
          const isInFullWordList = isWord && fullWordList && fullWordList.includes(key);
          
          // Check if word is wrapped in parentheses
          const isWrappedInParens = isWord && i > 0 && i < tokens.length - 1 && 
                                   tokens[i-1].includes('(') && tokens[i+1].includes(')');
          
          if (hit) {
            // Dictionary word - blue highlight with click functionality
            return (
              <button
                key={i}
                type="button"
                className="hl-word"
                onClick={() => {
                  const entry = normDict.get(key);
                  handleWordClick(tok, entry.value);
                }}
              >
                {tok}
              </button>
            );
          } else if (isWord && !isInFullWordList && !isWrappedInParens) {
            // Word not in fullWordList and not wrapped in parentheses - yellow highlight, no click
            return (
              <span key={i} className="hl-unknown-word">
                {tok}
              </span>
            );
          } else {
            // Regular text or punctuation
            return (
              <span key={i}>{tok}</span>
            );
          }
        })}
        
        {/* Word info overlay */}
        {isWordOverlayOpen && selectedWord && (
          <>
            {/* Backdrop - still fixed to cover entire screen */}
            <div
              style={{
                position: 'fixed',
                top: '0px',
                left: '0px',
                right: '0px',
                bottom: '0px',
                backgroundColor: 'rgba(0, 0, 0, 0.5)',
                zIndex: 1002,
                backdropFilter: window.innerWidth < 768 ? 'none' : 'blur(4px)',
                pointerEvents: 'all'
              }}
              onClick={() => setIsWordOverlayOpen(false)}
            />

            {/* Overlay content - positioned relative to nearest positioned ancestor */}
            <div
              ref={wordOverlayRef}
              role="dialog"
              aria-labelledby="word-info-title"
              style={{
                position: 'fixed',
                zIndex: 1003,
                backgroundColor: 'rgba(30, 20, 60, 0.95)',
                backdropFilter: window.innerWidth < 768 ? 'none' : 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                borderRadius: '16px',
                boxShadow: '0 20px 40px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.1) inset',
                overflow: 'hidden',
                pointerEvents: 'all',
                left: '50%',
                top: '50%',
                transform: 'translate(-50%, -50%)',
                width: window.innerWidth < 768 ? 'min(85vw, 350px)' : 'min(400px, 90vw)',
                maxWidth: '250px',
                minWidth: '150px',
                padding: '20px',
                fontFamily: "'Inter', 'SF Pro Display', 'Segoe UI Variable', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
                color: '#ffffff',
                // Add animations for smooth appearance
                opacity: isWordOverlayOpen ? 1 : 0,
                transition: 'opacity 200ms ease-out, transform 200ms ease-out'
              }}
            >
              {/* Header */}
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                marginBottom: '16px'
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  marginBottom: '8px'
                }}>
                  <h3 id="word-info-title" style={{
                    margin: 0,
                    fontSize: window.innerWidth < 768 ? '18px' : '20px',
                    fontWeight: '600',
                    color: '#60a5fa',
                    textTransform: 'capitalize'
                  }}>
                      {selectedWord}
                  </h3>
                  <button
                    onClick={() => setIsWordOverlayOpen(false)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'rgba(255, 255, 255, 0.6)',
                      fontSize: '20px',
                      cursor: 'pointer',
                      padding: '4px',
                      borderRadius: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: '28px',
                      height: '28px',
                      transition: 'all 150ms ease-out',
                      outline: 'none'
                    }}
                    onMouseEnter={(e) => {
                      e.target.style.color = '#ffffff';
                      e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                      e.target.style.boxShadow = '0 0 8px rgba(220, 220, 220, 0.5), 0 0 15px rgba(240, 240, 240, 0.3)';
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.color = 'rgba(255, 255, 255, 0.6)';
                      e.target.style.backgroundColor = 'transparent';
                      e.target.style.boxShadow = 'none';
                    }}
                    aria-label="Close"
                  >
                    ×
                  </button>
                </div>
                <h2 id="word-info-subtitle" style={{
                  margin: 0,
                  fontSize: window.innerWidth < 768 ? '14px' : '16px',
                  fontWeight: '400',
                  color: 'rgba(253, 253, 253, 0.8)',
                  textTransform: 'none'
                }}> 
                    other variants of this sign:
                </h2>
              </div>

              {/* Content */}
              <div style={{
                fontSize: window.innerWidth < 768 ? '14px' : '16px',
                lineHeight: '1.5'
              }}>
                {typeof selectedValue === 'object' && selectedValue !== null
                  ? Object.entries(selectedValue).map(([k, v]) => (
                      <div key={k} style={{ 
                        marginBottom: '12px',
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '8px'
                      }}>
                        <span style={{ 
                          color: 'rgba(255, 255, 255, 0.6)',
                          fontSize: '14px',
                          lineHeight: '1.5',
                          marginTop: '1px'
                        }}>
                          •
                        </span>
                        <span style={{ color: 'rgba(255, 255, 255, 1.0)' }}>
                        {/* print value of dict keys here */}
                          {String(v)}
                        </span>
                      </div>
                    ))
                  : <div style={{ 
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '8px'
                    }}>
                      <span style={{ 
                        color: 'rgba(255, 255, 255, 0.6)',
                        fontSize: '14px',
                        lineHeight: '1.5',
                        marginTop: '1px'
                      }}>
                        •
                      </span>
                      <span style={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                        {String(selectedValue)}
                      </span>
                    </div>
                }
              </div>
            </div>
          </>
        )}

        <style>{`
          .hl-wrap {
            display: inline;
            position: relative;
          }
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
          .hl-unknown-word {
            color: #ffdd1cff;
            padding: 0 1px;
            border-radius: 3px;
            font-family: inherit;
            font-size: inherit;
          }
        `}</style>
      </span>
    </>
  );
}
