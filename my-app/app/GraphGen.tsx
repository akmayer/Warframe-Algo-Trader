import { environment } from "@/environment";
import React, { useState } from "react";

const GraphGen: React.FC = () => {
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageUrl, setImageUrl] = useState("");

  const handleStartDateChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setStartDate(event.target.value);
  };

  const handleEndDateChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setEndDate(event.target.value);
  };

  const handleButtonClick = () => {
    // Make the API call with the start and end dates
    const apiUrl = `${environment.API_BASE_URL}/graph?startDate=${startDate}&endDate=${endDate}`;

    // You can use any method for making the API call, e.g., fetch, axios, etc.
    // Assuming using fetch here for simplicity
    fetch(apiUrl)
      .then((response) => {
        if (response.ok) {
          // Save the image to public/accValue.png
          return response.blob();
        }
        throw new Error("API request failed");
      })
      .then((imageBlob) => {
        // Create a local URL for the image blob
        const imageUrl = URL.createObjectURL(imageBlob);

        // Set the image URL and mark it as loaded
        setImageUrl(imageUrl);
        setImageLoaded(true);
      })
      .catch((error) => {
        console.error(error);
        // Handle error
      });
  };

  let imageElement = null;
  if (imageLoaded) {
    imageElement = <img className="mx-auto" src={imageUrl} alt="Graph" />;
  }

  return (
    <div className="p-8 shadow-lg shadow-slate-400 bg-black-custom rounded-md">
      <label htmlFor="startDate">Start Date: </label>
      <input
        className="text-center py-2 px-4 mb-4 border border-purple-custom-saturated rounded-lg bg-slate-600 text-white-custom"
        type="text"
        id="startDate"
        placeholder="YYYY-MM-DD"
        value={startDate}
        onChange={handleStartDateChange}
      />
      <br></br>

      <label htmlFor="endDate">End Date: </label>
      <input
        className="text-center py-2 px-4 mb-4 border border-purple-custom-saturated rounded-lg bg-slate-600 text-white-custom"
        type="text"
        id="endDate"
        placeholder="YYYY-MM-DD"
        value={endDate}
        onChange={handleEndDateChange}
      />
      <br></br>

      <button
        className="py-2 px-6 rounded-md bg-purple-custom-saturated text-white-custom shadow-md shadow-purple-700"
        onClick={handleButtonClick}
      >
        Load Graph
      </button>

      {imageElement}
    </div>
  );
};

export default GraphGen;
