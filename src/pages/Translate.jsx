import React, { useState, useRef, useEffect } from "react";
import VideoInput from "../components/VideoInput";
import { storage, ref, getDownloadURL } from "../firebase";
import namesData from '../namesdatapose.json';
import 'react-toastify/dist/ReactToastify.css';
import { Toaster, toast } from 'react-hot-toast';
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

    // Function to swap between modes
    const handleSwap = () => {
        setTranslatedText(""); // Clear the translated text on swap

        if (mode === "videoToText" && videoInputRef.current) {
            videoInputRef.current.stopCamera(); // Stop the camera when switching to textToVideo
        }

        setMode((prevMode) =>
            prevMode === "videoToText" ? "textToVideo" : "videoToText"
        );
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

    // new code - only trigger when mode is videoToText
    useEffect(() => {
        let interval;
        if (mode === "videoToText") {
            interval = setInterval(function () {
                get_sign_trans();
                getGemFlag();
            }, 1000);
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [mode]);


    
    const checkTextAgainstJson = (text) => {
        // Split the text into words, encode, and convert to lowercase
        const words = text.split(/\s+/).map(word => encodeURIComponent(word.toLowerCase()));
        
        // Convert namesData entries to lowercase for case-insensitive comparison
        const existingWords = new Set(namesData.map(item => item.toLowerCase()));
        
        // Filter out words that do not exist in the existing words set
        const missingWords = words.filter(word => !existingWords.has(word));
    
        if (missingWords.length > 0) {
            console.log(`The following words do not exist: ${missingWords}`);
            toast.error(`The following words do not exist: ${missingWords.join(', ')}`);
        }
    };

    // Function to convert text to video

    const handleTextToVideo = async () => {
        const fixedSourceText = sourceText.trim();
        console.log("Sending Source Text:", fixedSourceText);
        checkTextAgainstJson(fixedSourceText);
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
            const parsedVideoName = translatedText || fixedSourceText;
            const videoPath = firebaseURL + parsedVideoName + fileType;

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
                {mode === "videoToText" ? (
                    <>
                        <div style={styles.panel}>
                            <h2 style={styles.panelTitle}>Auslan</h2>
                            <div style={styles.videoInputContainer}>
                                <VideoInput />
                            </div>
                        </div>

                        <div style={styles.buttons}>
                            <button onClick={handleSwap} style={styles.swapButton} className="swap-button">
                                <div style={styles.buttonContent}>
                                    <span style={styles.swapIcon}>⇄</span>
                                    Swap
                                </div>
                            </button>
                        </div>

                        <div style={styles.panel}>
                            <h2 style={styles.panelTitle}>Text</h2>
                            {loading ? (
                                <div style={styles.loadingPlaceholder}>
                                    <div style={styles.spinner}></div>
                                    <p style={styles.loadingText}>Processing sign language...</p>
                                </div>
                            ) : (
                                <textarea
                                    placeholder='Translation will appear here...'
                                    value={translatedText}
                                    readOnly
                                    style={styles.textarea}
                                />
                            )}
                        </div>
                    </>
                ) : (
                    <>
                        <div style={styles.panel}>
                            <h2 style={styles.panelTitle}>Text</h2>
                            <textarea
                                placeholder='Enter text to convert to sign language...'
                                value={sourceText}
                                onChange={(e) => setSourceText(e.target.value)}
                                style={styles.textarea}
                            />
                        </div>

                        <div style={styles.buttons}>
                            <button onClick={handleSwap} style={styles.swapButton} className="swap-button">
                                <div style={styles.buttonContent}>
                                    <span style={styles.swapIcon}>⇄</span>
                                    Swap
                                </div>
                            </button>
                            <button
                                onClick={handleTextToVideo}
                                style={styles.translateButton}
                                className="translate-button"
                            >
                                <div style={styles.buttonContent}>
                                    <span style={styles.translateIcon}>✨</span>
                                    Translate
                                </div>
                            </button>
                        </div>

                        <div style={styles.panel}>
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
                                <div style={styles.videoPlaceholder}>
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
        </div>
    );
};

export default TranslateApp;