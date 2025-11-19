import { useEffect, useCallback } from 'react';

const API_BASE_URL = "/api";

export const useVideoToTextPolling = (mode, isPolling, setTranslatedText, setLoading) => {
  const get_sign_trans = useCallback(async () => {
    try {
      const response = await fetch(API_BASE_URL + "/get_sign_to_text", {
        method: "GET",
      });

      const data = await response.json();
      console.log("Full response:", data);

      const translatedText = data.translation;
      setTranslatedText(translatedText);
    } catch (error) {
      console.error("Error:", error);
      setTranslatedText(`Error: ${error.message}. Please check the API and input.`);
    }
  }, [setTranslatedText]);

  const getGemFlag = useCallback(async () => {
    try {
      const response = await fetch(API_BASE_URL + "/getGemFlag", {
        method: "GET",
      });

      const data = await response.json();
      console.log("GeminiFlag:", data);

      const isInGemini = data.flag;
      console.log("GeminiFlag:", isInGemini);
      setLoading(isInGemini);
    } catch (error) {
      console.error("Error:", error);
      setTranslatedText(`Error: ${error.message}. Please check the API and input.`);
    }
  }, [setLoading, setTranslatedText]);

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
  }, [mode, isPolling, get_sign_trans, getGemFlag]);
};
