import React from "react";

/**
 * InlineSelector Component
 * 

 */
const InlineSelector = ({ predictions, onSelect, onSkip }) => {
    if (!predictions || predictions.length === 0) return null;
    
    const top5 = predictions.top5 || predictions;
    const confidence = predictions.confidence || 0;
    
    return (
        <div style={{
            display: 'inline-block',
            margin: '0 8px',
            padding: '12px 16px',
            backgroundColor: '#fef3c7',
            border: '2px solid #f59e0b',
            borderRadius: '12px',
            animation: 'fadeIn 0.3s ease'
        }}>
            <div style={{
                fontSize: '0.85em',
                fontWeight: '600',
                color: '#92400e',
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
            }}>
                <span>⚠️</span>
                <span>Did you sign:</span>
                <span style={{ fontSize: '0.9em', opacity: 0.7 }}>
                    ({(confidence * 100).toFixed(0)}% confidence)
                </span>
            </div>
            
            <div style={{
                display: 'flex',
                gap: '6px',
                flexWrap: 'wrap'
            }}>
                {top5.slice(0, 5).map((pred, index) => {
                    const word = pred.label || pred.word;
                    const conf = pred.confidence || 0;
                    
                    return (
                        <button
                            key={index}
                            onClick={() => onSelect(word)}
                            style={{
                                padding: '6px 12px',
                                backgroundColor: 'white',
                                border: '2px solid #d97706',
                                borderRadius: '6px',
                                cursor: 'pointer',
                                fontWeight: '600',
                                fontSize: '0.95em',
                                color: '#92400e',
                                transition: 'all 0.2s ease',
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                gap: '2px'
                            }}
                            onMouseEnter={(e) => {
                                e.target.style.backgroundColor = '#fed7aa';
                                e.target.style.transform = 'scale(1.05)';
                            }}
                            onMouseLeave={(e) => {
                                e.target.style.backgroundColor = 'white';
                                e.target.style.transform = 'scale(1)';
                            }}
                        >
                            <span>{word}</span>
                            <span style={{ fontSize: '0.75em', opacity: 0.7 }}>
                                {(conf * 100).toFixed(0)}%
                            </span>
                        </button>
                    );
                })}
                
                <button
                    onClick={onSkip}
                    style={{
                        padding: '6px 12px',
                        backgroundColor: '#ef4444',
                        border: '2px solid #dc2626',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontWeight: '600',
                        fontSize: '0.95em',
                        color: 'white',
                        transition: 'all 0.2s ease'
                    }}
                    onMouseEnter={(e) => {
                        e.target.style.backgroundColor = '#dc2626';
                        e.target.style.transform = 'scale(1.05)';
                    }}
                    onMouseLeave={(e) => {
                        e.target.style.backgroundColor = '#ef4444';
                        e.target.style.transform = 'scale(1)';
                    }}
                >
                    Skip ✕
                </button>
            </div>
        </div>
    );
};

export default InlineSelector;

