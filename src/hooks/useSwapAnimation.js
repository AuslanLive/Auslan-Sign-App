import { useState, useCallback } from 'react';

export const useSwapAnimation = (
  mode,
  setMode,
  setTranslatedText,
  setShowTranslateButton,
  videoInputRef
) => {
  const [animationState, setAnimationState] = useState({
    isAnimating: false,
    swapButtonRepositioning: false,
    translateButtonAnimation: '',
    showTranslateButton: mode === "textToVideo"
  });

  const handleSwap = useCallback(() => {
    if (animationState.isAnimating) return;
    
    setAnimationState(prev => ({
      ...prev,
      isAnimating: true,
      swapButtonRepositioning: true
    }));
    
    setTranslatedText("");

    // Handle translate button exit animation
    if (mode === "textToVideo") {
      setAnimationState(prev => ({
        ...prev,
        translateButtonAnimation: 'translate-button-exit'
      }));
      setTimeout(() => {
        setAnimationState(prev => ({
          ...prev,
          showTranslateButton: false
        }));
      }, 400);
    }

    if (mode === "videoToText" && videoInputRef.current) {
      videoInputRef.current.stopCamera();
    }

    setTimeout(() => {
      const newMode = mode === "videoToText" ? "textToVideo" : "videoToText";
      setMode(newMode);
      
      if (mode === "videoToText") {
        setAnimationState(prev => ({
          ...prev,
          showTranslateButton: true,
          translateButtonAnimation: 'translate-button-enter'
        }));
      }
      
      setTimeout(() => {
        setAnimationState(prev => ({
          ...prev,
          isAnimating: false,
          swapButtonRepositioning: false,
          translateButtonAnimation: ''
        }));
      }, 400);
    }, 400);
  }, [animationState.isAnimating, mode, setMode, setTranslatedText, videoInputRef]);

  return { animationState, handleSwap };
};
