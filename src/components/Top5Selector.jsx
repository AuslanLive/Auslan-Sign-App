import React, { useState, useEffect } from "react";

/**
 * Top5Selector Component
 * 
 * Displays top-5 predictions

 */
const Top5Selector = ({ predictions, onSelect, onSkip }) => {
    const [selectedIndex, setSelectedIndex] = useState(null);
    const [isAnimating, setIsAnimating] = useState(false);

    useEffect(() => {
        // Reset animation when new predictions arrive
        setIsAnimating(true);
        setTimeout(() => setIsAnimating(false), 300);
    }, [predictions]);

    const handleSelect = (word, index) => {
        setSelectedIndex(index);
        
        // Trigger selection with slight delay for visual feedback
        setTimeout(() => {
            onSelect(word);
            setSelectedIndex(null);
        }, 200);
    };

    const handleSkip = () => {
        onSkip();
    };

    if (!predictions || predictions.length === 0) {
        return null;
    }

    return (
        <div style={{
            ...styles.container,
            animation: isAnimating ? 'slideIn 0.3s ease-out' : 'none'
        }}>
            <div style={styles.header}>
                <span style={styles.title}>Which word did you sign?</span>
                <span style={styles.subtitle}>Select the correct word:</span>
            </div>
            
            <div style={styles.predictionList}>
                {predictions.map((pred, index) => (
                    <button
                        key={index}
                        onClick={() => handleSelect(pred.label, index)}
                        style={{
                            ...styles.predictionButton,
                            ...(selectedIndex === index ? styles.selectedButton : {}),
                            transform: selectedIndex === index ? 'scale(0.95)' : 'scale(1)',
                        }}
                        className="prediction-button"
                    >
                        <div style={styles.predictionContent}>
                            <div style={styles.predictionText}>
                                <span style={styles.rank}>{index + 1}.</span>
                                <span style={styles.label}>{pred.label}</span>
                            </div>
                            <div style={styles.confidenceSection}>
                                <div style={styles.confidenceBarContainer}>
                                    <div 
                                        style={{
                                            ...styles.confidenceBar,
                                            width: `${pred.confidence * 100}%`,
                                            backgroundColor: getConfidenceColor(pred.confidence)
                                        }}
                                    />
                                </div>
                                <span style={styles.confidenceText}>
                                    {(pred.confidence * 100).toFixed(0)}%
                                </span>
                            </div>
                        </div>
                    </button>
                ))}
            </div>

            <button 
                onClick={handleSkip}
                style={styles.skipButton}
                className="skip-button"
            >
                ⊘ None of these / Skip
            </button>
        </div>
    );
};

// Helper function to get color based on confidence
const getConfidenceColor = (confidence) => {
    if (confidence >= 0.7) return '#10b981'; // Green
    if (confidence >= 0.5) return '#f59e0b'; // Amber
    return '#ef4444'; // Red
};

const styles = {
    container: {
        position: 'relative',
        width: '100%',
        maxWidth: '500px',
        backgroundColor: 'rgba(30, 20, 60, 0.95)',
        backdropFilter: 'blur(20px)',
        borderRadius: '20px',
        padding: '24px',
        boxShadow: '0 8px 32px rgba(168, 85, 247, 0.3), 0 0 0 1px rgba(168, 85, 247, 0.2)',
        border: '1px solid rgba(168, 85, 247, 0.3)',
        zIndex: 100,
    },
    header: {
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
        marginBottom: '20px',
        textAlign: 'center',
    },
    title: {
        fontSize: '20px',
        fontWeight: '700',
        color: '#ffffff',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    },
    subtitle: {
        fontSize: '14px',
        color: 'rgba(255, 255, 255, 0.6)',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    },
    predictionList: {
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        marginBottom: '16px',
    },
    predictionButton: {
        width: '100%',
        padding: '16px',
        backgroundColor: 'rgba(255, 255, 255, 0.08)',
        border: '2px solid rgba(168, 85, 247, 0.2)',
        borderRadius: '12px',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    },
    selectedButton: {
        backgroundColor: 'rgba(168, 85, 247, 0.3)',
        borderColor: 'rgba(168, 85, 247, 0.6)',
    },
    predictionContent: {
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        width: '100%',
    },
    predictionText: {
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
    },
    rank: {
        fontSize: '18px',
        fontWeight: '600',
        color: 'rgba(255, 255, 255, 0.5)',
        minWidth: '28px',
    },
    label: {
        fontSize: '22px',
        fontWeight: '700',
        color: '#ffffff',
        textAlign: 'left',
        flex: 1,
    },
    confidenceSection: {
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
    },
    confidenceBarContainer: {
        flex: 1,
        height: '8px',
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        borderRadius: '4px',
        overflow: 'hidden',
    },
    confidenceBar: {
        height: '100%',
        borderRadius: '4px',
        transition: 'width 0.3s ease',
    },
    confidenceText: {
        fontSize: '14px',
        fontWeight: '600',
        color: 'rgba(255, 255, 255, 0.8)',
        minWidth: '45px',
        textAlign: 'right',
    },
    skipButton: {
        width: '100%',
        padding: '14px',
        backgroundColor: 'rgba(239, 68, 68, 0.15)',
        border: '2px solid rgba(239, 68, 68, 0.3)',
        borderRadius: '12px',
        color: '#ef4444',
        fontSize: '16px',
        fontWeight: '600',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    },
};

// Add CSS animations
const styleSheet = document.createElement("style");
styleSheet.textContent = `
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-20px) scale(0.95);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }
    
    .prediction-button:hover {
        background-color: rgba(168, 85, 247, 0.2) !important;
        border-color: rgba(168, 85, 247, 0.4) !important;
        transform: scale(1.02) !important;
    }
    
    .prediction-button:active {
        transform: scale(0.98) !important;
    }
    
    .skip-button:hover {
        background-color: rgba(239, 68, 68, 0.25) !important;
        border-color: rgba(239, 68, 68, 0.5) !important;
    }
    
    .skip-button:active {
        transform: scale(0.98);
    }
`;
document.head.appendChild(styleSheet);

export default Top5Selector;


