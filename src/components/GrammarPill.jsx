import React, { useState, useRef, useEffect } from 'react';

// Grammar overlay content component
const GrammarOverlayContent = ({ grammarParsedText, onCopy, onToggleAlwaysShow, alwaysShowGrammar, copySuccess, onClose }) => (
    <div style={{
        padding: '14px',
        fontFamily: "'Inter', 'SF Pro Display', 'Segoe UI Variable', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
        height: '100%',
        display: 'flex',
        flexDirection: 'column'
    }}>
        {/* Header with close button */}
        <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '8px'
        }}>
            <h3 style={{
                margin: 0,
                fontSize: '16px',
                fontWeight: '600',
            }}>
                Auslan Grammar Structure
            </h3>
            <button
                onClick={onClose}
                style={{
                    background: 'none',
                    border: 'none',
                    color: 'rgba(255, 255, 255, 0.6)',
                    fontSize: '18px',
                    cursor: 'pointer',
                    padding: '4px',
                    borderRadius: '4px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '24px',
                    height: '24px',
                    transition: 'all 150ms ease-out',
                    outline: 'none'
                }}
                onMouseEnter={(e) => {
                    e.target.style.color = '#ffffff';
                    e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                    e.target.style.boxShadow = '0 0 8px rgba(255, 255, 255, 0.3)';
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
        
        <p style={{
            margin: '0 0 12px 0',
            fontSize: '13px',
            color: 'rgba(255, 255, 255, 0.8)',
            lineHeight: '1.4'
        }}>
            Auslan commonly uses the structure of: Time → Topic → Comment. <br />
            <br />
            Sentences often begin with when, then what/who, followed by what happens next.<br />
            <br />
            For your sentence, the likely grammatical structure is shown below:
        </p>
        <div style={{
            padding: '10px',
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '8px',
            marginBottom: '14px',
            border: '1px solid rgba(255, 255, 255, 0.15)'
        }}>
            <code style={{
                fontSize: '14px',
                color: '#ffffff',
                fontFamily: "'Inter', 'SF Pro Display', 'Segoe UI Variable', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
                wordBreak: 'break-word'
            }}>
                "{grammarParsedText.charAt(0).toUpperCase() + grammarParsedText.slice(1)}."
            </code>
        </div>
        <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
            marginTop: 'auto'
        }}>
            <label style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '13px',
                color: '#ffffff',
                cursor: 'pointer'
            }}>
                <input
                    type="checkbox"
                    checked={alwaysShowGrammar}
                    onChange={onToggleAlwaysShow}
                    style={{
                        margin: 0,
                        cursor: 'pointer'
                    }}
                />
                Always show
            </label>
            <button
                onClick={onCopy}
                style={{
                    padding: '6px 12px',
                    fontSize: '13px',
                    backgroundColor: 'rgba(168, 85, 247, 0.2)',
                    border: '1px solid rgba(168, 85, 247, 0.3)',
                    borderRadius: '6px',
                    color: '#ffffff',
                    cursor: 'pointer',
                    fontWeight: '500'
                }}
                onMouseEnter={(e) => {
                    e.target.style.backgroundColor = 'rgba(168, 85, 247, 0.3)';
                }}
                onMouseLeave={(e) => {
                    e.target.style.backgroundColor = 'rgba(168, 85, 247, 0.2)';
                }}
            >
                {copySuccess ? 'Copied!' : 'Copy'}
            </button>
        </div>
    </div>
);

const GrammarPill = ({ grammarParsedText, mode, isMobile, alwaysShowGrammar, setAlwaysShowGrammar }) => {
    const [isGrammarOpen, setGrammarOpen] = useState(false);
    const [copySuccess, setCopySuccess] = useState(false);
    const [showPill, setShowPill] = useState(false);
    const grammarPillRef = useRef(null);
    const grammarOverlayRef = useRef(null);

    // Handle grammar overlay state persistence
    const handleToggleAlwaysShow = () => {
        const newValue = !alwaysShowGrammar;
        setAlwaysShowGrammar(newValue);
        localStorage.setItem("auslan:alwaysShowGrammar", newValue.toString());
    };

    // Handle copy functionality
    const handleCopyGrammar = async () => {
        try {
            await navigator.clipboard.writeText(grammarParsedText);
            setCopySuccess(true);
            setTimeout(() => setCopySuccess(false), 2000);
        } catch (err) {
            // Fallback for older browsers
            try {
                const textArea = document.createElement('textarea');
                textArea.value = grammarParsedText;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                setCopySuccess(true);
                setTimeout(() => setCopySuccess(false), 2000);
            } catch (fallbackErr) {
                console.error('Copy failed:', fallbackErr);
            }
        }
    };

    // Handle grammar pill click
    const handleGrammarPillClick = () => {
        if (!grammarParsedText) return;
        setGrammarOpen(!isGrammarOpen);
    };

    // Handle ESC key and focus management
    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === 'Escape' && isGrammarOpen) {
                setGrammarOpen(false);
                if (grammarPillRef.current) {
                    grammarPillRef.current.focus();
                }
            }
        };

        const handleClickOutside = (e) => {
            if (isGrammarOpen && 
                grammarOverlayRef.current && 
                !grammarOverlayRef.current.contains(e.target) &&
                grammarPillRef.current &&
                !grammarPillRef.current.contains(e.target)) {
                setGrammarOpen(false);
            }
        };

        if (isGrammarOpen) {
            document.addEventListener('keydown', handleKeyDown);
            document.addEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('keydown', handleKeyDown);
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isGrammarOpen, isMobile]);

    // Focus management for overlay
    useEffect(() => {
        if (isGrammarOpen && grammarOverlayRef.current) {
            const firstFocusable = grammarOverlayRef.current.querySelector('input, button');
            if (firstFocusable) {
                firstFocusable.focus();
            }
        }
    }, [isGrammarOpen]);

    // Close grammar overlay when mode changes or text is cleared
    useEffect(() => {
        if (mode !== "textToVideo" || !grammarParsedText) {
            setGrammarOpen(false);
        }
    }, [mode, grammarParsedText]);

    // Handle pill entrance animation when grammarParsedText changes
    useEffect(() => {
        if (grammarParsedText && mode === "textToVideo") {
            // Reset state first
            setShowPill(false);
            // Trigger entrance animation after a brief delay for smoother transition
            const timer = setTimeout(() => {
                setShowPill(true);
            }, 200);
            return () => clearTimeout(timer);
        } else {
            setShowPill(false);
        }
    }, [grammarParsedText, mode]);

    // Don't render anything if not in textToVideo mode
    if (mode !== "textToVideo") {
        return null;
    }

    return (
        <>
            {/* Add CSS styles */}
            <style>{`
                @media (prefers-reduced-motion: reduce) {
                    .grammar-overlay-enter,
                    .grammar-overlay-exit,
                    .grammar-pill:hover,
                    .grammar-pill-enter {
                        transition: none !important;
                    }
                }
                
                .grammar-overlay-enter {
                    opacity: 0;
                    transform: ${isMobile ? 'translateY(8px)' : 'translateY(-4px)'};
                    transition: opacity 200ms ease-out, transform 200ms ease-out;
                }
                
                .grammar-overlay-enter.grammar-overlay-open {
                    opacity: 1;
                    transform: translateY(0);
                }
                
                .grammar-pill {
                    transition: all 150ms ease-out;
                }
                
                .grammar-pill-enter {
                    opacity: 0;
                    transform: scale(0.6) translateY(-12px) rotate(5deg);
                    box-shadow: 0 0 0 rgba(168, 85, 247, 0);
                    transition: all 500ms cubic-bezier(0.175, 0.885, 0.32, 1.275);
                }
                
                .grammar-pill-enter.grammar-pill-visible {
                    opacity: 1;
                    transform: scale(1) translateY(0) rotate(0deg);
                    box-shadow: 0 0 20px rgba(168, 85, 247, 0.4), 0 0 40px rgba(168, 85, 247, 0.2);
                    animation: grammar-pill-glow 2s ease-out forwards;
                }
                
                @keyframes grammar-pill-glow {
                    0% {
                        box-shadow: 0 0 20px rgba(59, 130, 246, 0.6), 0 0 40px rgba(59, 130, 246, 0.4);
                    }
                    25% {
                        box-shadow: 0 0 25px rgba(59, 130, 246, 0.8), 0 0 50px rgba(59, 130, 246, 0.5), 0 0 75px rgba(59, 130, 246, 0.2);
                    }
                    50% {
                        box-shadow: 0 0 25px rgba(99, 102, 241, 0.6), 0 0 50px rgba(99, 102, 241, 0.3), 0 0 75px rgba(99, 102, 241, 0.1);
                    }
                    75% {
                        box-shadow: 0 0 25px rgba(168, 85, 247, 0.6), 0 0 50px rgba(168, 85, 247, 0.3), 0 0 75px rgba(168, 85, 247, 0.1);
                    }
                    100% {
                        box-shadow: 0 0 8px rgba(168, 85, 247, 0.2), 0 0 16px rgba(168, 85, 247, 0.1);
                    }
                }
                
                .grammar-pill:hover {
                    background-color: rgba(168, 85, 247, 0.15) !important;
                    border-color: rgba(168, 85, 247, 0.4) !important;
                    transform: scale(1.05);
                    box-shadow: 0 0 15px rgba(168, 85, 247, 0.3), 0 0 30px rgba(168, 85, 247, 0.15);
                }
                
                .grammar-pill:focus {
                    outline: 2px solid rgba(168, 85, 247, 0.5);
                    outline-offset: 2px;
                }
            `}</style>

            <div style={{
                position: 'relative'
            }}>
                {/* Grammar pill */}
                {grammarParsedText && (
                    <button
                        ref={grammarPillRef}
                        onClick={handleGrammarPillClick}
                        className={`grammar-pill grammar-pill-enter ${showPill ? 'grammar-pill-visible' : ''}`}
                        style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            padding: '4px 8px',
                            fontSize: '16px',
                            fontWeight: '500',
                            backgroundColor: 'rgba(168, 85, 247, 0.1)',
                            border: '1px solid rgba(168, 85, 247, 0.2)',
                            borderRadius: '9999px',
                            color: '#ffffff',
                            cursor: 'pointer',
                            fontFamily: "'Inter', 'SF Pro Display', 'Segoe UI Variable', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
                        }}
                        aria-expanded={isGrammarOpen}
                        aria-haspopup="dialog"
                        aria-controls="grammar-overlay"
                    >
                        ?
                    </button>
                )}

                {/* Grammar overlay */}
                {isGrammarOpen && grammarParsedText && (
                    <>
                        {/* Backdrop */}
                        <div
                            style={{
                                position: 'fixed',
                                top: 0,
                                left: 0,
                                right: 0,
                                bottom: 0,
                                backgroundColor: 'rgba(0, 0, 0, 0.5)',
                                zIndex: 1000,
                                backdropFilter: 'blur(4px)'
                            }}
                            onClick={() => setGrammarOpen(false)}
                        />
                        
                        {/* Overlay content */}
                        <div
                            ref={grammarOverlayRef}
                            id="grammar-overlay"
                            role="dialog"
                            aria-labelledby="grammar-title"
                            className={`grammar-overlay-enter ${isGrammarOpen ? 'grammar-overlay-open' : ''}`}
                            style={{
                                position: isMobile ? 'fixed' : 'fixed',
                                zIndex: 1001,
                                backgroundColor: 'rgba(30, 20, 60, 0.95)',
                                backdropFilter: 'blur(20px)',
                                border: '1px solid rgba(255, 255, 255, 0.2)',
                                borderRadius: isMobile ? '16px 16px 0 0' : '12px',
                                boxShadow: '0 20px 40px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.1) inset',
                                ...(isMobile ? {
                                    left: 0,
                                    right: 0,
                                    bottom: 0,
                                    height: '50vh',
                                    maxHeight: '400px',
                                    minHeight: '200px'
                                } : {
                                    top: '50%',
                                    left: '50%',
                                    transform: 'translate(-50%, -50%)',
                                    width: '90vw',
                                    maxWidth: '500px',
                                    height: '60vh',
                                    maxHeight: '600px',
                                    minHeight: '400px'
                                })
                            }}
                        >
                            {isMobile && (
                                <div style={{
                                    display: 'flex',
                                    justifyContent: 'center',
                                    padding: '8px 0 4px 0'
                                }}>
                                    <div style={{
                                        width: '24px',
                                        height: '4px',
                                        backgroundColor: 'rgba(255, 255, 255, 0.3)',
                                        borderRadius: '2px'
                                    }} />
                                </div>
                            )}
                            
                            <GrammarOverlayContent
                                grammarParsedText={grammarParsedText}
                                onCopy={handleCopyGrammar}
                                onToggleAlwaysShow={handleToggleAlwaysShow}
                                alwaysShowGrammar={alwaysShowGrammar}
                                copySuccess={copySuccess}
                                onClose={() => setGrammarOpen(false)}
                            />
                        </div>
                    </>
                )}
            </div>
        </>
    );
};

export default GrammarPill;
