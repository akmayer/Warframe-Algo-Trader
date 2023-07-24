import { useEffect } from "react";
import { useState } from "react";

export default function Clock() {
    const [currentTime, setCurrentTime] = useState("");
    const [timeUntilMidnight, setTimeUntilMidnight] = useState("");
  
    useEffect(() => {
      const interval = setInterval(() => {
        const date = new Date();
        const hours = date.getUTCHours().toString().padStart(2, "0");
        const minutes = date.getUTCMinutes().toString().padStart(2, "0");
        const seconds = date.getUTCSeconds().toString().padStart(2, "0");
        const time = `${hours}:${minutes}:${seconds}`;
        setCurrentTime(time);
  
        // Calculate time until midnight
        const midnight = new Date(date);
        midnight.setUTCHours(24, 0, 0, 0);
        const timeUntilMidnightMillis = midnight - date;
        const hoursUntilMidnight = Math.floor(timeUntilMidnightMillis / 3600000);
        const minutesUntilMidnight = Math.floor(
          (timeUntilMidnightMillis % 3600000) / 60000
        );
        const secondsUntilMidnight = Math.floor(
          (timeUntilMidnightMillis % 60000) / 1000
        );
        // Pad the time values with leading zeros
        const paddedHours = hoursUntilMidnight.toString().padStart(2, '0');
        const paddedMinutes = minutesUntilMidnight.toString().padStart(2, '0');
        const paddedSeconds = secondsUntilMidnight.toString().padStart(2, '0');

        const timeUntilMidnight = `${paddedHours}:${paddedMinutes}:${paddedSeconds}`;
        setTimeUntilMidnight(timeUntilMidnight);
      }, 1000); // Update every second
  
      return () => {
        clearInterval(interval);
      };
    }, []);
  
    return (
      <div className="absolute top-[2vh] left-[2vh] text-left z-100 text-[1vw]">
        <div>GMT: {currentTime}</div>
        <div>Time until midnight GMT: {timeUntilMidnight}</div>
      </div>
    );
  }
  
