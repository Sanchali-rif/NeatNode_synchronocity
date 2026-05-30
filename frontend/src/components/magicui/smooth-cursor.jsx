import React, { useEffect, useState, useRef } from "react";
import { motion, useMotionValue, useSpring } from "framer-motion";

export function SmoothCursor() {
  const [isVisible, setIsVisible] = useState(false);
  const lastPosition = useRef({ x: 0, y: 0 });
  
  const cursorX = useMotionValue(-100);
  const cursorY = useMotionValue(-100);
  const rotation = useMotionValue(0);
  
  const springConfig = { damping: 25, stiffness: 300, mass: 0.5 };
  const cursorXSpring = useSpring(cursorX, springConfig);
  const cursorYSpring = useSpring(cursorY, springConfig);
  const rotationSpring = useSpring(rotation, { damping: 20, stiffness: 300, mass: 0.5 });

  useEffect(() => {
    // Disable on touch devices
    if (window.matchMedia("(pointer: coarse)").matches) {
      return;
    }

    const moveCursor = (e) => {
      const dx = e.clientX - lastPosition.current.x;
      const dy = e.clientY - lastPosition.current.y;
      
      // Only update rotation if there is significant movement to avoid jitter
      if (Math.abs(dx) > 2 || Math.abs(dy) > 2) {
        const angle = Math.atan2(dy, dx) * (180 / Math.PI);
        // The SVG points UP (0, -1). atan2 for UP is -90 degrees.
        // Add 90 to align the 0 degree rotation with the UP pointing SVG.
        const targetRotation = angle + 90;
        
        const currentRotation = rotation.get();
        // Calculate shortest path for rotation to prevent spinning backward when crossing -180/180
        let delta = targetRotation - currentRotation;
        delta = ((delta + 180) % 360) - 180;
        if (delta < -180) delta += 360;
        
        rotation.set(currentRotation + delta);
      }
      
      lastPosition.current = { x: e.clientX, y: e.clientY };

      cursorX.set(e.clientX);
      cursorY.set(e.clientY);
      if (!isVisible) setIsVisible(true);
    };

    window.addEventListener("mousemove", moveCursor);

    // Hide default cursor globally
    document.body.classList.add("hide-cursor");

    return () => {
      window.removeEventListener("mousemove", moveCursor);
      document.body.classList.remove("hide-cursor");
    };
  }, [cursorX, cursorY, rotation, isVisible]);

  if (typeof window !== "undefined" && window.matchMedia("(pointer: coarse)").matches) {
    return null;
  }

  return (
    <motion.div
      style={{
        position: 'fixed',
        left: 0,
        top: 0,
        pointerEvents: 'none',
        zIndex: 99999,
        x: cursorXSpring,
        y: cursorYSpring,
        rotate: rotationSpring,
        opacity: isVisible ? 1 : 0,
        translateX: "-50%",
        translateY: "-50%",
        color: 'var(--text-heading)', // Adapts to light/dark mode automatically
      }}
    >
      <svg 
        xmlns="http://www.w3.org/2000/svg" 
        width="28" 
        height="28" 
        viewBox="0 0 24 24" 
        fill="currentColor" 
        stroke="none"
        style={{
          filter: 'drop-shadow(0 4px 8px rgba(0,0,0,0.15))'
        }}
      >
        <path d="M12 2L4 22L12 17L20 22L12 2Z" />
      </svg>
    </motion.div>
  );
}
