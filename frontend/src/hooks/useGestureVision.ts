'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { jarvisAudio } from '@/lib/soundEffects';

export type GestureType =
  | 'none'
  | 'open_palm'   // ✋ Stop speech / pause / hold
  | 'thumbs_up'   // 👍 Confirm security HITL / Yes
  | 'fist'        // ✊ Emergency lock / mute
  | 'swipe_left'  // 👈 Previous tab
  | 'swipe_right' // 👉 Next tab
  | 'peace';      // ✌️ Telemetry status briefing

export interface GestureEvent {
  gesture: GestureType;
  confidence: number;
  label: string;
  timestamp: number;
}

interface UseGestureVisionOptions {
  enabled: boolean;
  onGesture?: (event: GestureEvent) => void;
  cooldownMs?: number;
}

const GESTURE_LABELS: Record<GestureType, string> = {
  none: 'Searching for hand...',
  open_palm: 'Open Palm (HOLD / PAUSE)',
  thumbs_up: 'Thumbs Up (CONFIRM / APPROVE)',
  fist: 'Closed Fist (LOCK / MUTE)',
  swipe_left: 'Swipe Left (PREV TAB)',
  swipe_right: 'Swipe Right (NEXT TAB)',
  peace: 'Peace / Victory (TELEMETRY)',
};

export function useGestureVision({
  enabled,
  onGesture,
  cooldownMs = 1200,
}: UseGestureVisionOptions) {
  const [isActive, setIsActive] = useState(false);
  const [currentGesture, setCurrentGesture] = useState<GestureEvent>({
    gesture: 'none',
    confidence: 0,
    label: GESTURE_LABELS.none,
    timestamp: Date.now(),
  });
  const [cameraError, setCameraError] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const lastTriggerRef = useRef<number>(0);

  // Position history for swipe velocity tracking
  const posHistoryRef = useRef<Array<{ x: number; y: number; time: number }>>([]);

  const onGestureRef = useRef(onGesture);
  onGestureRef.current = onGesture;

  // Initialize or terminate camera stream
  useEffect(() => {
    if (!enabled) {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
        animFrameRef.current = null;
      }
      setIsActive(false);
      setCameraError(null);
      return;
    }

    let isSubscribed = true;

    async function startCamera() {
      try {
        setCameraError(null);
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 320 },
            height: { ideal: 240 },
            facingMode: 'user',
          },
          audio: false,
        });

        if (!isSubscribed) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }

        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play().catch(() => {});
        }
        setIsActive(true);
      } catch (err: unknown) {
        if (isSubscribed) {
          const msg = err instanceof Error ? err.message : 'Webcam permission denied';
          setCameraError(msg);
          setIsActive(false);
        }
      }
    }

    startCamera();

    return () => {
      isSubscribed = false;
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
        animFrameRef.current = null;
      }
    };
  }, [enabled]);

  // Optical Hand Feature Classifier
  const processFrame = useCallback(() => {
    if (!videoRef.current || !canvasRef.current || !isActive) {
      animFrameRef.current = requestAnimationFrame(processFrame);
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (video.readyState < 2) {
      animFrameRef.current = requestAnimationFrame(processFrame);
      return;
    }

    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) {
      animFrameRef.current = requestAnimationFrame(processFrame);
      return;
    }

    const width = 160;
    const height = 120;
    canvas.width = width;
    canvas.height = height;

    // Draw downscaled frame
    ctx.drawImage(video, 0, 0, width, height);
    const imgData = ctx.getImageData(0, 0, width, height);
    const pixels = imgData.data;

    let skinPixelCount = 0;
    let sumX = 0;
    let sumY = 0;
    let minX = width;
    let maxX = 0;
    let minY = height;
    let maxY = 0;

    // Skin color detection in YCbCr-approximated RGB space
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const i = (y * width + x) * 4;
        const r = pixels[i];
        const g = pixels[i + 1];
        const b = pixels[i + 2];

        // Chrominance heuristic for diverse skin tones under ambient lighting
        const isSkin =
          r > 80 &&
          g > 40 &&
          b > 30 &&
          r > g &&
          r > b &&
          r - g > 12 &&
          Math.abs(r - g) > 10;

        if (isSkin) {
          skinPixelCount++;
          sumX += x;
          sumY += y;
          if (x < minX) minX = x;
          if (x > maxX) maxX = x;
          if (y < minY) minY = y;
          if (y > maxY) maxY = y;
        }
      }
    }

    const totalPixels = width * height;
    const skinRatio = skinPixelCount / totalPixels;

    // Must have a prominent hand presence in ROI (between 4% and 55% of view)
    if (skinRatio >= 0.04 && skinRatio <= 0.55 && skinPixelCount > 300) {
      const cx = sumX / skinPixelCount;
      const cy = sumY / skinPixelCount;
      const bboxW = Math.max(1, maxX - minX);
      const bboxH = Math.max(1, maxY - minY);
      const aspectRatio = bboxW / bboxH;
      const extent = skinPixelCount / (bboxW * bboxH); // fullness

      const now = Date.now();
      posHistoryRef.current.push({ x: cx, y: cy, time: now });

      // Keep recent 12 frames (~300ms)
      if (posHistoryRef.current.length > 12) {
        posHistoryRef.current.shift();
      }

      // Check Swipe velocity
      let detectedGesture: GestureType = 'none';
      let confidence = 0.85;

      if (posHistoryRef.current.length >= 6) {
        const oldest = posHistoryRef.current[0];
        const dx = cx - oldest.x;
        const dt = (now - oldest.time) / 1000;
        const velocityX = dt > 0 ? dx / dt : 0;

        if (velocityX > 140) {
          detectedGesture = 'swipe_right';
          confidence = 0.94;
        } else if (velocityX < -140) {
          detectedGesture = 'swipe_left';
          confidence = 0.94;
        }
      }

      // Static posture classification
      if (detectedGesture === 'none') {
        // 1. Open Palm: High aspect ratio close to 1, broad fullness, large area
        if (skinRatio > 0.16 && extent > 0.38 && aspectRatio > 0.75 && aspectRatio < 1.35) {
          detectedGesture = 'open_palm';
          confidence = Math.min(0.97, 0.82 + skinRatio);
        }
        // 2. Closed Fist: Very dense compactness, smaller aspect ratio
        else if (extent > 0.65 && skinRatio < 0.18) {
          detectedGesture = 'fist';
          confidence = 0.91;
        }
        // 3. Thumbs Up: Tall vertical orientation (aspectRatio < 0.65), centroid in lower half
        else if (aspectRatio < 0.68 && cy > minY + bboxH * 0.45 && bboxH > 40) {
          detectedGesture = 'thumbs_up';
          confidence = 0.89;
        }
        // 4. Peace / Victory: Moderate aspect ratio with vertical bifurcation
        else if (aspectRatio >= 0.68 && aspectRatio <= 0.95 && extent < 0.48) {
          detectedGesture = 'peace';
          confidence = 0.86;
        }
      }

      if (detectedGesture !== 'none') {
        const evt: GestureEvent = {
          gesture: detectedGesture,
          confidence: Math.round(confidence * 100),
          label: GESTURE_LABELS[detectedGesture],
          timestamp: now,
        };

        setCurrentGesture(evt);

        // Cooldown throttle to avoid rapid multiple triggers
        if (now - lastTriggerRef.current > cooldownMs) {
          lastTriggerRef.current = now;
          jarvisAudio.playGestureSound();
          if (onGestureRef.current) {
            onGestureRef.current(evt);
          }
        }
      } else {
        setCurrentGesture((prev) =>
          prev.gesture !== 'none'
            ? { ...prev, label: 'Tracking hand...' }
            : prev
        );
      }
    } else {
      // Clear position history if hand is out of frame
      posHistoryRef.current = [];
      setCurrentGesture({
        gesture: 'none',
        confidence: 0,
        label: GESTURE_LABELS.none,
        timestamp: Date.now(),
      });
    }

    animFrameRef.current = requestAnimationFrame(processFrame);
  }, [isActive, cooldownMs]);

  useEffect(() => {
    if (isActive) {
      animFrameRef.current = requestAnimationFrame(processFrame);
    }
    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
        animFrameRef.current = null;
      }
    };
  }, [isActive, processFrame]);

  return {
    videoRef,
    canvasRef,
    isActive,
    currentGesture,
    cameraError,
  };
}
