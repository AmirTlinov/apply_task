import { useEffect, useState } from "react";

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return false;
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return;
    const mediaQueryList = window.matchMedia(query);
    const onChange = () => setMatches(mediaQueryList.matches);

    onChange();

    if (typeof mediaQueryList.addEventListener === "function") {
      mediaQueryList.addEventListener("change", onChange);
      return () => mediaQueryList.removeEventListener("change", onChange);
    }

    // Safari fallback
    // eslint-disable-next-line deprecation/deprecation
    mediaQueryList.addListener(onChange);
    // eslint-disable-next-line deprecation/deprecation
    return () => mediaQueryList.removeListener(onChange);
  }, [query]);

  return matches;
}

