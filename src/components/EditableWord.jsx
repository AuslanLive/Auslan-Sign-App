import React, { useState, useRef, useEffect } from "react";
import ReactDOM from 'react-dom';

/**
 * EditableWord Component
 * 
 * Displays a word with confidence indicator and click-to-fix alternatives.
 
 */
const EditableWord = ({ wordData, onReplace }) => {
    const [showAlternatives, setShowAlternatives] = useState(false);
    const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0 });
    const wordRef = useRef(null);
    
    const {
        word,
        alternatives = [],
        confidence = 1.0,
        auto = false,
        id
    } = wordData;
    
    // Close dropdown when clicking outside and calculate position
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (!wordRef.current?.contains(event.target)) {
                setShowAlternatives(false);
            }
        };
        
        if (showAlternatives && wordRef.current) {
            // Calculate dropdown position based on word position
            const rect = wordRef.current.getBoundingClientRect();
            setDropdownPosition({
                top: window.scrollY + rect.bottom + 8,
                left: rect.left + (rect.width / 2)
            });
            
            document.addEventListener('mousedown', handleClickOutside);
        }
        
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [showAlternatives]);
    
    // Determine confidence level and styling
    const getConfidenceStyle = () => {
        if (confidence >= 0.80) {
            return {
                color: '#10b981', // green
                icon: '✓',
                bgColor: 'rgba(16, 185, 129, 0.2)',
                borderColor: '#10b981'
            };
        } else if (confidence >= 0.50) {
            return {
                color: '#f59e0b', // orange
                icon: '⚠',
                bgColor: 'rgba(245, 158, 11, 0.2)',
                borderColor: '#f59e0b'
            };
        } else {
            return {
                color: '#ef4444', // red
                icon: '!',
                bgColor: 'rgba(239, 68, 68, 0.2)',
                borderColor: '#ef4444'
            };
        }
    };
    
    const style = getConfidenceStyle();
    const hasAlternatives = alternatives && alternatives.length > 0;
    
    const handleWordClick = () => {
        if (hasAlternatives) {
            setShowAlternatives(!showAlternatives);
        }
    };
    
    const handleAlternativeClick = (alternative) => {
        onReplace(id, alternative.label || alternative.word);
        setShowAlternatives(false);
    };
    
    return (
        <span 
            ref={wordRef}
            style={{
                position: 'relative',
                display: 'inline-block',
                margin: '0 4px'
            }}
        >
            <span
                onClick={handleWordClick}
                style={{
                    cursor: hasAlternatives ? 'pointer' : 'default',
                    padding: '4px 8px',
                    borderRadius: '6px',
                    backgroundColor: auto ? style.bgColor : 'transparent',
                    border: auto ? `2px solid ${style.borderColor}` : 'none',
                    fontWeight: '600',
                    fontSize: '1.1em',
                    transition: 'all 0.2s ease',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    ':hover': {
                        backgroundColor: hasAlternatives ? style.bgColor : 'transparent'
                    }
                }}
                onMouseEnter={(e) => {
                    if (hasAlternatives) {
                        e.target.style.backgroundColor = style.bgColor;
                    }
                }}
                onMouseLeave={(e) => {
                    if (!auto && hasAlternatives) {
                        e.target.style.backgroundColor = 'transparent';
                    }
                }}
            >
                {word}
                {auto && hasAlternatives && (
                    <span 
                        style={{
                            fontSize: '0.8em',
                            color: style.color,
                            fontWeight: 'bold'
                        }}
                        title={`Confidence: ${(confidence * 100).toFixed(0)}%`}
                    >
                        {style.icon}
                    </span>
                )}
            </span>
            
            {/* Alternatives dropdown - render as portal to avoid overflow clipping */}
            {showAlternatives && hasAlternatives && ReactDOM.createPortal(
                <div 
                    style={{
                        position: 'fixed',
                        top: `${dropdownPosition.top}px`,
                        left: `${dropdownPosition.left}px`,
                        transform: 'translateX(-50%)',
                        backgroundColor: '#1e1b2e',
                        border: '2px solid rgba(168, 85, 247, 0.5)',
                        borderRadius: '12px',
                        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.5)',
                        zIndex: 10000,
                        minWidth: 'max-content',
                        maxWidth: '90vw',
                        padding: '8px 0'
                    }}
                >
                    <div 
                        style={{
                            padding: '8px 12px',
                            fontSize: '0.75em',
                            fontWeight: '600',
                            color: '#a855f7',
                            textTransform: 'uppercase',
                            borderBottom: '1px solid rgba(168, 85, 247, 0.3)'
                        }}
                    >
                        What it could be
                    </div>
                    
                    {alternatives.map((alt, index) => {
                        const altWord = alt.label || alt.word;
                        const altConf = alt.confidence || 0;
                        const isCurrentWord = altWord === word;
                        
                        return (
                            <div
                                key={index}
                                onClick={() => !isCurrentWord && handleAlternativeClick(alt)}
                                style={{
                                    padding: '10px 16px',
                                    cursor: isCurrentWord ? 'default' : 'pointer',
                                    backgroundColor: isCurrentWord ? 'rgba(168, 85, 247, 0.2)' : 'transparent',
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    transition: 'background-color 0.15s ease',
                                    borderLeft: isCurrentWord ? '3px solid #a855f7' : '3px solid transparent'
                                }}
                                onMouseEnter={(e) => {
                                    if (!isCurrentWord) {
                                        e.currentTarget.style.backgroundColor = 'rgba(168, 85, 247, 0.15)';
                                    }
                                }}
                                onMouseLeave={(e) => {
                                    if (!isCurrentWord) {
                                        e.currentTarget.style.backgroundColor = 'transparent';
                                    }
                                }}
                            >
                                <span 
                                    style={{
                                        fontWeight: isCurrentWord ? '600' : '500',
                                        color: isCurrentWord ? '#a855f7' : '#e5e7eb'
                                    }}
                                >
                                    {altWord}
                                    {isCurrentWord && (
                                        <span style={{ marginLeft: '6px', fontSize: '0.9em', color: '#9ca3af' }}>
                                            (current)
                                        </span>
                                    )}
                                </span>
                                <span 
                                    style={{
                                        fontSize: '0.85em',
                                        color: '#9ca3af',
                                        fontWeight: '500'
                                    }}
                                >
                                    {(altConf * 100).toFixed(0)}%
                                </span>
                            </div>
                        );
                    })}
                </div>,
                document.body
            )}
        </span>
    );
};

export default EditableWord;

