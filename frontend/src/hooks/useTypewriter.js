import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Advanced typewriter hook with multiple features:
 * - Variable speed typing
 * - Pause/resume functionality
 * - Character-by-character or word-by-word typing
 * - Cursor blinking effect
 * - Completion callbacks
 * - Skip animation option
 */
export function useTypewriter(
  text, 
  options = {}
) {
  const {
    speed = 30,
    startDelay = 0,
    cursor = true,
    cursorChar = '|',
    cursorBlinkSpeed = 500,
    mode = 'char', // 'char' or 'word'
    skipAnimation = false,
    onComplete,
    onStart,
    variableSpeed = false, // Vary speed based on punctuation
    preserveWhitespace = true
  } = options;

  const [displayedText, setDisplayedText] = useState("");
  const [isComplete, setIsComplete] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [showCursor, setShowCursor] = useState(cursor);
  const [isPaused, setPaused] = useState(false);
  
  const timeoutRef = useRef(null);
  const cursorIntervalRef = useRef(null);
  const indexRef = useRef(0);
  const startTimeRef = useRef(null);

  // Calculate typing speed based on character context
  const getTypingSpeed = useCallback((char, nextChar) => {
    if (!variableSpeed) return speed;
    
    // Slower for punctuation
    if (/[.!?]/.test(char)) return speed * 3;
    if (/[,;:]/.test(char)) return speed * 2;
    if (char === ' ' && /[.!?]/.test(nextChar)) return speed * 1.5;
    
    // Faster for common characters
    if (/[aeiou]/.test(char.toLowerCase())) return speed * 0.8;
    
    return speed;
  }, [speed, variableSpeed]);

  // Process text into chunks based on mode
  const processText = useCallback((text, mode) => {
    if (!text) return [];
    
    if (mode === 'word') {
      // Split by words but preserve spaces
      const words = text.split(/(\s+)/);
      return words.filter(word => word.length > 0);
    } else {
      // Character mode - split by characters
      return text.split('');
    }
  }, []);

  // Start cursor blinking
  useEffect(() => {
    if (cursor && cursorBlinkSpeed > 0) {
      cursorIntervalRef.current = setInterval(() => {
        setShowCursor(prev => !prev);
      }, cursorBlinkSpeed);
    }
    
    return () => {
      if (cursorIntervalRef.current) {
        clearInterval(cursorIntervalRef.current);
      }
    };
  }, [cursor, cursorBlinkSpeed]);

  // Main typing effect
  useEffect(() => {
    // Reset state when text changes
    setDisplayedText("");
    setIsComplete(false);
    setIsTyping(false);
    setPaused(false);
    indexRef.current = 0;
    startTimeRef.current = null;
    
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    if (!text) return;
    
    // Skip animation if requested
    if (skipAnimation) {
      setDisplayedText(text);
      setIsComplete(true);
      onComplete?.(text);
      return;
    }
    
    const chunks = processText(text, mode);
    if (chunks.length === 0) return;
    
    // Start after delay
    const startTyping = () => {
      setIsTyping(true);
      startTimeRef.current = Date.now();
      onStart?.(text);
      
      const typeNextChunk = () => {
        if (isPaused) {
          // Check again in 100ms if paused
          timeoutRef.current = setTimeout(typeNextChunk, 100);
          return;
        }
        
        const currentIndex = indexRef.current;
        if (currentIndex >= chunks.length) {
          // Typing complete
          setIsTyping(false);
          setIsComplete(true);
          onComplete?.(text);
          return;
        }
        
        const chunk = chunks[currentIndex];
        const nextChunk = chunks[currentIndex + 1];
        
        // Update displayed text
        setDisplayedText(prev => {
          if (mode === 'word') {
            return prev + chunk;
          } else {
            return prev + chunk;
          }
        });
        
        indexRef.current++;
        
        // Calculate delay for next character/word
        const currentSpeed = mode === 'char' 
          ? getTypingSpeed(chunk, nextChunk)
          : speed;
        
        timeoutRef.current = setTimeout(typeNextChunk, currentSpeed);
      };
      
      typeNextChunk();
    };
    
    if (startDelay > 0) {
      timeoutRef.current = setTimeout(startTyping, startDelay);
    } else {
      startTyping();
    }
    
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [text, speed, startDelay, mode, skipAnimation, getTypingSpeed, processText, onComplete, onStart, isPaused]);

  // Control functions
  const pause = useCallback(() => {
    setPaused(true);
  }, []);
  
  const resume = useCallback(() => {
    setPaused(false);
  }, []);
  
  const skip = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setDisplayedText(text);
    setIsComplete(true);
    setIsTyping(false);
    onComplete?.(text);
  }, [text, onComplete]);
  
  const restart = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setDisplayedText("");
    setIsComplete(false);
    setIsTyping(false);
    setPaused(false);
    indexRef.current = 0;
    
    // Restart the effect
    const chunks = processText(text, mode);
    if (chunks.length === 0) return;
    
    setIsTyping(true);
    startTimeRef.current = Date.now();
    onStart?.(text);
    
    const typeNextChunk = () => {
      if (isPaused) {
        timeoutRef.current = setTimeout(typeNextChunk, 100);
        return;
      }
      
      const currentIndex = indexRef.current;
      if (currentIndex >= chunks.length) {
        setIsTyping(false);
        setIsComplete(true);
        onComplete?.(text);
        return;
      }
      
      const chunk = chunks[currentIndex];
      const nextChunk = chunks[currentIndex + 1];
      
      setDisplayedText(prev => prev + chunk);
      indexRef.current++;
      
      const currentSpeed = mode === 'char' 
        ? getTypingSpeed(chunk, nextChunk)
        : speed;
      
      timeoutRef.current = setTimeout(typeNextChunk, currentSpeed);
    };
    
    typeNextChunk();
  }, [text, mode, speed, getTypingSpeed, processText, onStart, onComplete, isPaused]);

  // Format display text with cursor
  const displayText = cursor && showCursor && !isComplete
    ? displayedText + cursorChar
    : displayedText;

  // Calculate progress
  const progress = text ? (displayedText.length / text.length) * 100 : 0;
  
  // Calculate typing speed (characters per minute)
  const typingSpeed = startTimeRef.current && displayedText.length > 0
    ? Math.round((displayedText.length / ((Date.now() - startTimeRef.current) / 1000)) * 60)
    : 0;

  return {
    displayedText: displayText,
    isComplete,
    isTyping,
    isPaused,
    progress,
    typingSpeed,
    controls: {
      pause,
      resume,
      skip,
      restart
    }
  };
}

/**
 * Simpler typewriter hook for basic use cases
 */
export function useSimpleTypewriter(text, speed = 30) {
  const { displayedText } = useTypewriter(text, { speed, cursor: false });
  return displayedText;
}

/**
 * Hook for typing multiple texts in sequence
 */
export function useSequentialTypewriter(texts, options = {}) {
  const {
    speed = 30,
    pauseBetween = 1000,
    loop = false,
    cursor = true
  } = options;

  const [currentIndex, setCurrentIndex] = useState(0);
  const [isSequenceComplete, setIsSequenceComplete] = useState(false);
  
  const currentText = texts[currentIndex] || '';
  
  const { displayedText, isComplete, controls } = useTypewriter(currentText, {
    ...options,
    speed,
    cursor,
    onComplete: () => {
      setTimeout(() => {
        const nextIndex = currentIndex + 1;
        if (nextIndex >= texts.length) {
          if (loop) {
            setCurrentIndex(0);
          } else {
            setIsSequenceComplete(true);
          }
        } else {
          setCurrentIndex(nextIndex);
        }
      }, pauseBetween);
    }
  });

  const restartSequence = useCallback(() => {
    setCurrentIndex(0);
    setIsSequenceComplete(false);
    controls.restart();
  }, [controls]);

  return {
    displayedText,
    currentIndex,
    isSequenceComplete,
    currentText,
    controls: {
      ...controls,
      restartSequence
    }
  };
}
