import React from 'react';

const GrammarToggle = ({ parseGrammar, setParseGrammar }) => {
    return (
        <div style={{ position: 'absolute', top: '16px', right: '16px', zIndex: 10 }}>
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '12px',
                color: '#ffffff'
            }}>
                <span style={{ opacity: 0.8 }}>Grammar?</span>
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
        </div>
    );
};

export default GrammarToggle;
