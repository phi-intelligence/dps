"use client";

import { useEffect, useState } from "react";

/** Minimum time to show the loader (avoids flash on fast loads). */
const MIN_LOAD_TIME_MS = 600;

/** Maximum wait before we give up and show the page (avoids stuck loader). */
const MAX_WAIT_MS = 8000;

/**
 * Returns true when the page is ready to display.
 * Waits for: document complete, fonts loaded, and minimum display time.
 * Used to gate the full-page loading screen so animations fire on scroll, not during load.
 */
export function usePageReady(): boolean {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const start = Date.now();

    const checkReady = () => {
      const elapsed = Date.now() - start;
      const minElapsed = elapsed >= MIN_LOAD_TIME_MS;
      const maxElapsed = elapsed >= MAX_WAIT_MS;

      if (maxElapsed) {
        setReady(true);
        return;
      }

      const docComplete = typeof document !== "undefined" && document.readyState === "complete";
      const fontsReady =
        typeof document === "undefined" ||
        !document.fonts ||
        document.fonts.status === "loaded";

      if (minElapsed && docComplete && (fontsReady || maxElapsed)) {
        setReady(true);
        return;
      }

      if (!docComplete) {
        return;
      }

      if (!fontsReady) {
        document.fonts.ready.then(() => {
          const now = Date.now();
          if (now - start >= MIN_LOAD_TIME_MS) setReady(true);
          else setTimeout(setReady, MIN_LOAD_TIME_MS - (now - start), true);
        });
        return;
      }

      if (!minElapsed) {
        setTimeout(setReady, MIN_LOAD_TIME_MS - elapsed, true);
        return;
      }

      setReady(true);
    };

    if (document.readyState === "complete") {
      checkReady();
      return;
    }

    const onLoad = () => checkReady();
    window.addEventListener("load", onLoad);
    return () => window.removeEventListener("load", onLoad);
  }, []);

  return ready;
}
