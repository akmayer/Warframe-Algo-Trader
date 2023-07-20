import { environment } from "@/environment";
import { useState, useEffect } from "react";

function LiveScraperButton() {
  const [isRunning, setIsRunning] = useState(false);

  const fetchData = async () => {
    try {
      const response = await fetch(`${environment.API_BASE_URL}/live_scraper`);
      const data = await response.json();
      setIsRunning(data.Running);
    } catch (error) {
      console.error("Error fetching live scraper status:", error);
    }
  };

  useEffect(() => {
    const interval = setInterval(() => {
      fetchData();
    }, 1000); // Update every second
    fetchData();
    return () => {
      clearInterval(interval);
    };
  }, []);

  const handleButtonClick = () => {
    const apiUrl = isRunning
      ? `${environment.API_BASE_URL}/live_scraper/stop`
      : `${environment.API_BASE_URL}/live_scraper/start`;

    fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((response) => response.json())
      .then((data) => {
        setIsRunning(!isRunning);
      })
      .catch((error) => console.log(error));
  };

  return (
    <div className="p-2">
      <button
        className={
          isRunning
            ? "p-1 rounded-lg bg-rose-700 text-white-custom shadow-md shadow-rose-700"
            : "p-1 rounded-lg bg-purple-custom-saturated text-white-custom shadow-md shadow-purple-700"
        }
        onClick={handleButtonClick}
      >
        {isRunning ? "Stop" : "Start"}
      </button>
      <span>
        {isRunning
          ? " - Live Updater Status: Running"
          : " - Live Updater Status: Not running"}
      </span>
    </div>
  );
}

export default LiveScraperButton;
