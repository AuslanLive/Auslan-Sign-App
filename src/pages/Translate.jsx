import React, { useState, useRef, useEffect } from "react";
import VideoInput from "../components/VideoInput";
import WordSelectionModal from "../components/WordSelectionModal";
import { storage, ref, getDownloadURL } from "../firebase";
import wordList from '../fullWordList.json';
import 'react-toastify/dist/ReactToastify.css';
import { Toaster, toast } from 'react-hot-toast';
import { styles } from '../styles/TranslateStyles';
import '../styles/TranslateStyles.css';

// Add pulse animation CSS
const pulseKeyframes = `
@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}
`;

// Inject CSS
if (typeof document !== 'undefined') {
    const style = document.createElement('style');
    style.textContent = pulseKeyframes;
    document.head.appendChild(style);
}


const API_BASE_URL = "/api"


const TranslateApp = () => {
    const [mode, setMode] = useState("videoToText");
    const [sourceText, setSourceText] = useState("");
    const [translatedText, setTranslatedText] = useState("");
    const [sentence, setSentence] = useState(""); // New state for building sentences
    const [animatedSignVideo, setAnimatedSignVideo] = useState(null);
    const videoInputRef = useRef(null);
    const [loading, setLoading] = useState(false);
    const [isPolling, setIsPolling] = useState(true); // State to control API polling
    const [isAnimating, setIsAnimating] = useState(false);
    const [showClearButton, setShowClearButton] = useState(false);
    const [clearButtonAnimation, setClearButtonAnimation] = useState('');
    const [swapButtonRepositioning, setSwapButtonRepositioning] = useState(false);
    const [translateButtonAnimation, setTranslateButtonAnimation] = useState('');
    const [showTranslateButton, setShowTranslateButton] = useState(mode === "textToVideo");
    const [top5Predictions, setTop5Predictions] = useState([]); // top 5 predictions here
    const [showWordSelectionModal, setShowWordSelectionModal] = useState(false); // for modal selection
    const [modelStatus, setModelStatus] = useState("Ready to detect signs"); // Current model status
    const [currentSign, setCurrentSign] = useState(""); // Current sign being recorded
    const [hasHandsDetected, setHasHandsDetected] = useState(false); // Track hand detection
    const [redoCooldown, setRedoCooldown] = useState(false); // Prevent immediate modals after redo 

    // Function to handle camera start notification
    const handleCameraStart = () => {
        setIsPolling(true);
        if (videoInputRef.current) {
            videoInputRef.current.startTransmission();
        }
    };

    const pauseVideoProcessing = () => {
        setIsPolling(false);
        setModelStatus("Processing paused - waiting for your selection");
        setCurrentSign("");
        if (videoInputRef.current) {
            videoInputRef.current.pauseTransmission();
        }
    };

    const resumeVideoProcessing = () => {
        setIsPolling(true);
        setModelStatus("Ready to detect signs");
        setCurrentSign("");
        if (videoInputRef.current) {
            videoInputRef.current.resumeTransmission();
        }
    };

    // Function to swap between modes
    const handleSwap = () => {
        if (isAnimating) return; // Prevent multiple swaps during animation
        
        setIsAnimating(true);
        setSwapButtonRepositioning(true);
        setTranslatedText(""); // Clear the translated text on swap
        setSentence(""); // Clear the sentence on swap
        setShowWordSelectionModal(false); // Hide word selection modal on swap
        setTop5Predictions([]); // Clear predictions on swap

        // Handle translate button exit animation if switching from textToVideo
        if (mode === "textToVideo") {
            setTranslateButtonAnimation('translate-button-exit');
            setTimeout(() => {
                setShowTranslateButton(false);
            }, 400); // 50% faster from 600ms
        }

        if (mode === "videoToText" && videoInputRef.current) {
            videoInputRef.current.stopCamera(); // Stop the camera when switching to textToVideo
        }

        // Reset polling state when switching modes
        setIsPolling(true);

        // Synchronized with panel animation - mode change happens at panel midpoint
        setTimeout(() => {
            setMode((prevMode) =>
                prevMode === "videoToText" ? "textToVideo" : "videoToText"
            );
            
            // Handle translate button enter animation - starts with panel slide-in
            if (mode === "videoToText") {
                setShowTranslateButton(true);
                setTranslateButtonAnimation('translate-button-enter');
            }
            
            // Reset animation state - synchronized with panel animation completion
            setTimeout(() => {
                setIsAnimating(false);
                setSwapButtonRepositioning(false);
                setTranslateButtonAnimation('');
            }, 800); // 50% faster from 1200ms
        }, 400); // 50% faster from 600ms
    };
    const get_sign_trans = async () => {
        try {
            // CRITICAL: Only process if hands are detected and no modal is open
            if (!hasHandsDetected || showWordSelectionModal || redoCooldown) {
                console.log(" get_sign_trans: Skipping - hands:", hasHandsDetected, "modal:", showWordSelectionModal, "cooldown:", redoCooldown);
                return;
            }

            console.log(" get_sign_trans: Making API call to detect sign...");
            const response = await fetch(
                API_BASE_URL + "/get_sign_to_text",
                {
                    method: "GET",
                }
            );

            const data = await response.json();

            // Output parsed sentence to console
            console.log("Full response:", data);

            // Check if we have new predictions to show
            if (data.top_5 && data.top_5.length > 0 && !redoCooldown && !showWordSelectionModal) {
                // Print top 5 to terminal
                console.log("=== TOP 5 PREDICTIONS ===");
                data.top_5.forEach((prediction, index) => {
                    console.log(`${index + 1}. ${prediction[0]} (${(prediction[1] * 100).toFixed(1)}%)`);
                });
                console.log("========================");
                
                setTop5Predictions(data.top_5);
                setShowWordSelectionModal(true);
                setModelStatus("Sign detected! Please select from options below");
                setCurrentSign(data.top_1?.label || "Unknown sign");
                pauseVideoProcessing();
                // Don't automatically set translated text - wait for user selection
            } else if (data.translation) {
                // Fallback to old behavior if no top_5 data
                setTranslatedText(data.translation);
            }
        } catch (error) {
            console.error("Error:", error);
            setModelStatus("Error connecting to model");
            setTranslatedText(
                `Error: ${error.message}. Please check the API and input.`
            );
        }
    };
    const getGemFlag = async () => {
        try {
            const response = await fetch(API_BASE_URL + "/getGemFlag", {
                method: "GET",
            });

            const data = await response.json();

            // Output parsed sentence to console
            console.log("GeminiFlag:", data);

            // Set translated text or handle fallback
            const isInGemini = data.flag;

            // =======================================
            // PUT CODE HERE FOR GEMINI FLAG HANDLING
            // =======================================
            console.log("GeminiFlag:", isInGemini);
            setLoading(isInGemini);
        } catch (error) {
            console.error("Error:", error);
            setTranslatedText(
                `Error: ${error.message}. Please check the API and input.`
            );
        }
    };

    // old code - trigger every second
    // setInterval(get_sign_trans, 1000);

    // new code - only trigger when mode is videoToText and polling is enabled
    // CRITICAL: Don't poll when modal is open or during redo cooldown
    useEffect(() => {
        let interval;
        if (mode === "videoToText" && isPolling && !showWordSelectionModal && !redoCooldown) {
            interval = setInterval(function () {
                get_sign_trans();
                getGemFlag();
            }, 1000);
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [mode, isPolling, showWordSelectionModal, redoCooldown]);


    
    const checkTextAgainstWordListJson = (text) => {
        // Split the text into words, encode, and convert to lowercase
        const words = text.split(/\s+/).map(word => encodeURIComponent(word.toLowerCase()));

        // Convert wordList entries to lowercase for case-insensitive comparison
        const existingWords = new Set(wordList.map(item => item.toLowerCase()));

        // Filter out words that do not exist in the existing words set
        const missingWords = words.filter(word => !existingWords.has(word));
    
        if (missingWords.length > 0) {
            console.log(`The following words do not exist: ${missingWords}`);
            toast.error(`The following words do not exist: ${missingWords.join(', ')}`);
        }
    };

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
            }, 270); // 50% faster from 400ms
        }
    }, [translatedText, showClearButton]);

    // Monitor hand detection status
    useEffect(() => {
        const interval = setInterval(() => {
            if (videoInputRef.current && isPolling && !showWordSelectionModal && !redoCooldown) {
                const handsDetected = videoInputRef.current.hasHandsDetected;
                setHasHandsDetected(handsDetected);
                
                if (handsDetected) {
                    setModelStatus("Hands detected - recording sign...");
                    console.log(" Translate: Hands detected, ready for sign detection");
                } else {
                    setModelStatus("Ready to detect signs - show your hands");
                    console.log(" Translate: No hands detected, waiting for hands");
                }
            } else if (showWordSelectionModal) {
                setModelStatus("Sign detected! Please select from options below");
                console.log(" Translate: Modal is open, waiting for user selection");
            } else if (redoCooldown) {
                setModelStatus("Cooldown period - sign a new word to continue");
                console.log(" Translate: Redo cooldown active");
            }
        }, 500); // Check every 500ms

        return () => clearInterval(interval);
    }, [isPolling, showWordSelectionModal, redoCooldown]);

    // Clear any stale state on component mount (handles page refresh)
    useEffect(() => {
        // Force clear all modal-related state
        setShowWordSelectionModal(false);
        setTop5Predictions([]);
        setModelStatus("Ready to detect signs");
        setCurrentSign("");
        setHasHandsDetected(false);
        setTranslatedText("");
        setSentence("");
        setRedoCooldown(false);
        setIsPolling(false);
        
        // Stop any ongoing transmission
        if (videoInputRef.current) {
            videoInputRef.current.stopTransmission();
        }
        
        console.log("Page refreshed - all state cleared");
    }, []);

    // Function to handle word selection from top 5 predictions
    const handleWordSelection = (selectedWord) => {
        // Add the selected word to the sentence
        setSentence(prevSentence => {
            const newSentence = prevSentence ? `${prevSentence} ${selectedWord}` : selectedWord;
            // Update the displayed text with the new sentence
            setTranslatedText(newSentence);
            return newSentence;
        });
        
        // Hide the modal
        setShowWordSelectionModal(false);
        setTop5Predictions([]);
        
        // Resume video processing after selection
        resumeVideoProcessing();
    };

    // Function to handle "Redo" option
    const handleRedo = () => {
        setShowWordSelectionModal(false);
        setTop5Predictions([]);
        setRedoCooldown(true);
        setModelStatus("Cooldown period - sign a new word to continue");
        setCurrentSign("");
        
        // Set cooldown for 3 seconds
        setTimeout(() => {
            setRedoCooldown(false);
            setModelStatus("Ready to detect signs");
        }, 3000);
        
        // Resume video processing after redo
        resumeVideoProcessing();
    };

    // Function to close modal
    const handleCloseModal = () => {
        setShowWordSelectionModal(false);
        setTop5Predictions([]);
        // Resume video processing after closing modal
        resumeVideoProcessing();
    };

    // Function to clear translated text
    const handleClearText = () => {
        setClearButtonAnimation('clear-button-exit');
        setTimeout(() => {
            setTranslatedText("");
            setSentence(""); // Also clear the sentence
            setShowWordSelectionModal(false);
            setTop5Predictions([]);
            setModelStatus("Ready to detect signs");
            setCurrentSign("");
            setRedoCooldown(false); // Reset redo cooldown
            setIsPolling(false); // Stop API polling when clearing text
            // Stop keypoint transmission when clearing text
            if (videoInputRef.current) {
                videoInputRef.current.stopTransmission();
            }
        }, 133); // 50% faster from 200ms
    };

    // Function to convert text to video

    const handleTextToVideo = async () => {
        const fixedSourceText = sourceText.trim();
        console.log("Sending Source Text:", fixedSourceText);
        checkTextAgainstWordListJson(fixedSourceText);
        setLoading(true); // Set loading to true while fetching video

        // Step 1: API call to parse sentence to Auslan grammar
        try {
            const response = await fetch(API_BASE_URL + "/t2s", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ t2s_input: fixedSourceText }),
            });

            if (!response.ok)
                throw new Error(`HTTP error! status: ${response.status}`);

            const data = await response.json();
            console.log("Full response:", data);

            // Set translated text
            const translatedText = data.message || "No translation available.";
            setTranslatedText(translatedText);

            // Step 2: Generate the Firebase video path using the translated text
            const firebaseURL = "gs://auslan-194e5.appspot.com/output_videos/";
            const fileType = ".mp4";
            // const parsedVideoName = translatedText || fixedSourceText;

            let parsedVideoName;
            if (Array.isArray(translatedText)) {
                // Format as ['ITEM1', 'ITEM2', 'ITEM3'] to match what pose_video_creator.py creates in firebase
                // Ensure each item is wrapped in quotes and joined by commas
                const formattedItems = translatedText.map(item => `'${item}'`);
                parsedVideoName = `[${formattedItems.join(', ')}]`;
            } else {
                parsedVideoName = translatedText || fixedSourceText;
            }

            const videoPath = firebaseURL + parsedVideoName + fileType;

            console.log("Video Path:", videoPath);
            console.log("Parsed Video Name:", parsedVideoName);

            // Step 3: Fetch the video URL from Firebase
            const videoRef = ref(storage, videoPath);
            const videoUrl = await getDownloadURL(videoRef);
            setAnimatedSignVideo(videoUrl);
        } catch (error) {
            console.error("Error:", error);
            setTranslatedText(
                `Error: ${error.message}. Please check the API and input.`
            );
        } finally {
            setLoading(false); // Set loading to false after fetching video
        }
    };
    
    return (
        <div style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "flex-start",
            width: "100%",
            maxWidth: "100vw",
            margin: "0 auto",
            padding: "10px",
            minHeight: "100vh",
            background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)",
            position: "relative",
            boxSizing: "border-box",
        }}>
            <div style={{
                textAlign: 'center',
                marginBottom: '2rem',
                paddingTop: '1rem'
            }}>
                <h1 style={{
                    fontSize: '3rem',
                    fontWeight: 'bold',
                    background: 'linear-gradient(135deg, #00f2fe 0%, #3b82f6 50%,  #a855f7 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                    margin: 0,
                    textShadow: 'none',
                    filter: 'drop-shadow(2px 2px 4px rgba(0, 0, 0, 0.5))'
                }}>
                    AuslanLive
                </h1>
            </div>
            
            <div style={{
                display: "flex",
                flexDirection: "row",
                alignItems: "center",
                justifyContent: "center",
                gap: "25px",
                width: "100%",
                maxWidth: "100vw",
                flex: 1,
            }}>
                <Toaster 
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
                
                {/* Permanent status toast */}
                <div style={{
                    position: 'fixed',
                    top: '20px',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    zIndex: 1000,
                    background: 'rgba(26, 26, 46, 0.95)',
                    backdropFilter: 'blur(10px)',
                    color: '#ffffff',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    borderRadius: '12px',
                    padding: '12px 20px',
                    fontSize: '14px',
                    fontWeight: '500',
                    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    minWidth: '300px',
                    justifyContent: 'center'
                }}>
                    <div style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        backgroundColor: showWordSelectionModal ? '#ffc107' : redoCooldown ? '#ff6b35' : isPolling ? '#00ff00' : '#ff4444',
                        animation: isPolling && !showWordSelectionModal && !redoCooldown ? 'pulse 2s infinite' : 'none'
                    }}></div>
                    <span>{modelStatus}</span>
                    {currentSign && (
                        <span style={{ 
                            color: '#00f2fe', 
                            fontWeight: '600',
                            marginLeft: '8px'
                        }}>
                            "{currentSign}"
                        </span>
                    )}
                </div>
                {mode === "videoToText" ? (
                    <>
                        <div style={styles.panel} className={`panel ${isAnimating ? 'panel-swap-animation' : ''}`}>
                            <h2 style={styles.panelTitle}>Auslan</h2>
                            <div style={styles.videoInputContainer}>
                                <VideoInput ref={videoInputRef} onCameraStart={handleCameraStart} />
                            </div>
                        </div>

                        <div style={styles.buttons}>
                            <button 
                                onClick={handleSwap} 
                                style={styles.swapButton} 
                                className={`swap-button ${isAnimating ? 'swap-button-animation' : ''} ${swapButtonRepositioning ? 'swap-button-reposition' : ''}`}
                                disabled={isAnimating}
                            >
                                <div style={styles.buttonContent}>
                                    <span style={styles.swapIcon} className={isAnimating ? 'swap-icon-animation' : ''}>⇄</span>
                                    Swap
                                </div>
                            </button>
                        </div>

                        <div style={styles.panel} className={`panel ${isAnimating ? 'panel-swap-animation' : ''}`}>
                            <h2 style={styles.panelTitle}>Text</h2>
                            {loading ? (
                                <div style={styles.loadingPlaceholder}>
                                    <div style={styles.spinner}></div>
                                    <p style={styles.loadingText}>Processing sign language...</p>
                                </div>
                            ) : (
                                <div style={{ position: 'relative', width: '100%', height: '100%' }}>
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
                        <div style={styles.panel} className={`panel ${isAnimating ? 'panel-swap-animation' : ''}`}>
                            <h2 style={styles.panelTitle}>Text</h2>
                            <textarea
                                placeholder='Enter text to convert to sign language...'
                                value={sourceText}
                                onChange={(e) => setSourceText(e.target.value)}
                                style={styles.textarea}
                            />
                        </div>

                        <div style={styles.buttons}>
                            <button 
                                onClick={handleSwap} 
                                style={styles.swapButton} 
                                className={`swap-button ${isAnimating ? 'swap-button-animation' : ''} ${swapButtonRepositioning ? 'swap-button-reposition' : ''}`}
                                disabled={isAnimating}
                            >
                                <div style={styles.buttonContent}>
                                    <span style={styles.swapIcon} className={isAnimating ? 'swap-icon-animation' : ''}>⇄</span>
                                    Swap
                                </div>
                            </button>
                            {showTranslateButton && (
                                <button
                                    onClick={handleTextToVideo}
                                    style={styles.translateButton}
                                    className={`translate-button ${translateButtonAnimation}`}
                                >
                                    <div style={styles.buttonContent}>
                                        <span style={styles.translateIcon}>✨</span>
                                        Translate
                                    </div>
                                </button>
                            )}
                        </div>

                        <div style={styles.panel} className={`panel ${isAnimating ? 'panel-swap-animation' : ''}`}>
                            <h2 style={styles.panelTitle}>Auslan</h2>
                            {loading ? (
                                <div style={styles.loadingPlaceholder}>
                                    <div style={styles.spinner}></div>
                                    <p style={styles.loadingText}>Generating sign language video...</p>
                                </div>
                            ) : animatedSignVideo ? (
                                <div style={styles.videoContainer}>
                                    <video
                                        src={animatedSignVideo}
                                        controls
                                        autoPlay
                                        loop
                                        style={styles.video}
                                        onLoadedMetadata={(e) =>
                                            (e.target.playbackRate = 1.0)
                                        }
                                    />
                                </div>
                            ) : (
                                <div style={{...styles.videoPlaceholder, padding: "5px"}}>
                                    <div style={styles.placeholderIcon}>🎬</div>
                                    <p style={styles.placeholderText}>
                                        Enter text and click translate to see the sign language video
                                    </p>
                                </div>
                            )}
                        </div>
                    </>
                )}
            </div>
            
            {/* Word Selection Modal */}
            <WordSelectionModal
                isOpen={showWordSelectionModal}
                top5Predictions={top5Predictions}
                onWordSelect={handleWordSelection}
                onRedo={handleRedo}
                onClose={handleCloseModal}
            />
        </div>
    );
};

export default TranslateApp;