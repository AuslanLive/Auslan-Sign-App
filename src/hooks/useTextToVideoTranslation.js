import { useCallback } from 'react';
import { toast } from 'react-hot-toast';
import { ref, getDownloadURL } from '../firebase';
import { cleanInputText } from '../lib/cleanInputText';
import wordList from '../fullWordList.json';

const API_BASE_URL = "/api";

export const useTextToVideoTranslation = (
  storage,
  setLoading,
  setTranslatedText,
  setGrammarParsedText,
  setAnimatedSignVideo
) => {
  const checkTextAgainstWordListJson = useCallback((text) => {
    const words = text.split(/\s+/).map(word => encodeURIComponent(word.toLowerCase()));
    const existingWords = new Set(wordList.map(item => item.toLowerCase()));
    const missingWords = words.filter(word => !existingWords.has(word));
    
    console.log(missingWords);
    if (missingWords.length > 0) {
      console.log(`The following words do not exist: ${missingWords}`);
      toast.error(`The following words do not exist: ${missingWords.join(', ')}`);
    }
  }, []);

  const translateText = useCallback(async (sourceText) => {
    const cleanedText = cleanInputText(sourceText);

    console.log("Sending Source Text:", cleanedText);
    if (cleanedText === null || cleanedText === undefined || cleanedText.trim().length === 0) {
      console.log(`No text to translate: ${cleanedText}`);
      toast.error(`No text to translate`);
      return;
    }

    checkTextAgainstWordListJson(cleanedText);
    setLoading(true);

    try {
      const response = await fetch(API_BASE_URL + "/t2s", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ t2s_input: cleanedText }),
      });

      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);

      const data = await response.json();
      console.log("Full response:", data);

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

      // Generate the Firebase video path using the original array format
      const firebaseURL = "gs://auslan-194e5.appspot.com/output_videos/";
      const fileType = ".mp4";

      let parsedVideoName;
      if (Array.isArray(translatedText)) {
        // Use underscore format to match the Python backend
        parsedVideoName = translatedText.join(' ');
      } else {
        parsedVideoName = translatedText;
      }

      const videoPath = firebaseURL + parsedVideoName + fileType;

      console.log("Video Path:", videoPath);
      console.log("Parsed Video Name:", parsedVideoName);

      const videoRef = ref(storage, videoPath);
      const videoUrl = await getDownloadURL(videoRef);
      setAnimatedSignVideo(videoUrl);
    } catch (error) {
      console.error("Error:", error);
      setTranslatedText(`Error: ${error.message}. Please check the API and input.`);
      setGrammarParsedText("");
    } finally {
      setLoading(false);
    }
  }, [storage, setLoading, setTranslatedText, setGrammarParsedText, setAnimatedSignVideo, checkTextAgainstWordListJson]);

  return { translateText };
};
