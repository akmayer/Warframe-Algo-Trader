import { environment } from "@/environment";
import { useState, useEffect } from "react";

function StatsScraperButton() {
  const [isRunning, setIsRunning] = useState(false);

  const fetchData = async () => {
    try {
      const response = await fetch(`${environment.API_BASE_URL}/stats_scraper`);
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
      ? `${environment.API_BASE_URL}/stats_scraper/stop`
      : `${environment.API_BASE_URL}/stats_scraper/start`;

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
    <div className="module-column">
      <button
        className={
          isRunning
            ? "p-1 rounded-lg bg-rose-700 text-white-custom shadow-md shadow-rose-700"
            : "p-1 rounded-lg bg-purple-custom-saturated text-white-custom shadow-md shadow-purple-700"
        }
        onClick={handleButtonClick}
      >
        {isRunning ? "Stop Stats Scraper" : "Start Stats Scraper"}
      </button>
    </div>
  );
}

export default StatsScraperButton;
