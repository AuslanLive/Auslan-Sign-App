import React, { useEffect, useRef, useState } from "react";

const API_BASE_URL = "/api"


// Import necessary MediaPipe scripts
const cameraUtilsUrl =
    "https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js";
const controlUtilsUrl =
    "https://cdn.jsdelivr.net/npm/@mediapipe/control_utils/control_utils.js";   
const drawingUtilsUrl =
    "https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js";
const holisticUrl =
    "https://cdn.jsdelivr.net/npm/@mediapipe/holistic/holistic.js";

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
    const holisticRef = useRef(null); // Reference to the holistic object
    const [isCameraOn, setIsCameraOn] = useState(false); // State to track if the camera is on
    const [error, setError] = useState(null); // State to handle errors
    const [isTransmitting, setIsTransmitting] = useState(true); // State to control keypoint transmission
    const [isPaused, setIsPaused] = useState(false); // State to control pause/resume
    const [hasHandsDetected, setHasHandsDetected] = useState(false); // track the hands

    useEffect(() => {
        const loadMediaPipe = async () => {
            await loadScript(cameraUtilsUrl);
            await loadScript(controlUtilsUrl);
            await loadScript(drawingUtilsUrl);
            await loadScript(holisticUrl);

            const holistic = new window.Holistic({
                locateFile: (file) =>
                    `https://cdn.jsdelivr.net/npm/@mediapipe/holistic/${file}`,
            });

            holistic.setOptions({
                modelComplexity: 1,
                smoothLandmarks: true,
                enableSegmentation: true,
                smoothSegmentation: true,
                minDetectionConfidence: 0.5,
                minTrackingConfidence: 0.5,
            });

            holisticRef.current = holistic;
        };

        loadMediaPipe();

        return () => {
            stopCamera(); // Cleanup the camera on component unmount
        };
    }, []);

    const startCamera = async () => {
        try {
            const videoElement = videoRef.current;
            const canvasElement = canvasRef.current;
            const canvasCtx = canvasElement.getContext("2d");

            const stream = await navigator.mediaDevices.getUserMedia({
                video: true,
            });
            videoElement.srcObject = stream;

            if (!holisticRef.current) {
                console.error("Holistic model is not initialized");
                return;
            }

            const holistic = holisticRef.current;

            holistic.onResults((results) => {
                // Clear the canvas and draw the video and landmarks
                canvasCtx.save();
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

                // Hide face/pose overlays for cleaner UI; only draw hands if desired
                if (results.leftHandLandmarks) {
                    window.drawConnectors(
                        canvasCtx,
                        results.leftHandLandmarks,
                        window.HAND_CONNECTIONS,
                        {
                            color: "#CC0000",
                            lineWidth: 5,
                        }
                    );
                    window.drawLandmarks(canvasCtx, results.leftHandLandmarks, {
                        color: "#00FF00",
                        lineWidth: 2,
                    });
                }
                if (results.rightHandLandmarks) {
                    window.drawConnectors(
                        canvasCtx,
                        results.rightHandLandmarks,
                        window.HAND_CONNECTIONS,
                        {
                            color: "#00CC00",
                            lineWidth: 5,
                        }
                    );
                    window.drawLandmarks(
                        canvasCtx,
                        results.rightHandLandmarks,
                        { color: "#FF0000", lineWidth: 2 }
                    );
                }
                canvasCtx.restore();

                // Buffer frames when transmitting and not paused (for batch send)
                if (isTransmitting && !isPaused) {
                    // Prepare keypoints (pose ignored, only hands)
                    const keypoints = [
                        null,
                        results.leftHandLandmarks
                            ? results.leftHandLandmarks.map((lm) => ({ ...lm, visibility: 0.0 }))
                            : null,
                        results.rightHandLandmarks
                            ? results.rightHandLandmarks.map((lm) => ({ ...lm, visibility: 0.0 }))
                            : null,
                    ];

                    // Only buffer if at least one hand is detected
                    const lCount = keypoints[1] ? keypoints[1].length : 0;
                    const rCount = keypoints[2] ? keypoints[2].length : 0;
                    const hasHands = lCount > 0 || rCount > 0;

                    // Update hand detection status
                    setHasHandsDetected(hasHands);

                    if (hasHands) {
                        // Debug: show counts in console
                        if ((lCount + rCount) % 21 === 0) {
                            console.log(`Frame keypoints -> L:${lCount} R:${rCount}`);
                        }

                        // Save to a rolling buffer for batch upload
                        frameBuffer.current.push({ keypoints });
                        if (frameBuffer.current.length > 300) frameBuffer.current.shift();
                    }
                }
            });

            if (!cameraRef.current) {
                const camera = new window.Camera(videoElement, {
                    onFrame: async () => {
                        await holistic.send({ image: videoElement });
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

    // Recording buffer for batch mode
    const frameBuffer = useRef([]);

    const stopTransmission = () => {
        setIsTransmitting(false);
    };

    const startTransmission = () => {
        frameBuffer.current = [];
        setIsTransmitting(true);
        setIsPaused(false);
    };

    const pauseTransmission = () => {
        setIsPaused(true);
    };

    const resumeTransmission = () => {
        setIsPaused(false);
    };

    const uploadRecording = async () => {
        try {
            const frames = frameBuffer.current.map((f) => f);
            console.log(`Uploading recording: ${frames.length} frames`);
            const res = await fetch(API_BASE_URL + "/recording", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ frames }),
            });
            const data = await res.json();
            console.log("WORD:", data?.top_1?.label || "-");
            console.log("Top-5:", data?.top_5 || []);
            // Clear buffer after successful upload to start fresh window
            frameBuffer.current = [];
        } catch (e) {
            console.error("Recording upload failed", e);
        }
    };

    // Auto-send recordings periodically while transmitting and not paused
    useEffect(() => {
        let intervalId;
        if (isCameraOn && isTransmitting && !isPaused) {
            intervalId = setInterval(() => {
                // Send only if we have a reasonable number of frames
                if (frameBuffer.current.length >= 24) {
                    uploadRecording();
                }
            }, 2000); // every 2s
        }
        return () => {
            if (intervalId) clearInterval(intervalId);
        };
    }, [isCameraOn, isTransmitting, isPaused]);

    React.useImperativeHandle(ref, () => ({
        stopCamera,
        stopTransmission,
        startTransmission,
        pauseTransmission,
        resumeTransmission,
        hasHandsDetected,
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
        <div className='container' style={styles.container}>
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
                        width='1280'
                        height='720'
                        style={{
                            ...styles.canvas,
                            display: isCameraOn ? 'block' : 'none'
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
            {isCameraOn && (
                <div style={{ position: 'absolute', bottom: 20, right: 20, display: 'flex', gap: 12 }}>
                    <button onClick={startTransmission} style={styles.button}>Start Recording</button>
                    <button onClick={stopTransmission} style={styles.button}>Stop Recording</button>
                    <button onClick={uploadRecording} style={styles.button}>Send Recording</button>
                </div>
            )}
        </div>
    );
});

const styles = {
    container: {
        position: "relative",
        width: "100%",
        height: "100%",
        padding: "1px",
        boxSizing: "border-box",
        outline: "2px solid #007bff",
        borderRadius: "8px",
        backgroundColor: "#333333",
    },
    canvas: {
        width: "100%",
        height: "100%",
        objectFit: "cover",
        borderRadius: "10px",
        boxSizing: "border-box",
        transform: "scaleX(-1)",
    },
    button: {
        position: "absolute",
        bottom: "20px",
        left: "20px",
        padding: "12px 24px",
        fontSize: "14px",
        fontWeight: "600",
        background: "linear-gradient(135deg, #a855f7 0%, #3b82f6 100%)",
        color: "#ffffff",
        border: "none",
        borderRadius: "25px",
        cursor: "pointer",
        zIndex: 11,
        transition: "all 0.3s ease",
        boxShadow: "0 4px 15px rgba(0, 0, 0, 0.4)",
        backdropFilter: "blur(10px)",
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        transform: "translateY(0) scale(1)",
    },
    placeholder: {
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        background: "#0D0E1A",
        backdropFilter: "blur(10px)",
        color: "rgba(255, 255, 255, 0.5)",
        borderRadius: "10px",
        textAlign: "center",
        padding: "20px",
        boxSizing: "border-box",
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
