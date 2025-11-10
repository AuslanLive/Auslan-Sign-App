import React, { useState, useRef, useEffect } from "react";
import VideoInput from "../components/VideoInput";
import ToasterWithMax from "../components/ToasterWithMax";
import GrammarPill from "../components/GrammarPill";
import GrammarDisplay from "../components/GrammarDisplay";
import SwapControls from "../components/SwapControls";
import { storage } from "../firebase";
import { toast } from 'react-hot-toast';
import { styles } from '../styles/TranslateStyles';
import '../styles/TranslateStyles.css';
import 'react-toastify/dist/ReactToastify.css';

// Custom hooks
import { useVideoToTextPolling } from '../hooks/useVideoToTextPolling';
import { useTextToVideoTranslation } from '../hooks/useTextToVideoTranslation';
import { useSwapAnimation } from '../hooks/useSwapAnimation';

const TranslateApp = () => {
    const [mode, setMode] = useState("videoToText");
    const [sourceText, setSourceText] = useState("");
    const [translatedText, setTranslatedText] = useState("");
    const [animatedSignVideo, setAnimatedSignVideo] = useState(null);
    const videoInputRef = useRef(null);
    const [loading, setLoading] = useState(false);
    const [isPolling, setIsPolling] = useState(true);
    const [showClearButton, setShowClearButton] = useState(false);
    const [clearButtonAnimation, setClearButtonAnimation] = useState('');
    const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
    const [grammarParsedText, setGrammarParsedText] = useState("");
    const [alwaysShowGrammar, setAlwaysShowGrammar] = useState(() => 
        localStorage.getItem("auslan:alwaysShowGrammar") === "true"
    );

    // Custom hooks
    useVideoToTextPolling(mode, isPolling, setTranslatedText, setLoading);
    
    const { translateText } = useTextToVideoTranslation(
        storage,
        setLoading,
        setTranslatedText,
        setGrammarParsedText,
        setAnimatedSignVideo
    );

    const { animationState, handleSwap } = useSwapAnimation(
        mode,
        setMode,
        setTranslatedText,
        () => {}, // No longer needed since managed in animationState
        videoInputRef
    );

    // Handle camera start notification
    const handleCameraStart = () => {
        setIsPolling(true);
        if (videoInputRef.current) {
            videoInputRef.current.startTransmission();
        }
    };

    // Update size on window change
    useEffect(() => {
        const handleResize = () => {
            setIsMobile(window.innerWidth < 768);
        };

        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, []);

    // Monitor translatedText changes to animate clear button
    useEffect(() => {
        if (translatedText && !showClearButton) {
            setShowClearButton(true);
            setClearButtonAnimation('clear-button-enter');
        } else if (!translatedText && showClearButton) {
            setClearButtonAnimation('clear-button-exit');
            setTimeout(() => {
                setShowClearButton(false);
                setClearButtonAnimation('');
            }, 270);
        }
    }, [translatedText, showClearButton]);

    // Function to clear translated text
    const handleClearText = () => {
        setClearButtonAnimation('clear-button-exit');
        setTimeout(() => {
            setTranslatedText("");
            setIsPolling(false);
            if (videoInputRef.current) {
                videoInputRef.current.stopTransmission();
            }
        }, 133);
    };

    // Function to handle Enter key press
    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && mode === 'textToVideo' && !loading) {
            e.preventDefault();
            handleTextToVideo();
        }
    };

    // Function to handle translate button click with loading check
    const handleTextToVideo = () => {
        if (loading) {
            toast.error("Please wait until current translation is complete!");
            return;
        }
        translateText(sourceText);
    };

    // React code for UI rendering
    return (
        <div className="translate-app">
            <div className="header">
                <h1 className="title">
                    👋AuslanLive
                </h1>
            </div>
            
            <div className="main-content">
                <ToasterWithMax 
                    max={3}
                    position="top-right"
                    toastOptions={{
                        style: {
                            background: 'rgba(255, 255, 255, 0.1)',
                            backdropFilter: 'blur(10px)',
                            color: '#ffffff',
                            border: '1px solid rgba(255, 255, 255, 0.2)',
                            borderRadius: '12px',
                        },
                    }}
                />
                
                {mode === "videoToText" ? (
                    <>
                        <div style={styles.panel} className={`panel ${animationState.isAnimating ? 'panel-swap-animation' : ''}`}>
                            <h2 style={styles.panelTitle}>Auslan</h2>
                            <div style={styles.videoInputContainer}>
                                <VideoInput ref={videoInputRef} onCameraStart={handleCameraStart} isMobile={isMobile} />
                            </div>
                        </div>

                        <SwapControls
                            onSwap={handleSwap}
                            onTranslate={handleTextToVideo}
                            animationState={animationState}
                            loading={loading}
                            isMobile={isMobile}
                        />

                        <div style={{...styles.panel, ...(isMobile ? styles.panelMobile : {})}} className={`panel ${animationState.isAnimating ? 'panel-swap-animation' : ''}`}>
                            <h2 style={styles.panelTitle}>Text</h2>
                            {loading ? (
                                <div style={{...styles.loadingPlaceholder, ...(isMobile ? styles.loadingPlaceholderMobile : {})}}>
                                    <div style={styles.spinner}></div>
                                    <p style={styles.loadingText}>Processing sign language...</p>
                                </div>
                            ) : (
                                <div style={{ position: 'relative', width: '100%', display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
                                    <textarea
                                        placeholder='Translation will appear here...'
                                        value={translatedText}
                                        readOnly
                                        style={styles.textarea}
                                    />
                                    {showClearButton && (
                                        <button 
                                            onClick={handleClearText} 
                                            style={styles.clearButton}
                                            className={`clear-button ${clearButtonAnimation}`}
                                        >
                                            Clear
                                        </button>
                                    )}
                                </div>
                            )}
                        </div>
                    </>
                ) : (
                    <>
                        <div style={{...styles.panel, ...(isMobile ? styles.panelMobile : {})}} className={`panel ${animationState.isAnimating ? 'panel-swap-animation' : ''}`}>
                            <h2 style={styles.panelTitle}>Text</h2>
                            <textarea
                                placeholder='Enter text to convert to sign language...'
                                value={sourceText}
                                onChange={(e) => setSourceText(e.target.value)}
                                onKeyDown={handleKeyDown}
                                style={styles.textarea}
                            />
                        </div>

                        <SwapControls
                            onSwap={handleSwap}
                            onTranslate={handleTextToVideo}
                            animationState={animationState}
                            loading={loading}
                            isMobile={isMobile}
                        />

                        <div style={{...styles.panel, ...(isMobile ? styles.panelMobile : {})}} className={`panel ${animationState.isAnimating ? 'panel-swap-animation' : ''}`}>
                            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                                <h2 style={styles.panelTitle}>Auslan</h2>
                            </div>
                            
                            <div style={{ position: 'absolute', top: '16px', right: '16px', zIndex: 10 }}>
                                <GrammarPill 
                                    grammarParsedText={grammarParsedText}
                                    mode={mode}
                                    isMobile={isMobile}
                                    alwaysShowGrammar={alwaysShowGrammar}
                                    setAlwaysShowGrammar={setAlwaysShowGrammar}
                                />
                            </div>
                            
                            {loading ? (
                                <div style={{...styles.loadingPlaceholder, ...(isMobile ? styles.loadingPlaceholderMobile : {})}}>
                                    <div style={styles.spinner}></div>
                                    <p style={styles.loadingText}>Generating sign language video...</p>
                                </div>
                            ) : animatedSignVideo ? (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', flex: 1, minHeight: 0, overflow: 'hidden' }}>
                                    <GrammarDisplay 
                                        grammarParsedText={grammarParsedText}
                                        alwaysShowGrammar={alwaysShowGrammar}
                                    />
                                    <div style={{ ...styles.videoContainer, flex: 1, minHeight: 0 }}>
                                        <video
                                            src={animatedSignVideo}
                                            controls
                                            autoPlay
                                            loop
                                            style={styles.video}
                                            onLoadedMetadata={(e) => (e.target.playbackRate = 1.0)}
                                        />
                                    </div>
                                </div>
                            ) : (
                                <div style={{...styles.videoPlaceholder, padding: "5px"}}>
                                    <div style={styles.placeholderIcon}>🎬</div>
                                    <p style={styles.placeholderText}>
                                        Enter text to generate the Auslan video!
                                    </p>
                                </div>
                            )}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default TranslateApp;