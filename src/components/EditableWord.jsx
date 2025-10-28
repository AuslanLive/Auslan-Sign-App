import React from "react";

/**
 * EditableWord Component
 * 
 * Displays a word with confidence indicator.
 
 */
const EditableWord = ({ wordData }) => {
    const {
        word,
        confidence = 1.0,
        auto = false,
    } = wordData;
    
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
    
    return (
        <span 
            style={{
                position: 'relative',
                display: 'inline-block',
                margin: '0 4px'
            }}
        >
            <span
                style={{
                    cursor: 'default',
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
                }}
            >
                {word}
                {auto && (
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
        </span>
    );
};

export default EditableWord;

