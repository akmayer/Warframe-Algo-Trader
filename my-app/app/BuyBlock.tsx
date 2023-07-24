import { useState } from "react";
import { useEffect } from "react";

export default function BuyBlock() {
    const [itemName, setItemName] = useState("");
    const [price, setPrice] = useState("");
    const [allItemNames, setAllItemNames] = useState([]);

    useEffect(() => {
      fetch("http://127.0.0.1:8000/all_items")
        .then((response) => response.json())
        .then((data) => {
          setAllItemNames(data.item_names);
        })
        .catch((error) => console.log(error));
    }, []);

    const handleItemNameChange = (event) => {
      const inputValue = event.target.value;
      const formattedInputValue = inputValue.replace(/\s+/g, "_");
      setItemName(formattedInputValue);
    };
    
    const handleButtonClick = () => {
      if (itemName === "" || price === "" || isNaN(price)) {
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
      document.getElementById("buyButton").disabled = true;
  
      fetch("http://127.0.0.1:8000/item/", {
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
  
          fetch("http://127.0.0.1:8000/transaction/", {
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
      document.getElementById("buyButton").disabled = false;
    };
    
    return (
      <div className="w-[36vw] m-auto items-center justify-center p-[1.5vw] rounded-[1vw] bg-grey-custom-light mb-[1.5vw]">
        <h1 className="pb-[1vw] text-[1vw]">Purchase New Item:</h1>
        <input
        className="text-center w-[15vw] h-[1vw] py-[1vw] px-[2vw] mx-[0.1vw] mb-[1vw] text-[0.9vw] shadow-[inset_0_0px_0px_0.25vw] shadow-grey-custom-darkgreen border border-blue-custom bg-black-custom border-[0.1vw] text-white-custom"
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
          className="text-center w-[15vw] h-[1vw] py-[1vw] px-[2vw] mx-[0.1vw] mb-[1vw] text-[0.9vw] shadow-[inset_0_0px_0px_0.25vw] shadow-grey-custom-darkgreen border border-blue-custom bg-black-custom border-[0.1vw] text-white-custom"
          type="text"
          placeholder="Price"
          value={price}
          onChange={(event) => setPrice(event.target.value)}
        />
        
        <button className="py-[0.3vw] px-[0.5vw] w-[4vw] h-[2vw] bg-blue-custom-light text-black-custom-text text-[0.9vw] hover:bg-blue-custom-highlight transition duration-500" onClick={handleButtonClick} id="buyButton">Buy</button>
        
      </div>
    );
  }