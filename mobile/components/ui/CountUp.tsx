import React, { useEffect, useState } from "react";
import { Text, TextStyle } from "react-native";

interface CountUpProps {
  value: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  durationMs?: number;
  style?: TextStyle;
}

export default function CountUp({
  value,
  decimals = 0,
  prefix = "",
  suffix = "",
  durationMs = 800,
  style,
}: CountUpProps) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let startTimestamp: number | null = null;
    let animationFrame: number;

    const step = (timestamp: number) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / durationMs, 1);
      // Ease out cubic
      const easedProgress = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(easedProgress * value);

      if (progress < 1) {
        animationFrame = requestAnimationFrame(step);
      } else {
        setDisplayValue(value);
      }
    };

    animationFrame = requestAnimationFrame(step);

    return () => {
      if (animationFrame) cancelAnimationFrame(animationFrame);
    };
  }, [value, durationMs]);

  return (
    <Text style={style}>
      {prefix}
      {displayValue.toFixed(decimals)}
      {suffix}
    </Text>
  );
}
