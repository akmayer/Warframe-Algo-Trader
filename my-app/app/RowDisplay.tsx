import { environment } from "@/environment";
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
  const [rows, setRows] = useState<Row[]>([]);
  const [inProg, setInProg] = useState("");

  useEffect(() => {
    // Fetch data from the REST API
    const interval = setInterval(() => {
      console.log("ping");
      fetch(`${environment.API_BASE_URL}/items`)
        .then((response) => response.json())
        .then((data) => setRows(data))
        .catch((error) => console.log(error));
    }, 1000); // Update every second

    console.log("In useEffect");
    fetch(`${environment.API_BASE_URL}/items`)
      .then((response) => response.json())
      .then((data) => setRows(data))
      .catch((error) => console.log(error));

    return () => {
      clearInterval(interval);
    };
  }, []);

  const handleButtonClick = (
    itemName: string,
    purchasePrice: number,
    listedPrice: number,
    number: number,
    price: string,
    buttonId: string
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
    (document.getElementById(buttonId) as HTMLButtonElement)!.disabled = true;

    const parts = buttonId.split("-");
    const lastPart = parts[parts.length - 1];

    let apiEndpoint: string;

    if (lastPart === "del") {
      // Perform specific action for "del"
      apiEndpoint = `${environment.API_BASE_URL}/market/remove`;
      console.log("Button with id", buttonId, "clicked. Action: 'del'");
      // Your action for "del" goes here
    } else {
      // Perform default action for other cases
      apiEndpoint = `${environment.API_BASE_URL}/market/close`;
      console.log("Button with id", buttonId, "clicked. Default action");
      // Your default action goes here
    }

    // Trigger PUT API call to "/market/{item_name}"
    fetch(`${apiEndpoint}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(transactionData),
    })
      .then((response) => response.json())
      .then((marketResponseData) => {
        // Handle the response data if needed
        console.log(marketResponseData);
        setInProg("");

        // After the PUT API call to "/market/{item_name}" is completed, trigger the POST API call to "/transaction/"
        fetch(`${environment.API_BASE_URL}/transaction/`, {
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
            fetch(`${environment.API_BASE_URL}/item/sell`, {
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
                fetch(`${environment.API_BASE_URL}/items`)
                  .then((response) => response.json())
                  .then((data) => {
                    setRows(data);
                    (document.getElementById(
                      buttonId
                    ) as HTMLButtonElement)!.disabled = false;
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
    <div className="main-inventory-block">
      <div className="module-header">Inventory:</div>
      <table className="inventory-grid">
        <tbody>
          <tr className="inventory-row column-names">
            <td className="item">Name:</td>
            <td className="item">Avg Purchase Price:</td>
            <td className="item">Listed Price:</td>
            <td className="item">Number Owned:</td>
            <td className="item">Sell Price:</td>
          </tr>
          {rows.map((row) => {
            const textBoxId = `textbox-${row.id}`;
            const sellButtonId = `button-${row.id}-sell`;
            const delButtonId = `button-${row.id}-del`;
            return (
              <tr
                key={row.id}
                className="inventory-row"
              >
                <td className="item">{row.name}</td>
                <td className="item">{row.purchasePrice}</td>
                <td className="item">{row.listedPrice}</td>
                <td className="item">{row.number}</td>
                <td className="item">
                  <div className="min-w-[100px]">
                    <input
                      type="text"
                      id={textBoxId}
                      className="text-center py-1 px-2 w-12 border border-purple-custom-saturated rounded-lg bg-slate-600"
                    />
                    <button
                      onClick={() =>
                        handleButtonClick(
                          row.name,
                          row.purchasePrice,
                          row.listedPrice,
                          row.number,
                          (document.getElementById(textBoxId) as HTMLInputElement)
                            ?.value,
                          sellButtonId
                        )
                      }
                      id={sellButtonId}
                      className="py-1 px-2 rounded-md bg-purple-custom-saturated text-white-custom shadow-md shadow-purple-700"
                    >
                      Sell
                    </button>
                    <button
                      onClick={() =>
                        handleButtonClick(
                          row.name,
                          row.purchasePrice,
                          row.listedPrice,
                          row.number,
                          (document.getElementById(textBoxId) as HTMLInputElement)
                            ?.value,
                          delButtonId
                        )
                      }
                      id={delButtonId}
                      className="py-1 px-2 rounded-md bg-purple-custom-saturated text-white-custom shadow-md shadow-purple-700"
                    >
                      Sell (w/o Reporting)
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {inProg}
    </div>
  );
}
