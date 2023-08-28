import { environment } from "@/environment";
import { ChangeEvent, useState } from "react";
import { useEffect } from "react";
import CSS from 'csstype';

export default function BuyBlock() {
  const [itemName, setItemName] = useState("");
  const [price, setPrice] = useState("");
  const [allItemNames, setAllItemNames] = useState<string[]>([]);

  useEffect(() => {
    fetch(`${environment.API_BASE_URL}/all_items`)
      .then((response) => response.json())
      .then((data) => {
        setAllItemNames(data.item_names);
      })
      .catch((error) => console.log(error));
  }, []);

  const handleItemNameChange = (event: ChangeEvent<HTMLInputElement>) => {
    const inputValue = event.target.value;
    const formattedInputValue = inputValue.replace(/\s+/g, "_");
    setItemName(formattedInputValue);
  };

  const handleButtonClick = (buttonId : string) => {
    if (itemName === "" || price === "" || isNaN(Number(price))) {
      // Check if either textbox is empty or price is not a number
      return;
    }

    const formattedItemName = itemName.replace(/\s+/g, "_").toLowerCase();

    if (!allItemNames.includes(formattedItemName)) {
      // Check if the formatted item name is not in the predetermined list
      return;
    }

    const itemData = {
      name: formattedItemName,
      purchasePrice: price,
      number: 1,
    };
    (document.getElementById(buttonId) as HTMLButtonElement)!.disabled = true;

    if (buttonId === "buyButton") {
      const transactionData = {
        name: formattedItemName,
        transaction_type: "buy",
        price: price,
      };

      fetch(`${environment.API_BASE_URL}/market/close`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(transactionData),
      })
      .then((response) => response.json())
      .then((data) => {
        console.log(data);
      })
    }

    fetch(`${environment.API_BASE_URL}/item`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(itemData),
    })
      .then((response) => response.json())
      .then((data) => {
        // Handle response data if needed
        console.log(data);

        // Send transaction data
        const transactionData = {
          name: formattedItemName,
          transaction_type: "buy",
          price: price,
        };

        fetch(`${environment.API_BASE_URL}/transaction`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(transactionData),
        })
          .then((response) => response.json())
          .then((transactionResponse) => {
            // Handle transaction response if needed
            console.log(transactionResponse);

            // Reset input values
            setItemName("");
            setPrice("");

            //window.location.reload();
          })
          .catch((error) => console.log(error));
      })
      .catch((error) => console.log(error));

    setItemName("");
    setPrice("");

    (document.getElementById(buttonId) as HTMLButtonElement)!.disabled =
      false;
  };

  return (
    <div className="main-buy-block">
      <div className="module-header">Purchase New Item</div>
      <input
        className=""
        type="text"
        list="itemNames"
        placeholder="Item Name"
        value={itemName}
        onChange={handleItemNameChange}
      />
      <datalist id="itemNames">
        {allItemNames.map((name) => (
          <option key={name} value={name} />
        ))}
      </datalist>
      <input
        className=""
        type="text"
        placeholder="Price"
        value={price}
        onChange={(event) => setPrice(event.target.value)}
      />
      <div className="button-collection">
        <button
          className=""
          onClick={() => handleButtonClick("buyButton")}
          id="buyButton"
        >
          Buy
        </button>
        <button
          className=""
          onClick={() => handleButtonClick("addButton")}
          id="addButton"
        >
          Buy (w/o Reporting)
        </button>
      </div>
    </div>
  );
}
