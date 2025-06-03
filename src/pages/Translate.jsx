import React, { useState, useRef, useEffect } from "react";
import VideoInput from "../components/VideoInput";
import { storage, ref, getDownloadURL } from "../firebase";
import { data } from "autoprefixer";
import namesData from '../namesdatapose.json';
import 'react-toastify/dist/ReactToastify.css';
import { Toaster, toast } from 'react-hot-toast';


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
        <div style={styles.container}>
            <Toaster position="top-right" />
            {mode === "videoToText" ? (
                <>
                    <div style={styles.panel}>
                        <h2>Sign</h2>
                        <VideoInput />
                    </div>

                    <div style={styles.buttons}>
                        <button onClick={handleSwap} style={styles.button}>
                            Swap
                        </button>
                    </div>

                    <div style={styles.panel}>
                        <h2>Text</h2>
                        {loading ? ( // Display loading animation if loading is true
                            <div style={styles.loadingPlaceholder}>
                                {/* Loading... */}
                                <div className='spinner'></div>
                            </div>
                        ) : (
                            <textarea
                                placeholder='Translation will appear here'
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
                        <h2>Text</h2>
                        <textarea
                            placeholder='Enter text to convert to sign language'
                            value={sourceText}
                            onChange={(e) => setSourceText(e.target.value)}
                            style={styles.textarea}
                        />
                    </div>

                    <div style={styles.buttons}>
                        <button onClick={handleSwap} style={styles.button}>
                            Swap
                        </button>
                        <button
                            onClick={handleTextToVideo}
                            style={styles.button}
                        >
                            Translate
                        </button>
                    </div>

                    <div style={styles.panel}>
                        <h2>Sign Video</h2>
                        {loading ? ( // Display loading animation if loading is true
                            <div style={styles.loadingPlaceholder}>
                                {/* Loading... */}
                                <div className='spinner'></div>
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
                                Please type in a sentence and click translate!
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
};

const styles = {
    container: {
        display: "flex",
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-around",
        gap: "20px",
        width: "100%",
        margin: "0 auto",
    },
    panel: {
        display: "flex",
        flex: "1",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        width: "600px",
        height: "600px",
        boxSizing: "border-box",
        padding: "20px",
    },
    textarea: {
        width: "530px",
        height: "540px",
        padding: "10px",
        fontSize: "20px",
        resize: "none",
        boxSizing: "border-box",
        backgroundColor: "#333333",
        color: "#ffffff",
        border: "1px solid #555555",
        borderRadius: "8px",
    },
    buttons: {
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        color: "white",
        gap: "10px",
    },
    button: {
        padding: "10px 20px",
        fontSize: "20px",
        backgroundColor: "#007bff", // Existing button background color
        color: "#ffffff", // White text color
        cursor: "pointer",
        border: "none", // Optional: removes default border for a cleaner look
        borderRadius: "5px", // Optional: adds rounded corners
    },
    videoContainer: {
        width: "100%",
        maxWidth: "800px",
        height: "auto",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        overflow: "hidden",
        borderRadius: "8px",
        color: "#ffffff",
        backgroundColor: "#333333",
    },
    video: {
        width: "100%",
        height: "100%",
        objectFit: "contain",
    },
    videoPlaceholder: {
        width: "530px", // Full width placeholder
        height: "540px", // Set a height for the placeholder
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        backgroundColor: "#333333", // A background color for the placeholder
        color: "darkgray",
        borderRadius: "8px",
    },
    loadingPlaceholder: {
        // New loading animation style
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        width: "530px",
        height: "540px",
        fontSize: "20px",
        color: "white",
        backgroundColor: "#333333",
        borderRadius: "8px",
        border: "1px solid #555555",
    },
};

export default TranslateApp;