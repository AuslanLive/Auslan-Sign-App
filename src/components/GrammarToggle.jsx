import React, { useState, useRef, useEffect } from 'react';
import GrammarOverlay from './GrammarOverlay';
import grammarDict from '../ambiguous_dict_lowercase.json';
import fullWordList from '../fullWordList.json';

const GrammarToggle = ({ parseGrammar, setParseGrammar, grammarParsedText, isMobile, alwaysShowGrammar, setAlwaysShowGrammar }) => {
    const [isGrammarOpen, setGrammarOpen] = useState(false);
    const [copySuccess, setCopySuccess] = useState(false);
    const grammarToggleRef = useRef(null);
    const grammarOverlayRef = useRef(null);

    // Handle grammar overlay state persistence
    const handleToggleAlwaysShow = () => {
        const newValue = !alwaysShowGrammar;
        setAlwaysShowGrammar(newValue);
        localStorage.setItem("auslan:alwaysShowGrammar", newValue.toString());
    };

    // Handle copy functionality
    const handleCopyGrammar = async () => {
        if (!grammarParsedText || !grammarParsedText.trim()) return;
        
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

    // Handle grammar text click
    const handleGrammarTextClick = (e) => {
        e.stopPropagation();
        setGrammarOpen(!isGrammarOpen);
    };

    // Handle ESC key and focus management
    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === 'Escape' && isGrammarOpen) {
                setGrammarOpen(false);
                if (grammarToggleRef.current) {
                    grammarToggleRef.current.focus();
                }
            }
        };

        const handleClickOutside = (e) => {
            if (isGrammarOpen && 
                grammarOverlayRef.current && 
                !grammarOverlayRef.current.contains(e.target) &&
                grammarToggleRef.current &&
                !grammarToggleRef.current.contains(e.target)) {
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
    }, [isGrammarOpen]);

    // Focus management for overlay
    useEffect(() => {
        if (isGrammarOpen && grammarOverlayRef.current) {
            const firstFocusable = grammarOverlayRef.current.querySelector('input, button');
            if (firstFocusable) {
                firstFocusable.focus();
            }
        }
    }, [isGrammarOpen]);

    return (
        <>
            {/* Add CSS styles */}
            <style>{`
                @media (prefers-reduced-motion: reduce) {
                    .grammar-overlay-enter,
                    .grammar-overlay-exit {
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
            `}</style>

            <div style={{ position: 'absolute', top: '16px', right: '16px', zIndex: 10 }}>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '12px',
                    color: '#ffffff'
                }}>
                    <span 
                        ref={grammarToggleRef}
                        onClick={handleGrammarTextClick}
                        style={{ 
                            opacity: 0.8,
                            cursor: 'pointer',
                            textDecoration: 'underline',
                            transition: 'opacity 150ms ease-out'
                        }}
                        onMouseEnter={(e) => {
                            e.target.style.opacity = '1';
                        }}
                        onMouseLeave={(e) => {
                            e.target.style.opacity = '0.8';
                        }}
                        title="Click to view grammar information"
                    >
                        Grammar On?
                    </span>
                    <div
                        onClick={() => setParseGrammar(!parseGrammar)}
                        style={{
                            position: 'relative',
                            width: '40px',
                            height: '20px',
                            backgroundColor: parseGrammar ? '#00a2ffff' : '#666',
                            borderRadius: '10px',
                            cursor: 'pointer',
                            transition: 'background-color 0.3s ease',
                            border: '1px solid rgba(255, 255, 255, 0.2)'
                        }}
                    >
                        <div
                            style={{
                                position: 'absolute',
                                top: '2px',
                                left: parseGrammar ? '20px' : '2px',
                                width: '14px',
                                height: '14px',
                                backgroundColor: '#ffffff',
                                borderRadius: '50%',
                                transition: 'left 0.3s ease',
                                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.3)'
                            }}
                        />
                    </div>
                </div>

                {/* Grammar overlay */}
                {isGrammarOpen && (
                    <>
                        {/* Backdrop */}
                        <div
                            style={{
                                position: 'fixed',
                                top: '0px',
                                left: '0px',
                                right: '0px',
                                bottom: '0px',
                                backgroundColor: 'rgba(0, 0, 0, 0.5)',
                                zIndex: 1000,
                                backdropFilter: isMobile ? 'none' : 'blur(4px)',
                                pointerEvents: 'all',
                                borderRadius: '24px',
                                overflow: 'hidden'
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
                                position: 'fixed',
                                zIndex: 1001,
                                backgroundColor: 'rgba(30, 20, 60, 0.95)',
                                backdropFilter: isMobile ? 'none' : 'blur(20px)',
                                border: '1px solid rgba(255, 255, 255, 0.2)',
                                borderRadius: '16px',
                                boxShadow: '0 20px 40px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.1) inset',
                                overflow: 'hidden',
                                pointerEvents: 'all',
                                left: '50%',
                                top: '50%',
                                transform: 'translate(-50%, -50%)',
                                width: isMobile ? 'min(60vw, 400px)' : 'min(22vw, 600px)',
                                height: isMobile ? 'min(30vh, 500px)' : 'min(50vh, 650px)',
                                maxWidth: '95vw',
                                maxHeight: '40vh',
                                minWidth: '280px',
                                minHeight: '250px'
                            }}
                        >
                            <GrammarOverlay
                                grammarParsedText={grammarParsedText}
                                onCopy={handleCopyGrammar}
                                onToggleAlwaysShow={handleToggleAlwaysShow}
                                alwaysShowGrammar={alwaysShowGrammar}
                                copySuccess={copySuccess}
                                onClose={() => setGrammarOpen(false)}
                                grammarDict={grammarDict}
                                fullWordList={fullWordList}
                            />
                        </div>
                    </>
                )}
            </div>
        </>
    );
};

export default GrammarToggle;
