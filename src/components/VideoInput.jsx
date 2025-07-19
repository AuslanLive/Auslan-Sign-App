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

                // Draw Pose and Hands Landmarks
                if (results.poseLandmarks) {
                    window.drawConnectors(
                        canvasCtx,
                        results.poseLandmarks,
                        window.POSE_CONNECTIONS,
                        {
                            color: "#00FF00",
                            lineWidth: 4,
                        }
                    );
                    window.drawLandmarks(canvasCtx, results.poseLandmarks, {
                        color: "#FF0000",
                        lineWidth: 2,
                    });
                }
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

                // Prepare keypoints to send to backend
                const keypoints = [
                    results.poseLandmarks,
                    results.leftHandLandmarks
                        ? results.leftHandLandmarks.map((landmark) => ({
                              ...landmark,
                              visibility: 0.0,
                          }))
                        : null,
                    results.rightHandLandmarks
                        ? results.rightHandLandmarks.map((landmark) => ({
                              ...landmark,
                              visibility: 0.0,
                          }))
                        : null,
                ];

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
                        console.log("Data saved successfully:", data);
                    })
                    .catch((error) => {
                        console.error("Error saving data:", error);
                    });
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

    React.useImperativeHandle(ref, () => ({
        stopCamera,
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
            <button onClick={toggleCamera} style={styles.button} className="camera-button">
                {isCameraOn ? "Turn Camera Off" : "Turn Camera On"}
            </button>
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
        background: "rgba(10, 10, 20, 0.6)",
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
