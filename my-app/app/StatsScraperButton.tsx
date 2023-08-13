import { useState, useEffect } from "react";

function StatsScraperButton() {
  const [isRunning, setIsRunning] = useState(false);

  const fetchData = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/stats_scraper");
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
      ? "http://127.0.0.1:8000/stats_scraper/stop"
      : "http://127.0.0.1:8000/stats_scraper/start";

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
    <div className="p-[0.5vw]">
      <button
        className={
          isRunning
            ? "p-[0.5vw] rounded-[0.5vw] w-[6.5vw] h-[6.5vw] bg-transparent border-[0.1vw] border-green-custom-light text-green-custom-light transition delay-50 hover:bg-blue-custom-highlight hover:border-blue-custom-highlight"
            : "p-[0.5vw] rounded-[0.5vw] w-[6.5vw] h-[6.5vw] bg-transparent border-[0.1vw] border-red-custom text-red-custom transition delay-50 hover:bg-red-custom-highlight hover:border-red-custom-highlight hover:text-black-custom-text "
        }
        onClick={handleButtonClick}>
        Market Stats
      </button>
    </div>
  );
}

export default StatsScraperButton;