import { useState, useEffect } from 'react';

/**
 * Custom hook to simulate a typewriter effect.
 * Given a `text` string, it returns `displayedText` which
 * gradually reveals one more character at a time at the specified speed (ms).
 */
export function useTypewriter(text, speed = 30) {
  const [displayedText, setDisplayedText] = useState("");

  useEffect(() => {
    setDisplayedText(""); // clear whenever text changes
    if (!text) return;

    let index = 0;
    const interval = setInterval(() => {
      setDisplayedText((prev) => prev + text.charAt(index));
      index += 1;
      if (index >= text.length) {
        clearInterval(interval);
      }
    }, speed);

    return () => clearInterval(interval);
  }, [text, speed]);

  return displayedText;
}
