import React, { useEffect, useRef, useState } from "react";

const API_BASE_URL = "/api"


// Import necessary MediaPipe scripts
const cameraUtilsUrl =
    "https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js";
const controlUtilsUrl =
    "https://cdn.jsdelivr.net/npm/@mediapipe/control_utils/control_utils.js";   
const drawingUtilsUrl =
    "https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js";
const handsUrl =
    "https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js";

// Load external MediaPipe scripts dynamically
const loadScript = (url) => {
    return new Promise((resolve) => {
        const script = document.createElement("script");
        script.src = url;
        script.crossOrigin = "anonymous";
        script.onload = () => resolve();
        document.head.appendChild(script);
    });
};

const VideoInput = React.forwardRef((props, ref) => {
    // Use React.forwardRef
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const cameraRef = useRef(null); // Reference to the camera object
    const handsRef = useRef(null); // Reference to the hands object
    const [isCameraOn, setIsCameraOn] = useState(false); // State to track if the camera is on
    const [error, setError] = useState(null); // State to handle errors
    const [isTransmitting, setIsTransmitting] = useState(true); // State to control keypoint transmission

    useEffect(() => {
        const loadMediaPipe = async () => {
            await loadScript(cameraUtilsUrl);
            await loadScript(controlUtilsUrl);
            await loadScript(drawingUtilsUrl);
            await loadScript(handsUrl);

            // Initialize Hands solution
            const hands = new window.Hands({
                locateFile: (file) =>
                    `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
            });

            hands.setOptions({
                maxNumHands: 2,  // Track both hands
                modelComplexity: 1,
                minDetectionConfidence: 0.5,
                minTrackingConfidence: 0.5,
            });

            handsRef.current = hands;
        };

        loadMediaPipe();

        return () => {
            stopCamera(); // Cleanup the camera on component unmount
        };
    }, []);
    
    function resizeCanvasToDisplaySize(canvas) {
        const width = canvas.clientWidth;
        const height = canvas.clientHeight;
        if (canvas.width !== width || canvas.height !== height) {
            canvas.width = width;
            canvas.height = height;
        }
    }

    const startCamera = async () => {
        try {
            const videoElement = videoRef.current;
            const canvasElement = canvasRef.current;
            const canvasCtx = canvasElement.getContext("2d");

            const stream = await navigator.mediaDevices.getUserMedia({
                video: true,
            });
            videoElement.srcObject = stream;

            if (!handsRef.current) {
                console.error("Hands model is not initialized");
                return;
            }

            const hands = handsRef.current;

            // Updated to handle Hands results 
            hands.onResults((results) => {
                // Clear the canvas and draw the video and landmarks
                canvasCtx.save();
                resizeCanvasToDisplaySize(canvasElement);

                canvasCtx.clearRect(
                    0,
                    0,
                    canvasElement.width,
                    canvasElement.height
                );
                canvasCtx.drawImage(
                    results.image,
                    0,
                    0,
                    canvasElement.width,
                    canvasElement.height
                );

                // Draw Hand Landmarks
                if (results.multiHandLandmarks) {
                    for (let i = 0; i < results.multiHandLandmarks.length; i++) {
                        const landmarks = results.multiHandLandmarks[i];
                        const handedness = results.multiHandedness[i].label; // "Left" or "Right"
                        
                        // Different colors for left and right hands
                        const color = handedness === "Left" ? "#00FF00" : "#FF0000";
                        const connectionColor = handedness === "Left" ? "#00CC00" : "#CC0000";
                        
                        window.drawConnectors(
                            canvasCtx,
                            landmarks,
                            window.HAND_CONNECTIONS,
                            {
                                color: connectionColor,
                                lineWidth: 5,
                            }
                        );
                        window.drawLandmarks(canvasCtx, landmarks, {
                            color: color,
                            lineWidth: 2,
                        });
                    }
                }
                canvasCtx.restore();

                // Only send keypoints if transmission is enabled
                if (isTransmitting) {
                    // Extract left and right hands from results
                    let leftHand = null;
                    let rightHand = null;
                    
                    if (results.multiHandLandmarks && results.multiHandedness) {
                        for (let i = 0; i < results.multiHandLandmarks.length; i++) {
                            const handedness = results.multiHandedness[i].label;
                            const landmarks = results.multiHandLandmarks[i];
                            
                            if (handedness === "Left") {
                                leftHand = landmarks;
                            } else if (handedness === "Right") {
                                rightHand = landmarks;
                            }
                        }
                    }
                    
                    // Prepare keypoints for honors model (hands only)
                    const keypoints = {
                        leftHand: leftHand,
                        rightHand: rightHand
                    };

                    // Send keypoints data to backend
                    fetch(API_BASE_URL + "/keypoints", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({ keypoints }), // Convert data to JSON
                    })
                        .then((response) => response.json())
                        .then((data) => {
                            // console.log("Hand keypoints sent successfully:", data);
                        })
                        .catch((error) => {
                            console.error("Error saving data:", error);
                        });
                }
            });

            if (!cameraRef.current) {
                const camera = new window.Camera(videoElement, {
                    onFrame: async () => {
                        await hands.send({ image: videoElement });
                    },
                    width: 1280,
                    height: 720,
                });
                cameraRef.current = camera;
            }

            cameraRef.current.start();
            setIsCameraOn(true);
            
            // Notify parent that camera started (to resume polling)
            if (props.onCameraStart) {
                props.onCameraStart();
            }
        } catch (err) {
            handleCameraError(err);
        }
    };

    const stopCamera = () => {
        if (videoRef.current && videoRef.current.srcObject) {
            let stream = videoRef.current.srcObject;
            let tracks = stream.getTracks();

            tracks.forEach((track) => track.stop()); // Stop all tracks to turn off the camera
            setIsCameraOn(false);

            // Clear the canvas
            const canvasElement = canvasRef.current;
            const canvasCtx = canvasElement.getContext("2d");
            canvasCtx.clearRect(
                0,
                0,
                canvasElement.width,
                canvasElement.height
            );

            videoRef.current.srcObject = null;
        }
    };

    const stopTransmission = () => {
        setIsTransmitting(false);
    };

    const startTransmission = () => {
        setIsTransmitting(true);
    };

    React.useImperativeHandle(ref, () => ({
        stopCamera,
        stopTransmission,
        startTransmission,
    }));

    const toggleCamera = () => {
        if (isCameraOn) {
            stopCamera();
        } else {
            startCamera();
        }
    };

    const handleCameraError = (err) => {
        if (err.name === "NotAllowedError") {
            setError(
                "Camera access was denied. Please allow camera permissions in your browser."
            );
        } else if (err.name === "NotFoundError") {
            setError(
                "No camera found. Please connect a camera to use this feature."
            );
        } else {
            setError(`Error accessing camera: ${err.message}`);
        }
    };

    return (
        <div className='container' style={styles.placeholder}>
            {error ? (
                <div style={{ color: "red" }}>{error}</div>
            ) : (
                <>
                    <video
                        ref={videoRef}
                        className='input_video'
                        style={{ display: "none" }}
                    ></video>
                    {!isCameraOn && (
                        <div style={styles.placeholder}>
                            <div style={styles.placeholderIcon}>📹</div>
                            <p style={styles.placeholderText}>
                                Click "Turn Camera On" to start sign language detection
                            </p>
                        </div>
                    )}
                    <canvas
                        ref={canvasRef}
                        className='output_canvas'
                        style={{
                            ...styles.canvas,
                            display: isCameraOn ? 'block' : 'none', 
                            backgroundColor: "#333333",
                        }}
                    />
                </>
            )}

            <button 
                onClick={toggleCamera} 
                style={{
                    ...styles.button,
                    background: isCameraOn 
                        ? "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)" 
                        : "linear-gradient(135deg, #a855f7 0%, #3b82f6 100%)"
                }} 
                className={isCameraOn ? "camera-button-off" : "camera-button"}
            >
                {isCameraOn ? "Turn Camera Off" : "Turn Camera On"}
            </button>
        </div>
    );
});

const styles = {
    container: {
        position: "relative",
        display: "flex",
        flex: 1,
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        width: "100%",
        height: "100%",
        minHeight: 0,
        padding: "1px",
        borderRadius: "16px",
        
    },
    canvas: {
        position: "relative", 
        flex: 1,
        minHeight: 0,
        width: "100%",
        objectFit: "cover",
        borderRadius: "16px",
        boxSizing: "border-box",
        transform: "scaleX(-1)",
    },
    button: {
        marginTop: "5px",
        marginBottom: "10px",
        padding: "12px 24px",
        fontSize: "14px",
        fontWeight: "600",
        background: "linear-gradient(135deg, #a855f7 0%, #3b82f6 100%)",
        color: "#ffffff",
        border: "none",
        borderRadius: "25px",
        cursor: "pointer",
        zIndex: 2,
        boxShadow: "0 4px 15px rgba(0,0,0,0.4)",
        backdropFilter: "blur(10px)",
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        transition: "all 0.3s ease",
    },
    placeholder: {
        position: "relative", 
        flex: 1,
        minHeight: 0,
        width: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        background: "transparent",
        backdropFilter: "blur(10px)",
        color: "rgba(255, 255, 255, 0.7)",
        textAlign: "center",
        padding: "20px",
        boxSizing: "border-box",
        borderRadius: "16px",
    },
    placeholderIcon: {
        fontSize: "32px",
        marginBottom: "12px",
        opacity: "0.6",
    },
    placeholderText: {
        fontSize: "14px",
        lineHeight: "1.4",
        margin: "0",
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        maxWidth: "280px",
    },
};

export default VideoInput;
