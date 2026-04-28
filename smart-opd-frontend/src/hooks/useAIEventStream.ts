import { useState, useEffect } from 'react';

export function useAIEventStream(triggerId: number | null, message: string | null, delay: number = 1500) {
  const [displayMessage, setDisplayMessage] = useState<string | null>(null);
  const [isThinking, setIsThinking] = useState(false);

  useEffect(() => {
    if (!message || !triggerId) return;

    setIsThinking(true);
    setDisplayMessage(null);

    const timer = setTimeout(() => {
      setDisplayMessage(message);
      setIsThinking(false);
    }, delay);

    return () => clearTimeout(timer);
  }, [triggerId, message, delay]);

  return { displayMessage, isThinking };
}