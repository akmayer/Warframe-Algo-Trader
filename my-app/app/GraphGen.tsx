import React, { useState } from 'react';


const GraphGen: React.FC = () => {
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [imageLoaded, setImageLoaded] = useState(false);
    const [imageUrl, setImageUrl] = useState('');
  
    const handleStartDateChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      setStartDate(event.target.value);
    };
  
    const handleEndDateChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      setEndDate(event.target.value);
    };
  
    const handleButtonClick = () => {
      // Make the API call with the start and end dates
      const apiUrl = `http://127.0.0.1:8000/graph?startDate=${startDate}&endDate=${endDate}`;
  
      // You can use any method for making the API call, e.g., fetch, axios, etc.
      // Assuming using fetch here for simplicity
      fetch(apiUrl)
        .then(response => {
          if (response.ok) {
            // Save the image to public/accValue.png
            return response.blob();
          }
          throw new Error('API request failed');
        })
        .then(imageBlob => {
          // Create a local URL for the image blob
          const imageUrl = URL.createObjectURL(imageBlob);
  
          // Set the image URL and mark it as loaded
          setImageUrl(imageUrl);
          setImageLoaded(true);
        })
        .catch(error => {
          console.error(error);
          // Handle error
        });
    };
  
    let imageElement = null;
    if (imageLoaded) {
      imageElement = <img className="mx-auto" src={imageUrl} alt="Graph" />;
    }
  
    return (
      <div className="w-[36vw] m-auto items-center justify-center p-[1.5vw] rounded-[1vw] bg-grey-custom-light ">
        <table className='w-[100%] '>
          <tbody>
            <tr className='leading-[1vw]'>
              <td>
                <input 
                  className="text-center inline w-[15vw] h-[1vw] py-[1vw] px-[2vw] mx-[0.1vw] mb-[0.1vw] text-[0.9vw] shadow-[inset_0_0px_0px_0.25vw] shadow-grey-custom-darkgreen border-blue-custom bg-black-custom border-[0.1vw] text-white-custom"
                  type="text" 
                  id="startDate" 
                  placeholder='YYYY-MM-DD'
                  value={startDate} 
                  onChange={handleStartDateChange} />
              </td>
              <td>
                <input 
                  className="text-center inline w-[15vw] h-[1vw] py-[1vw] px-[2vw] mx-[0.1vw] mb-[0.1vw] text-[0.9vw] shadow-[inset_0_0px_0px_0.25vw] shadow-grey-custom-darkgreen border-blue-custom bg-black-custom border-[0.1vw] text-white-custom"
                  type="text" 
                  id="endDate" 
                  placeholder='YYYY-MM-DD'
                  value={endDate} 
                  onChange={handleEndDateChange} />
              </td>
            </tr>
            <tr className='leading-[1vw]'>
              <td><label htmlFor="startDate" className='inline-block align-bottom text-[0.7vw] text-center text-white-custom/30'>Start Date</label></td>
              <td><label htmlFor="endDate" className='inline-block align-bottom text-[0.7vw] text-center text-white-custom/30'>End Date</label></td>
            </tr>
          </tbody>
        </table>
        <button className="py-[0.3vw] px-[0.5vw] w-[6vw] h-[2vw] mb-[1vw] bg-blue-custom-light text-black-custom-text text-[0.9vw] hover:bg-blue-custom-highlight transition duration-500"  onClick={handleButtonClick}>Load Graph</button>
        
        {imageElement}
      </div>
    );
  };

<<<<<<< Updated upstream
export default GraphGen;
=======
  let imageElement = null;
  if (imageLoaded) {
    imageElement = <img className="mx-auto" src={imageUrl} alt="Graph" />;
  }

  return (
    <div className="w-[36vw] m-auto items-center justify-center p-[1.5vw] rounded-[1vw] bg-grey-custom-light ">
      <table className='w-[100%] '>
        <tbody>
          <tr className='leading-[1vw]'>
            <td>
              <input 
                className="text-center inline w-[15vw] h-[1vw] py-[1vw] px-[2vw] mx-[0.1vw] mb-[0.1vw] text-[0.9vw] shadow-[inset_0_0px_0px_0.25vw] shadow-grey-custom-darkgreen border-blue-custom bg-black-custom border-[0.1vw] text-white-custom"
                type="text" 
                id="startDate" 
                placeholder='YYYY-MM-DD'
                value={startDate} 
                onChange={handleStartDateChange} />
            </td>
            <td>
              <input 
                className="text-center inline w-[15vw] h-[1vw] py-[1vw] px-[2vw] mx-[0.1vw] mb-[0.1vw] text-[0.9vw] shadow-[inset_0_0px_0px_0.25vw] shadow-grey-custom-darkgreen border-blue-custom bg-black-custom border-[0.1vw] text-white-custom"
                type="text" 
                id="endDate" 
                placeholder='YYYY-MM-DD'
                value={endDate} 
                onChange={handleEndDateChange} />
            </td>
          </tr>
          <tr className='leading-[1vw]'>
            <td><label htmlFor="startDate" className='inline-block align-bottom text-[0.7vw] text-center text-white-custom/30'>Start Date</label></td>
            <td><label htmlFor="endDate" className='inline-block align-bottom text-[0.7vw] text-center text-white-custom/30'>End Date</label></td>
          </tr>
        </tbody>
      </table>
      <button className="py-[0.3vw] px-[0.5vw] w-[6vw] h-[2vw] mb-[1vw] bg-blue-custom-light text-black-custom-text text-[0.9vw] hover:bg-blue-custom-highlight transition duration-500"  onClick={handleButtonClick}>Load Graph</button>
      
      {imageElement}
    </div>
  );
};

export default GraphGen;
>>>>>>> Stashed changes
