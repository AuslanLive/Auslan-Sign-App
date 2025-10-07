import React from 'react';

const WordSelectionModal = ({ 
    isOpen, 
    top5Predictions, 
    onWordSelect, 
    onRedo, 
    onClose 
}) => {
    if (!isOpen) return null;

    return (
        <div style={styles.overlay}>
            <div style={styles.modal}>
                <div style={styles.header}>
                    <h2 style={styles.title}>Select the word you signed:</h2>
                    <button 
                        onClick={onClose}
                        style={styles.closeButton}
                    >
                        ×
                    </button>
                </div>
                
                <div style={styles.predictionsContainer}>
                    {top5Predictions.map((prediction, index) => (
                        <button
                            key={index}
                            onClick={() => onWordSelect(prediction[0])}
                            style={styles.predictionButton}
                            onMouseEnter={(e) => {
                                e.target.style.backgroundColor = 'rgba(59, 130, 246, 0.2)';
                                e.target.style.borderColor = 'rgba(59, 130, 246, 0.5)';
                            }}
                            onMouseLeave={(e) => {
                                e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                                e.target.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                            }}
                        >
                            <div style={styles.wordInfo}>
                                <span style={styles.wordText}>{prediction[0]}</span>
                                <span style={styles.confidence}>
                                    {(prediction[1] * 100).toFixed(1)}%
                                </span>
                            </div>
                        </button>
                    ))}
                </div>
                
                <div style={styles.footer}>
                    <button
                        onClick={onRedo}
                        style={styles.redoButton}
                        onMouseEnter={(e) => {
                            e.target.style.backgroundColor = 'rgba(255, 193, 7, 0.3)';
                        }}
                        onMouseLeave={(e) => {
                            e.target.style.backgroundColor = 'rgba(255, 193, 7, 0.2)';
                        }}
                    >
                        Redo - None of these words
                    </button>
                </div>
            </div>
        </div>
    );
};

const styles = {
    overlay: {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        backdropFilter: 'blur(5px)',
    },
    modal: {
        backgroundColor: 'rgba(26, 26, 46, 0.95)',
        borderRadius: '16px',
        padding: '24px',
        maxWidth: '500px',
        width: '90%',
        maxHeight: '80vh',
        overflow: 'auto',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.5)',
        backdropFilter: 'blur(10px)',
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px',
        paddingBottom: '16px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
    },
    title: {
        color: '#ffffff',
        fontSize: '20px',
        fontWeight: '600',
        margin: 0,
        background: 'linear-gradient(135deg, #00f2fe 0%, #3b82f6 50%, #a855f7 100%)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text',
    },
    closeButton: {
        background: 'none',
        border: 'none',
        color: '#ffffff',
        fontSize: '24px',
        cursor: 'pointer',
        padding: '4px 8px',
        borderRadius: '4px',
        transition: 'all 0.2s ease',
    },
    predictionsContainer: {
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        marginBottom: '20px',
    },
    predictionButton: {
        padding: '16px 20px',
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        borderRadius: '12px',
        color: '#ffffff',
        fontSize: '16px',
        cursor: 'pointer',
        transition: 'all 0.3s ease',
        textAlign: 'left',
        width: '100%',
        boxSizing: 'border-box',
    },
    wordInfo: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        width: '100%',
    },
    wordText: {
        fontSize: '16px',
        fontWeight: '500',
    },
    confidence: {
        fontSize: '14px',
        opacity: 0.7,
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        padding: '4px 8px',
        borderRadius: '6px',
    },
    footer: {
        paddingTop: '16px',
        borderTop: '1px solid rgba(255, 255, 255, 0.1)',
    },
    redoButton: {
        width: '100%',
        padding: '14px',
        backgroundColor: 'rgba(255, 193, 7, 0.2)',
        border: '1px solid rgba(255, 193, 7, 0.4)',
        borderRadius: '10px',
        color: '#ffc107',
        fontSize: '16px',
        fontWeight: '500',
        cursor: 'pointer',
        transition: 'all 0.3s ease',
    },
};

export default WordSelectionModal;