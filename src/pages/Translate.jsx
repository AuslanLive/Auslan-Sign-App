import React, { useState, useRef, useEffect } from "react";
import VideoInput from "../components/VideoInput";
import ToasterWithMax from "../components/ToasterWithMax";
import GrammarPill from "../components/GrammarPill";
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

    // Function to handle camera start notification
    const handleCameraStart = () => {
        setIsPolling(true);
        if (videoInputRef.current) {
            videoInputRef.current.startTransmission();
        }
    };

    // Function to swap between modes
    const handleSwap = () => {
        if (isAnimating) return; // Prevent multiple swaps during animation
        
        setIsAnimating(true);
        setSwapButtonRepositioning(true);
        setTranslatedText(""); // Clear the translated text on swap
        setGrammarParsedText(""); // Clear grammar text on swap

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
    useEffect(() => {
        let interval;
        if (mode === "videoToText" && isPolling) {
            interval = setInterval(function () {
                get_sign_trans();
                getGemFlag();
            }, 1000);
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [mode, isPolling]);

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
    const handleClearText = () => {
        setClearButtonAnimation('clear-button-exit');
        setTimeout(() => {
            setTranslatedText("");
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
                            <div style={styles.videoInputContainer}>
                                <VideoInput ref={videoInputRef} onCameraStart={handleCameraStart} isMobile={isMobile} />
                            </div>
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