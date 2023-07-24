import { useState } from "react";
import { useEffect } from "react";
interface Row {
    id: number;
    name: string;
    purchasePrice: number;
    listedPrice: number;
    number: number;
  }
  
export default function RowDisplay() {
  const [rows, setRows] = useState([]);
  const [inProg, setInProg] = useState("");

  useEffect(() => {
    // Fetch data from the REST API
    const interval = setInterval(() => {
      console.log("ping");
      fetch("http://127.0.0.1:8000/items")
        .then((response) => response.json())
        .then((data) => setRows(data))
        .catch((error) => console.log(error));
    }, 1000); // Update every second

    console.log("In useEffect");
    fetch("http://127.0.0.1:8000/items")
      .then((response) => response.json())
      .then((data) => setRows(data))
      .catch((error) => console.log(error));

    return () => {
      clearInterval(interval);
    };
  }, []);

  const handleButtonClick = (
    itemName,
    purchasePrice,
    listedPrice,
    number,
    price,
    buttonId
  ) => {

    if (price.trim() === "") {
      // Do nothing if the price is not entered
      return;
    }
    
    const updatedNumber = number - 1;
    setInProg("IN PROGRESS");

    // Prepare the data to be sent in the PUT request to "/market/{item_name}"
    const marketData = {
      name: itemName,
      purchasePrice: purchasePrice,
      number: updatedNumber,
    };

    // Prepare the data to be sent in the POST request to "/transaction/"
    const transactionData = {
      name: itemName,
      transaction_type: "sell",
      price: parseFloat(price),
    };
    // Disable the button
    document.getElementById(buttonId).disabled = true;

    // Trigger PUT API call to "/market/{item_name}"
    fetch(`http://127.0.0.1:8000/market/${itemName}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(marketData),
    })
      .then((response) => response.json())
      .then((marketResponseData) => {
        // Handle the response data if needed
        console.log(marketResponseData);
        setInProg("");

        // After the PUT API call to "/market/{item_name}" is completed, trigger the POST API call to "/transaction/"
        fetch(`http://127.0.0.1:8000/transaction/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(transactionData),
        })
          .then((response) => response.json())
          .then((transactionResponseData) => {
            // Handle the response data if needed
            console.log(transactionResponseData);

            // After the POST API call to "/transaction/" is completed, trigger the GET API call to "/item"
            fetch(`http://127.0.0.1:8000/item/sell`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify(marketData),
            })
              .then((response) => response.json())
              .then((itemResponseData) => {
                // Handle the response data if needed
                console.log(itemResponseData);

                // After the PUT API call to "/item" is completed, trigger the GET API call to "/items"
                fetch("http://127.0.0.1:8000/items")
                  .then((response) => response.json())
                  .then((data) => {
                    setRows(data);
                    document.getElementById(buttonId).disabled = false;
                  })
                  .catch((error) => console.log(error));
              })
              .catch((error) => console.log(error));
          })
          .catch((error) => console.log(error));
      })
      .catch((error) => console.log(error));
  };

  return (
    <div className="items-center justify-center p-[1.5vw] w-[36vw] m-auto rounded-[1vw] bg-grey-custom-light mb-[1.5vw]">
      <h1 className="pb-[1vw] text-[1vw]">Inventory:</h1>
      <div className="w-full flex flex-col">
        <div className="flex font-bold py-[0.5vw] text-[0.8vw]">
          <div className="w-2/6 px-[2vw]">Name:</div>
          <div className="w-1/6 px-[2vw]">Avg Buy:</div>
          <div className="w-1/6 px-[2vw]">Listed Price:</div>
          <div className="w-1/6 px-[2vw]">Number Owned:</div>
          <div className="w-1/6 px-[2vw]">Sell Price:</div>
        </div>
        {rows.map((row) => {
          const textBoxId = `textbox-${row.id}`;
          const buttonId = `button-${row.id}`;
          return (
            <div
              key={row.id}
              className="flex text-[0.6vw] items-center border-b-[0.1vw] border-grey-custom py-[0.5vw]"
            >
              <div className="w-2/6 px-[2vw]">{row.name}</div>
              <div className="w-1/6 px-[2vw]">{row.purchasePrice}</div>
              <div className="w-1/6 px-[2vw]">{row.listedPrice}</div>
              <div className="w-1/6 px-[2vw]">{row.number}</div>
              <div className="w-1/6 px-[2vw]">
                <div className="min-w-[0.5vw]">
                  <input
                    type="text"
                    id={textBoxId}
                    className="text-center py-[0.5vw] px-[1vw] w-[2vw] shadow-[inset_0_0px_0px_0.25vw] border-[0.1vw] shadow-grey-custom-darkgreen border-blue-custom bg-black-custom text-white-custom"
                  />
                  <button
                    onClick={() =>
                      handleButtonClick(
                        row.name,
                        row.purchasePrice,
                        row.listedPrice,
                        row.number,
                        document.getElementById(textBoxId).value,
                        buttonId
                      )
                    }
                    id={buttonId}
                    className="py-[0.3vw] px-[0.5vw] bg-blue-custom-light text-black-custom-text text-[0.9vw] hover:bg-blue-custom-highlight transition duration-500"
                  >
                    Sell
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      {inProg}
    </div>
  );
}