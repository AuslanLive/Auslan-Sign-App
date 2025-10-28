import React, { useState, useRef, useEffect } from "react";
import VideoInput from "../components/VideoInput";
import ToasterWithMax from "../components/ToasterWithMax";
import GrammarPill from "../components/GrammarPill";
import Top5Selector from "../components/Top5Selector";
import EditableWord from "../components/EditableWord";
import InlineSelector from "../components/InlineSelector";
import FrameProgressIndicator from "../components/FrameProgressIndicator";
import { storage, ref, getDownloadURL } from "../firebase";
import wordList from '../fullWordList.json';
import 'react-toastify/dist/ReactToastify.css';
import { toast } from 'react-hot-toast';
import { styles } from '../styles/TranslateStyles';
import '../styles/TranslateStyles.css';


const API_BASE_URL = "/api"

const TranslateApp = () => {
    const [mode, setMode] = useState("videoToText");
    const [sourceText, setSourceText] = useState("");
    const [translatedText, setTranslatedText] = useState("");
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
    const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
    const [grammarParsedText, setGrammarParsedText] = useState("");
    const [alwaysShowGrammar, setAlwaysShowGrammar] = useState(() => 
        localStorage.getItem("auslan:alwaysShowGrammar") === "true"
    );
    
    // State for honors model top-5 predictions
    const [pendingPredictions, setPendingPredictions] = useState([]);
    const [showTop5Selector, setShowTop5Selector] = useState(false);
    const [lastPredictionId, setLastPredictionId] = useState(null);
    
    // State for sentence with word objects (for click-to-fix)
    const [sentenceWords, setSentenceWords] = useState([]);
    
    // State for processing indicator
    const [isProcessingActive, setIsProcessingActive] = useState(false);
    
    // State for frame collection progress
    const [frameStatus, setFrameStatus] = useState(null);
    const [showFrameProgress, setShowFrameProgress] = useState(false);

    // Function to handle camera start notification
    const handleCameraStart = () => {
        setIsPolling(true);
        if (videoInputRef.current) {
            videoInputRef.current.startTransmission();
        }
    };
    
    // Handle word selection from top-5
    const handleWordSelection = async (selectedWord) => {
        try {
            const response = await fetch(API_BASE_URL + "/select_word", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ word: selectedWord })
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log("Word selected:", data);
                
                // Clear the top-5 selector
                setPendingPredictions([]);
                setShowTop5Selector(false);
                
                // Show success toast
                toast.success(`Added: ${selectedWord}`);
            }
        } catch (error) {
            console.error("Error selecting word:", error);
            toast.error("Failed to add word");
        }
    };
    
    // Handle skipping prediction
    const handleSkipPrediction = async () => {
        try {
            await fetch(API_BASE_URL + "/skip_prediction", {
                method: "POST"
            });
            
            // Clear the top-5 selector
            setPendingPredictions([]);
            setShowTop5Selector(false);
            
            toast("Skipped prediction", { icon: "⊘" });
        } catch (error) {
            console.error("Error skipping prediction:", error);
        }
    };
    
    // Handle word replacement (click-to-fix)
    const handleReplaceWord = async (wordId, newWord) => {
        try {
            const response = await fetch(API_BASE_URL + "/replace_word", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ word_id: wordId, new_word: newWord })
            });
            
            if (response.ok) {
                toast.success(`Changed to: ${newWord}`);
                // Sentence words will update via polling
            } else {
                toast.error("Failed to replace word");
            }
        } catch (error) {
            console.error("Error replacing word:", error);
            toast.error("Error replacing word");
        }
    };

    // Function to swap between modes
    const handleSwap = () => {
        if (isAnimating) return; // Prevent multiple swaps during animation
        
        setIsAnimating(true);
        setSwapButtonRepositioning(true);
        setTranslatedText(""); // Clear the translated text on swap
        // Remove this line: setGrammarParsedText(""); // Don't clear grammar text on swap

        // Handle translate button exit animation if switching from textToVideo
        if (mode === "textToVideo") {
            setTranslateButtonAnimation('translate-button-exit');
            setTimeout(() => {
                setShowTranslateButton(false);
            }, 400); // Matches exit animation duration (0.4s)
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
            
            // Reset animation state - synchronized with swap button animation completion
            setTimeout(() => {
                setIsAnimating(false);
                setSwapButtonRepositioning(false);
                setTranslateButtonAnimation('');
            }, 400); // Now matches both enter/exit animation duration (0.4s)
        }, 400); // Midpoint of 800ms swap animation
    };
    const get_sign_trans = async () => {
        try {
            const response = await fetch(
                API_BASE_URL + "/get_sign_to_text",
                {
                    method: "GET",
                }
            );

            const data = await response.json();

            // Output parsed sentence to console
            console.log("Full response:", data);

            // Set translated text or handle fallback
            const translatedText = data.translation;
            setTranslatedText(translatedText);
        } catch (error) {
            console.error("Error:", error);
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
    // Disabled get_sign_trans() - we now use sentenceWords word-by-word system
    useEffect(() => {
        let interval;
        if (mode === "videoToText" && isPolling) {
            interval = setInterval(function () {
                // get_sign_trans(); // DISABLED - replaced by sentenceWords system
                getGemFlag();
            }, 1000);
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [mode, isPolling]);
    
    // Sync sentenceWords to translatedText for display
    useEffect(() => {
        if (sentenceWords && sentenceWords.length > 0) {
            const words = sentenceWords.map(item => 
                typeof item === 'object' ? item.word : item
            ).join(' ');
            setTranslatedText(words);
        }
    }, [sentenceWords]);
    
    // Poll for sentence words (honors model)
    useEffect(() => {
        let interval;
        if (mode === "videoToText" && isPolling) {
            interval = setInterval(async () => {
                try {
                    const response = await fetch(API_BASE_URL + "/api/get_sentence_words");
                    if (response.ok) {
                        const data = await response.json();
                        if (data.words && Array.isArray(data.words)) {
                            setSentenceWords(data.words);
                        }
                    }
                } catch (error) {
                    console.error("Error fetching sentence words:", error);
                }
            }, 500); // Poll every 500ms for smooth updates
        }
        
        return () => {
            if (interval) clearInterval(interval);
        };
    }, [mode, isPolling]);
    
    // Poll for pending top-5 predictions (honors model)
    useEffect(() => {
        let interval;
        if (mode === "videoToText" && isPolling) {
            interval = setInterval(async () => {
                try {
                    const response = await fetch(API_BASE_URL + "/get_pending_predictions");
                    const data = await response.json();
                    
                    if (data.predictions && data.predictions.length > 0) {
                        // Create unique ID for this prediction set
                        const newId = JSON.stringify(data.predictions);
                        
                        // Only update if predictions actually changed (prevents flickering)
                        if (newId !== lastPredictionId) {
                            setPendingPredictions(data.predictions);
                            setShowTop5Selector(true);
                            setLastPredictionId(newId);
                        }
                    } else if (data.predictions && data.predictions.length === 0) {
                        // Clear predictions when none pending
                        if (showTop5Selector) {
                            setPendingPredictions([]);
                            setShowTop5Selector(false);
                            setLastPredictionId(null);
                        }
                    }
                } catch (error) {
                    console.error("Error fetching pending predictions:", error);
                }
            }, 500); // Check more frequently for responsive UX
        } else {
            setPendingPredictions([]);
            setShowTop5Selector(false);
            setLastPredictionId(null);
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [mode, isPolling, lastPredictionId, showTop5Selector]);
    
    // Poll for sentence words (for click-to-fix functionality)
    useEffect(() => {
        let interval;
        if (mode === "videoToText" && isPolling) {
            interval = setInterval(async () => {
                try {
                    const response = await fetch(API_BASE_URL + "/get_sentence_words");
                    const data = await response.json();
                    
                    if (data.words) {
                        setSentenceWords(data.words);
                    }
                } catch (error) {
                    console.error("Error fetching sentence words:", error);
                }
            }, 500); // Poll at same rate as pending predictions
        } else {
            setSentenceWords([]);
        }
        
        return () => {
            if (interval) clearInterval(interval);
        };
    }, [mode, isPolling]);
    
    // Poll for processing status to show visual indicator
    useEffect(() => {
        let interval;
        if (mode === "videoToText" && isPolling) {
            interval = setInterval(async () => {
                try {
                    const response = await fetch(API_BASE_URL + "/get_processing_status");
                    const data = await response.json();
                    
                    // Active when NOT paused and camera is on
                    setIsProcessingActive(!data.is_paused);
                } catch (error) {
                    console.error("Error fetching processing status:", error);
                }
            }, 300); // Poll frequently for smooth UI feedback
        } else {
            setIsProcessingActive(false);
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [mode, isPolling]);
    
    // Poll for frame collection status
    useEffect(() => {
        let interval;
        if (mode === "videoToText" && isPolling) {
            interval = setInterval(async () => {
                try {
                    const response = await fetch(API_BASE_URL + "/get_frame_status");
                    const data = await response.json();
                    
                    setFrameStatus(data);
                    
                    // Show progress indicator when actively collecting frames
                    // or when close to completing (> 10 frames)
                    const shouldShow = data.frames_collected > 0 && !showTop5Selector;
                    setShowFrameProgress(shouldShow);
                    
                } catch (error) {
                    console.error("Error fetching frame status:", error);
                }
            }, 100); // Poll very frequently for smooth progress bar
        } else {
            setFrameStatus(null);
            setShowFrameProgress(false);
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [mode, isPolling, showTop5Selector]);

    // Update size on window change
    useEffect(() => {
        const handleResize = () => {
            setIsMobile(window.innerWidth < 768)
        }

        handleResize();

        window.addEventListener("resize", handleResize);

        return () =>{
            window.removeEventListener("resize", handleResize);
        }
    }, []);
    
    // Spacebar trigger for manual frame capture
    useEffect(() => {
        const handleKeyPress = async (e) => {
            // Only in videoToText mode, when camera is active, and modal is NOT showing
            if (mode === "videoToText" && isPolling && !showTop5Selector && e.code === 'Space') {
                e.preventDefault(); // Prevent page scroll
                
                // Trigger immediate prediction if we have enough frames
                try {
                    if (frameStatus && frameStatus.frames_collected >= 32) {
                        // Force a prediction by telling backend to process current buffer
                        toast("Capturing word...", { icon: "📸", duration: 1000 });
                        
                        const response = await fetch(API_BASE_URL + "/force_predict", {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json"
                            }
                        });
                        
                        if (!response.ok) {
                            toast.error("Failed to capture word");
                        }
                    } else {
                        toast("Need more frames! Keep signing...", { icon: "⚠️", duration: 1500 });
                    }
                } catch (error) {
                    console.error("Error triggering manual capture:", error);
                    toast.error("Error capturing word");
                }
            }
        };

        window.addEventListener("keydown", handleKeyPress);

        return () => {
            window.removeEventListener("keydown", handleKeyPress);
        };
    }, [mode, isPolling, showTop5Selector, frameStatus]);
    
    const checkTextAgainstWordListJson = (text) => {
        // Split the text into words, encode, and convert to lowercase
        const words = text.split(/\s+/).map(word => encodeURIComponent(word.toLowerCase()));

        // Convert wordList entries to lowercase for case-insensitive comparison
        const existingWords = new Set(wordList.map(item => item.toLowerCase()));

        // Filter out words that do not exist in the existing words set
        const missingWords = words.filter(word => !existingWords.has(word));
        console.log(missingWords)
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

    // Function to clear translated text
    const handleClearText = async () => {
        setClearButtonAnimation('clear-button-exit');
        
        // Clear sentence on backend
        try {
            await fetch(API_BASE_URL + "/clear_sentence", {
                method: "POST"
            });
        } catch (error) {
            console.error("Error clearing sentence:", error);
        }
        
        setTimeout(() => {
            setTranslatedText("");
            setSentenceWords([]); // Clear the word objects
            setPendingPredictions([]); // Clear pending predictions
            setShowTop5Selector(false); // Hide selector
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
        console.log("Sending Source Text:", fixedSourceText.length);
        if (fixedSourceText === null || fixedSourceText === undefined || fixedSourceText.trim().length === 0) {
            console.log(`No text to translate: ${fixedSourceText}`);
            toast.error(`No text to translate`);
            return;
        };

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
            
            // Extract grammar parsed text for the hint component
            if (Array.isArray(translatedText)) {
                setGrammarParsedText(translatedText.join(' '));
            } else if (typeof translatedText === 'string') {
                setGrammarParsedText(translatedText);
            } else {
                setGrammarParsedText("");
            }

            // Step 2: Generate the Firebase video path using the original array format
            const firebaseURL = "gs://auslan-194e5.appspot.com/output_videos/";
            const fileType = ".mp4";

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
            setGrammarParsedText(""); // Clear grammar text on error
        } finally {
            setLoading(false); // Set loading to false after fetching video
        }
    };

    // Function to handle Enter key press
    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && mode === 'textToVideo' && !loading) {
            e.preventDefault(); // Prevent default textarea behavior
            
            // Trigger dramatic translate button animation
            const translateButton = document.querySelector('.translate-button');
            if (translateButton) {
                // Initial dramatic press effect
                translateButton.style.transform = 'translateY(4px) scale(0.92)';
                translateButton.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.6)';
                
                setTimeout(() => {
                    // Bounce back with emphasis
                    translateButton.style.transform = 'translateY(-4px) scale(1.08)';
                    translateButton.style.boxShadow = '0 0 30px rgba(168, 85, 247, 0.8), 0 0 60px rgba(168, 85, 247, 0.6), 0 8px 25px rgba(0, 0, 0, 0.4)';
                }, 100);
                
                setTimeout(() => {
                    // Return to normal with slight overshoot
                    translateButton.style.transform = 'translateY(0) scale(1.02)';
                    translateButton.style.boxShadow = '';
                }, 250);
                
                setTimeout(() => {
                    // Final settle
                    translateButton.style.transform = 'translateY(0) scale(1)';
                }, 400);
            }
            
            handleTextToVideo();
        }
        
        // Prevent spacebar from triggering button clicks when textarea is focused
        if (e.key === ' ' && e.target.tagName === 'TEXTAREA') {
            // Allow normal spacebar behavior in textarea (adding spaces)
            return;
        }
    };

    // Function to handle translate button click with loading check
    const handleTranslateButtonClick = (e) => {
        // Prevent spacebar activation when button is focused
        if (e.type === 'keydown' && e.key === ' ') {
            e.preventDefault();
            return;
        }
        
        if (loading) {
            toast.error("Please wait until current translation is complete!");
            return;
        }
        handleTextToVideo();
    };

    // React code for UI rendering
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
            background: "linear-gradient(135deg, #0f0d2e 0%, #1a1545 15%, #2d1f65 35%, #4a2b85 60%, #5236a5 75%, #6b3cb8 90%, #7440c4 100%)",
            backgroundSize: "100% 100%",
            backgroundAttachment: "fixed",
            //animation: "gradientShift 15s ease-in-out infinite alternate",
            position: "relative",
            boxSizing: "border-box",
            minHeight: "100vh",
            overflow: "visible",
            height: "auto",
        }}>
            <link rel="icon" href="/Interpreter-Symbol-s-text.ico" />
            <div style={{
                textAlign: 'center',
                marginBottom: '2rem',
                paddingTop: '1rem'
            }}>
                <h1 style={{
                    fontSize: '3rem',
                    fontWeight: '700',
                    fontFamily: "'Inter', 'SF Pro Display', 'Segoe UI Variable', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
                    letterSpacing: '-0.03em',
                    fontFeatureSettings: "'cv02', 'cv03', 'cv04', 'cv11'",
                    background: 'linear-gradient(135deg, #008cff 0%, #3b82f6 40%, #a855f7 70%, #9155f1ff 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                    margin: 0,
                    textShadow: 'none',
                    filter: 'drop-shadow(2px 2px 4px rgba(0, 0, 0, 0.5))'
                }}>
                    👋AuslanLive
                </h1>
            </div>
            
            <div style={{
                display: "flex",
                flexDirection: isMobile ? "column" : "row",
                alignItems: "center",
                justifyContent: "center",
                gap: "25px",
                width: "100%",
                maxWidth: "100vw",
                flex: 1,
            }}>
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
                        <div style={styles.panel} className={`panel ${isAnimating ? 'panel-swap-animation' : ''}`}>
                            <h2 style={styles.panelTitle}>Auslan</h2>
                            
                            {isProcessingActive && (
                                <div style={{
                                    position: 'absolute',
                                    top: '16px',
                                    right: '16px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    padding: '8px 12px',
                                    backgroundColor: 'rgba(16, 185, 129, 0.15)',
                                    border: '2px solid rgba(16, 185, 129, 0.4)',
                                    borderRadius: '20px',
                                    zIndex: 10,
                                    animation: 'pulse 2s ease-in-out infinite'
                                }}>
                                    <div style={{
                                        width: '8px',
                                        height: '8px',
                                        backgroundColor: '#10b981',
                                        borderRadius: '50%',
                                        boxShadow: '0 0 8px #10b981',
                                        animation: 'blink 1.5s ease-in-out infinite'
                                    }} />
                                    <span style={{
                                        fontSize: '14px',
                                        fontWeight: '600',
                                        color: '#10b981',
                                        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
                                    }}>
                                        Processing
                                    </span>
                                </div>
                            )}
                            
                            <div style={styles.videoInputContainer}>
                                <VideoInput ref={videoInputRef} onCameraStart={handleCameraStart} isMobile={isMobile} />
                            </div>
                            
                        </div>
                        
                        <FrameProgressIndicator 
                            frameStatus={frameStatus}
                            isVisible={showFrameProgress}
                        />

                        <div style={{...styles.buttons, ...(isMobile ? styles.buttonsMobileTag : {})}}>
                            <button 
                                onClick={handleSwap} 
                                style={{
                                    ...styles.swapButton,
                                    transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
                                }} 
                                className={`swap-button ${isAnimating ? 'swap-button-animation' : ''} ${swapButtonRepositioning ? 'swap-button-reposition' : ''}`}
                            >
                                <div style={styles.buttonContent}>
                                    <span style={styles.swapIcon} className={isAnimating ? 'swap-icon-animation' : ''}>⇄</span>
                                </div>
                            </button>
                            {showTranslateButton && (
                                <button
                                    onClick={handleTranslateButtonClick}
                                    style={{
                                        ...styles.translateButton,
                                        opacity: loading ? 0.6 : 1,
                                        cursor: loading ? 'not-allowed' : 'pointer'
                                    }}
                                    className={`translate-button ${translateButtonAnimation}`}
                                >
                                    <div style={styles.buttonContent}>
                                        <span style={styles.translateIcon}>✨</span>
                                        {loading ? 'Translating...' : 'Translate'}
                                    </div>
                                </button>
                            )}
                        </div>

                        <div style={{...styles.panel, ...(isMobile ? styles.panelMobile : {})}} className={`panel ${isAnimating ? 'panel-swap-animation' : ''}`}>
                            <h2 style={styles.panelTitle}>Text</h2>
                            {loading ? (
                                <div style={{...styles.loadingPlaceholder, ...(isMobile ? styles.loadingPlaceholderMobile : {})}}>
                                    <div style={styles.spinner}></div>
                                    <p style={styles.loadingText}>Processing sign language...</p>
                                </div>
                            ) : (
                                <div style={{ position: 'relative', width: '100%',  display: 'flex', flexDirection: 'column', flex: 1,  minHeight: 0, }}>
                                    <div
                                        style={{
                                            ...styles.textarea,
                                            overflow: 'auto',
                                            whiteSpace: 'normal',
                                            fontSize: '1.5em',
                                            lineHeight: '1.8',
                                            padding: '20px',
                                            paddingLeft: '28px'
                                        }}
                                    >
                                        {sentenceWords.length === 0 && !showTop5Selector && (
                                            <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>
                                                Translation will appear here...
                                            </span>
                                        )}
                                        
                                        {/* Render editable words */}
                                        {sentenceWords.map((wordData, index) => (
                                            <EditableWord
                                                key={wordData.id || index}
                                                wordData={wordData}
                                                onReplace={handleReplaceWord}
                                            />
                                        ))}
                                        
                                        {showTop5Selector && pendingPredictions.length > 0 && pendingPredictions[0].top5 && (
                                            <InlineSelector
                                                predictions={pendingPredictions[0]}
                                                onSelect={handleWordSelection}
                                                onSkip={handleSkipPrediction}
                                            />
                                        )}
                                    </div>
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
                        <div style={{...styles.panel, ...(isMobile ? styles.panelMobile : {})}} className={`panel ${isAnimating ? 'panel-swap-animation' : ''}`}>
                            <h2 style={styles.panelTitle}>Text</h2>
                            <textarea
                                placeholder='Enter text to convert to sign language...'
                                value={sourceText}
                                onChange={(e) => setSourceText(e.target.value)}
                                onKeyDown={handleKeyDown}
                                style={styles.textarea}
                            />
                        </div>

                        <div style={{...styles.buttons, ...(isMobile ? styles.buttonsMobileTag : {})}}>
                            <button 
                                onClick={handleSwap} 
                                style={{
                                    ...styles.swapButton,
                                    transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
                                }} 
                                className={`swap-button ${isAnimating ? 'swap-button-animation' : ''} ${swapButtonRepositioning ? 'swap-button-reposition' : ''}`}
                            >
                                <div style={styles.buttonContent}>
                                    <span style={styles.swapIcon} className={isAnimating ? 'swap-icon-animation' : ''}>⇄</span>
                                </div>
                            </button>
                            {showTranslateButton && (
                                <button
                                    onClick={handleTranslateButtonClick}
                                    onKeyDown={handleTranslateButtonClick}
                                    style={{
                                        ...styles.translateButton,
                                        opacity: loading ? 0.6 : 1,
                                        cursor: loading ? 'not-allowed' : 'pointer'
                                    }}
                                    className={`translate-button ${translateButtonAnimation}`}
                                >
                                    <div style={styles.buttonContent}>
                                        <span style={styles.translateIcon}>✨</span>
                                        Translate
                                    </div>
                                </button>
                            )}
                        </div>

                        <div style={{...styles.panel, ...(isMobile ? styles.panelMobile : {})}} className={`panel ${isAnimating ? 'panel-swap-animation' : ''}`}>
                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                marginBottom: '8px'
                            }}>
                                <h2 style={styles.panelTitle}>Auslan</h2>
                            </div>
                            
                            {/* Grammar pill positioned absolutely in top-right corner */}
                            <div style={{
                                position: 'absolute',
                                top: '16px',
                                right: '16px',
                                zIndex: 10
                            }}>
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
                                <div style={{
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: '12px',
                                    flex: 1
                                }}>
                                    {/* Grammar text display when alwaysShowGrammar is true */}
                                    {alwaysShowGrammar && grammarParsedText && (
                                        <div style={{
                                            padding: '8px 12px',
                                            backgroundColor: 'rgba(0, 0, 0, 0.32)',
                                            border: 'none',
                                            borderRadius: '8px',
                                            fontSize: '18px',
                                            color: '#ffffff',
                                            fontFamily: "Inter, 'SF Pro Display', 'Segoe UI Variable', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
                                            boxShadow: '0 0 0 1px rgba(190, 155, 210, 0.3), 0 0 6px rgba(190, 155, 210, 0.15)'
                                        }}>
                                            <div style={{
                                                fontSize: '16px',
                                                color: 'rgba(255, 255, 255, 0.6)',
                                                marginBottom: '4px',
                                                fontWeight: '500'
                                            }}>
                                                Auslan Grammar:
                                            </div>
                                            "{grammarParsedText.charAt(0).toUpperCase() + grammarParsedText.slice(1)}."
                                        </div>
                                    )}
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