import React, { useState, useEffect } from 'react';
import HighlightedText from './HighlightedText';

const GrammarOverlay = ({ grammarParsedText, onCopy, onToggleAlwaysShow, alwaysShowGrammar, copySuccess, onClose, grammarDict, fullWordList }) => {
    const [selectedWord, setSelectedWord] = useState(null);
    const [selectedValue, setSelectedValue] = useState(null);

    // Reset selected word when overlay closes or text changes
    useEffect(() => {
        setSelectedWord(null);
        setSelectedValue(null);
    }, [grammarParsedText]);

    // Lightweight check for highlighted words
    const hasHighlightedWords = React.useMemo(() => {
        if (!grammarParsedText || !grammarDict) return false;
        
        const words = grammarParsedText.split(/\s+/);
        return words.some(word => {
            const cleanWord = word.toLowerCase().replace(/[^\w]/g, '');
            return Object.keys(grammarDict).some(key => 
                key.toLowerCase().split('(')[0].trim() === cleanWord
            );
        });
    }, [grammarParsedText, grammarDict]);

    // Check for yellow highlighted words (words not in fullWordList and not in parentheses)
    const hasYellowWords = React.useMemo(() => {
        if (!grammarParsedText || !fullWordList) return false;
        
        const tokens = grammarParsedText.split(/(\b[\p{L}\p{N}_']+\b)/u);
        return tokens.some(tok => {
            const containsParens = tok.includes('(') || tok.includes(')');
            const isWord = /\w/.test(tok) && !containsParens;
            const key = tok.toLowerCase();
            const hit = isWord && grammarDict && Object.keys(grammarDict).some(dictKey => 
                dictKey.toLowerCase().split('(')[0].trim() === key
            );
            const isInFullWordList = isWord && fullWordList.includes(key);
            
            // Check if followed by closing paren
            const tokenIndex = tokens.indexOf(tok);
            const isFollowedByCloseParen = isWord && tokenIndex < tokens.length - 1 && tokens[tokenIndex + 1] === ')';
            
            return isWord && !hit && !isInFullWordList && !isFollowedByCloseParen;
        });
    }, [grammarParsedText, fullWordList, grammarDict]);

    return (
        <div style={{
            padding: '14px',
            fontFamily: "'Inter', 'SF Pro Display', 'Segoe UI Variable', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            overflowY: 'auto'
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
                    fontSize: window.innerWidth < 768 ? '16px' : '18px',
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
                fontSize: window.innerWidth < 768 ? '14px' : '16px',
                color: 'rgba(255, 255, 255, 0.8)',
                lineHeight: '1.4'
            }}>
                Commonly uses the structure of: Time → Topic → Comment. <br />
                <br />
                Sentences often begin with when, then what/who, followed by what happens next.<br />
                {grammarParsedText && grammarParsedText.trim() && (
                    <>
                        <br />
                        For your sentence, the likely grammatical structure is shown below:
                    </>
                )}
            </p>

            {/* Grammar examples section when no parsed text */}
            {(!grammarParsedText || !grammarParsedText.trim()) && (
                <>
                    <h4 style={{
                        margin: '0 0 12px 0',
                        fontSize: window.innerWidth < 768 ? '15px' : '17px',
                        fontWeight: '600',
                        color: 'rgba(255, 255, 255, 0.9)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                    }}>
                        <span style={{
                            fontSize: '18px'
                        }}>📝</span>
                        Example:
                    </h4>
                    <div style={{
                        padding: '16px',
                        backgroundColor: 'rgba(255, 255, 255, 0.06)',
                        borderRadius: '12px',
                        marginBottom: '14px',
                        border: '1px solid rgba(255, 255, 255, 0.15)',
                        fontSize: window.innerWidth < 768 ? '14px' : '15px',
                        lineHeight: '1.6'
                    }}>
                        {/* English sentence */}
                        <div style={{
                            padding: '12px 14px',
                            backgroundColor: 'rgba(59, 130, 246, 0.15)',
                            border: '1px solid rgba(59, 130, 246, 0.3)',
                            borderRadius: '8px',
                            marginBottom: '12px'
                        }}>
                            <div style={{
                                fontSize: window.innerWidth < 768 ? '14px' : '15px',
                                color: 'rgba(59, 130, 246, 0.9)',
                                fontWeight: '600',
                                marginBottom: '4px',
                                letterSpacing: '0.5px'
                            }}>
                                English
                            </div>
                            <div style={{
                                color: 'rgba(255, 255, 255, 0.9)',
                                fontSize: window.innerWidth < 768 ? '14px' : '16px',
                                fontWeight: '500'
                            }}>
                                "I'm going to the shop."
                            </div>
                        </div>

                        {/* Arrow */}
                        <div style={{
                            textAlign: 'center',
                            margin: '8px 0',
                            color: 'rgba(255, 255, 255, 0.6)'
                        }}>
                            <span style={{
                                fontSize: '20px',
                                display: 'inline-block',
                                transform: 'rotate(90deg)'
                            }}>
                                ➤
                            </span>
                        </div>

                        {/* Auslan sentence */}
                        <div style={{
                            padding: '12px 14px',
                            backgroundColor: 'rgba(168, 85, 247, 0.15)',
                            border: '1px solid rgba(168, 85, 247, 0.3)',
                            borderRadius: '8px',
                            marginBottom: '14px'
                        }}>
                            <div style={{
                                fontSize: window.innerWidth < 768 ? '14px' : '15px',
                                color: 'rgba(168, 85, 247, 0.9)',
                                fontWeight: '600',
                                marginBottom: '4px',
                                letterSpacing: '0.5px'
                            }}>
                                Auslan
                            </div>
                            <div style={{
                                color: 'rgba(255, 255, 255, 0.9)',
                                fontSize: window.innerWidth < 768 ? '14px' : '16px',
                                fontWeight: '600',
                                letterSpacing: '1px'
                            }}>
                                "SHOP ME GO."
                            </div>
                        </div>

                        {/* Explanation */}
                        <div style={{
                            padding: '12px 14px',
                            backgroundColor: 'rgba(255, 193, 7, 0.1)',
                            border: '1px solid rgba(255, 193, 7, 0.2)',
                            borderRadius: '8px',
                            borderLeft: '4px solid rgba(255, 193, 7, 0.6)'
                        }}>
                            <div style={{
                                fontSize: window.innerWidth < 768 ? '14px' : '15px',
                                color: 'rgba(255, 193, 7, 0.8)',
                                fontWeight: '600',
                                marginBottom: '6px',
                                letterSpacing: '0.5px'
                            }}>
                                Structure Breakdown
                            </div>
                            <div style={{
                                color: 'rgba(255, 255, 255, 0.8)',
                                fontSize: window.innerWidth < 768 ? '13px' : '15px',
                                lineHeight: '1.5'
                            }}>
                                The <strong style={{color: 'rgba(255, 255, 255, 0.95)'}}>topic</strong> (SHOP) comes first, followed by <strong style={{color: 'rgba(255, 255, 255, 0.95)'}}>who</strong> (ME), then the <strong style={{color: 'rgba(255, 255, 255, 0.95)'}}>action</strong> (GO). Usually the verb is the last item.
                            </div>
                        </div>
                    </div>
                </>
            )}

            {grammarParsedText && grammarParsedText.trim() && (
                <div style={{
                    padding: '10px',
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    borderRadius: '8px',
                    marginBottom: '14px',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    color: '#ffffff',
                    fontSize: window.innerWidth < 768 ? '14px' : '16px',
                    fontFamily: "'Inter', 'SF Pro Display', 'Segoe UI Variable', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
                    wordBreak: 'break-word'
                }}>
                    "
                    <HighlightedText
                        text={grammarParsedText.charAt(0).toUpperCase() + grammarParsedText.slice(1)}
                        dict={grammarDict}
                        fullWordList={fullWordList}
                        onWordClick={(word, value) => {
                            setSelectedWord(word);
                            setSelectedValue(value);
                        }}
                    />
                    ."
                </div>
            )}

            {hasHighlightedWords && (
                <div style={{
                    padding: '8px 12px',
                    backgroundColor: 'rgba(59, 130, 246, 0.25)',
                    border: '1px solid rgba(59, 130, 246, 0.5)',
                    borderRadius: '6px',
                    marginBottom: '14px',
                    fontSize: window.innerWidth < 768 ? '12px' : '14px',
                    color: 'rgba(255, 255, 255, 0.75)',
                    lineHeight: '1.4',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                }}>
                    <span style={{
                        fontSize: '20px',
                        color: 'rgba(59, 130, 246, 0.8)'
                    }}>
                        💡
                    </span>
                    If a word appears in blue, it has multiple signs in Auslan — click it to view a list of them.
                </div>
            )}

            {hasYellowWords && (
                <div style={{
                    padding: '8px 12px',
                    backgroundColor: 'rgba(255, 193, 7, 0.25)',
                    border: '1px solid rgba(255, 193, 7, 0.5)',
                    borderRadius: '6px',
                    marginBottom: '14px',
                    fontSize: window.innerWidth < 768 ? '12px' : '14px',
                    color: 'rgba(255, 255, 255, 0.75)',
                    lineHeight: '1.4',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                }}>
                    <span style={{
                        fontSize: '20px',
                        color: 'rgba(255, 193, 7, 0.8)'
                    }}>
                        ✋
                    </span>
                    Yellow words are fingerspelled when no direct Auslan sign exists.
                </div>
            )}
            
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '12px',
                marginTop: 'auto'
            }}>
                {grammarParsedText && grammarParsedText.trim() && (
                    <label style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: window.innerWidth < 768 ? '12px' : '14px',
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
                        Always On?
                    </label>
                )}
                {grammarParsedText && grammarParsedText.trim() && (
                    <button
                        onClick={onCopy}
                        style={{
                            padding: '6px 12px',
                            fontSize: window.innerWidth < 768 ? '11px' : '13px',
                            backgroundColor: 'rgba(147, 51, 234, 0.2)',
                            border: '1px solid rgba(147, 51, 234, 0.4)',
                            borderRadius: '6px',
                            color: '#ffffff',
                            cursor: 'pointer',
                            fontWeight: '500',
                            boxShadow: '0 0 8px rgba(147, 51, 234, 0.3)'
                        }}
                        onMouseEnter={(e) => {
                            e.target.style.backgroundColor = 'rgba(147, 51, 234, 0.3)';
                            e.target.style.boxShadow = '0 0 15px rgba(147, 51, 234, 0.5), 0 0 25px rgba(147, 51, 234, 0.3)';
                        }}
                        onMouseLeave={(e) => {
                            e.target.style.backgroundColor = 'rgba(147, 51, 234, 0.2)';
                            e.target.style.boxShadow = '0 0 8px rgba(147, 51, 234, 0.3)';
                        }}
                    >
                        {copySuccess ? 'Copied!' : 'Copy'}
                    </button>
                )}
            </div>
        </div>
    );
};

export default GrammarOverlay;
