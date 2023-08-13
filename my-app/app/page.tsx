"use client"; // This is a client component 👈🏽
//import Image from 'next/image'
//import styles from './page.module.css'
import { useState } from "react";
import { useEffect } from "react";
import BuyBlock from "./BuyBlock";
import Clock from "./Clock";
import RowDisplay from "./RowDisplay";
import LiveScraperButton from "./LiveScraperButton";
import StatsScraperButton from "./StatsScraperButton";
import ScreenReaderButton from "./ScreenReaderButton";
import GraphGen from "./GraphGen";

interface ItemTotals {
  total_purchase_price: number;
  total_listed_price: number;
}

async function fetchItemTotals(): Promise<ItemTotals> {
  try {
    const response = await fetch("http://127.0.0.1:8000/items/sum");
    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error fetching item totals:", error);
    return {
      total_purchase_price: 0,
      total_listed_price: 0,
    };
  }
}

export default function Home() {
  const [itemTotals, setItemTotals] = useState<ItemTotals>({
    total_purchase_price: 0,
    total_listed_price: 0,
  });

  useEffect(() => {
    const interval = setInterval(() => {
      fetchData();
    }, 1000); // Update every second
    const fetchData = async () => {
      const totals = await fetchItemTotals();
      setItemTotals(totals);
    };

    fetchData();
    return () => {
      clearInterval(interval);
    };
  }, []);

  return (
      <div className="flex h-full min-h-screen text-grey-custom bg-grey-custom-green bg-cover bg-center ">
        <Clock />
        <div className="w-[50vw] text-center items-center p-[5vw] justify-center self-center">

          
          
          <h1 className="text-center font-semibold pb-[1vw] text-[2vw]">
            Inventory Manager
          </h1>
          <BuyBlock />
          
          <RowDisplay />
          
          <div className="text-left p-[1vw] m-auto rounded-[1vw] bg-grey-custom-light w-[36vw] text-[0.8vw]">
            Total Purchase Price: {itemTotals.total_purchase_price}<br />
            Total Listed Price: {itemTotals.total_listed_price}
          </div>
          
        </div>
        <div className="w-[50vw] text-center items-center p-[5vw] justify-center self-center">
          <h1 className="text-center font-semibold pb-[1vw] text-[2vw]">
            Transaction Control
          </h1>
          <div className="flex flex-row justify-center p-[1vw] rounded-[1vw] bg-grey-custom-light text-[0.9vw]">
            <StatsScraperButton />
            <LiveScraperButton />
            <ScreenReaderButton />
          </div>
          <h1 className="text-center font-semibold pt-[1vw] pb-[1vw] text-[2vw]">
            Visualizations
          </h1>
          <GraphGen />
        </div>
      </div>
  )
}
