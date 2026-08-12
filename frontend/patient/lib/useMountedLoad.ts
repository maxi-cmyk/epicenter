"use client";

import { useEffect } from "react";

/** Run an async loader after mount without synchronous setState inside the effect body. */
export function useMountedLoad(load: () => void | Promise<void>) {
  useEffect(() => {
    let active = true;
    const timer = window.setTimeout(() => {
      if (active) void load();
    }, 0);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [load]);
}
