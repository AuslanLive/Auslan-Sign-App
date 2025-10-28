import React from "react";

/**
 * FrameProgressIndicator Component
 * 
 * Shows frame collection progress and instructions for word-by-word signing
 */
const FrameProgressIndicator = ({ frameStatus, isVisible }) => {
    if (!isVisible || !frameStatus) return null;

    const { 
        frames_collected = 0, 
        min_frames = 32,
        ready_to_predict = false 
    } = frameStatus;
    
    const progress = Math.min((frames_collected / Math.max(min_frames, 32)) * 100, 100);
    const isCollecting = frames_collected > 0;
    const hasEnoughFrames = frames_collected >= min_frames;

    // Determine instruction text based on progress
    let instructionText = "Ready to sign";
    let emoji = "👋";
    let secondaryText = "";
    
    if (hasEnoughFrames) {
        instructionText = "Drop hands to complete";
        emoji = "🤚";
        secondaryText = `${frames_collected} frames collected`;
    } else if (isCollecting) {
        instructionText = "Keep signing...";
        emoji = "📹";
        const remaining = min_frames - frames_collected;
        secondaryText = `Need ${remaining} more frames (${min_frames} minimum)`;
    }

    return (
        <div style={{
            ...styles.container,
            animation: hasEnoughFrames ? 'frameComplete 0.5s ease-out' : 'none'
        }}>
            {/* Emoji indicator */}
            <div style={styles.emojiContainer}>
                <span style={{
                    ...styles.emoji,
                    animation: isCollecting ? 'pulse 1.5s ease-in-out infinite' : 'none'
                }}>
                    {emoji}
                </span>
            </div>

            {/* Frame count */}
            <div style={styles.countText}>
                <span style={styles.countNumber}>{frames_collected}</span>
                <span style={styles.countLabel}> frames</span>
            </div>

            {/* Progress bar */}
            <div style={styles.progressBarContainer}>
                <div 
                    style={{
                        ...styles.progressBar,
                        width: `${progress}%`,
                        backgroundColor: hasEnoughFrames ? '#10b981' : '#a855f7',
                        transition: 'width 0.1s linear, background-color 0.3s ease'
                    }}
                />
            </div>

            {/* Instruction text */}
            <div style={styles.instructionText}>
                {instructionText}
            </div>

            {/* Secondary instruction text */}
            {secondaryText && (
                <div style={styles.secondaryText}>
                    {secondaryText}
                </div>
            )}
        </div>
    );
};

const styles = {
    container: {
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        backgroundColor: 'rgba(30, 27, 46, 0.95)',
        backdropFilter: 'blur(20px)',
        borderRadius: '20px',
        padding: '20px 30px',
        minWidth: '280px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(168, 85, 247, 0.5)',
        border: '2px solid rgba(168, 85, 247, 0.6)',
        zIndex: 10000,
    },
    emojiContainer: {
        textAlign: 'center',
        marginBottom: '12px',
    },
    emoji: {
        fontSize: '32px',
        display: 'inline-block',
    },
    countText: {
        textAlign: 'center',
        fontSize: '24px',
        fontWeight: '700',
        marginBottom: '12px',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    },
    countNumber: {
        color: '#a855f7',
        fontSize: '28px',
    },
    countSeparator: {
        color: 'rgba(255, 255, 255, 0.4)',
        margin: '0 4px',
    },
    countTotal: {
        color: 'rgba(255, 255, 255, 0.6)',
        fontSize: '24px',
    },
    countLabel: {
        color: 'rgba(255, 255, 255, 0.5)',
        fontSize: '16px',
        marginLeft: '4px',
    },
    progressBarContainer: {
        width: '100%',
        height: '8px',
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        borderRadius: '4px',
        overflow: 'hidden',
        marginBottom: '12px',
    },
    progressBar: {
        height: '100%',
        borderRadius: '4px',
        transition: 'width 0.1s linear',
        boxShadow: '0 0 10px rgba(168, 85, 247, 0.5)',
    },
    instructionText: {
        textAlign: 'center',
        fontSize: '16px',
        fontWeight: '600',
        color: '#ffffff',
        marginBottom: '4px',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    },
    secondaryText: {
        textAlign: 'center',
        fontSize: '13px',
        color: 'rgba(255, 255, 255, 0.6)',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    },
};

// Add CSS animations
const styleSheet = document.createElement("style");
styleSheet.textContent = `
    @keyframes frameComplete {
        0% {
            transform: translate(-50%, -50%) scale(1);
        }
        50% {
            transform: translate(-50%, -50%) scale(1.05);
            box-shadow: 0 8px 32px rgba(16, 185, 129, 0.6), 0 0 0 1px rgba(16, 185, 129, 0.5);
        }
        100% {
            transform: translate(-50%, -50%) scale(1);
        }
    }
`;
document.head.appendChild(styleSheet);

export default FrameProgressIndicator;

