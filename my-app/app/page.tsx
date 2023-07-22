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
import { environment } from "@/environment";

interface ItemTotals {
  total_purchase_price: number;
  total_listed_price: number;
}

async function fetchItemTotals(): Promise<ItemTotals> {
  try {
    const response = await fetch(`${environment.API_BASE_URL}/items/sum`);
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
    <div className="flex h-full min-h-screen text-purple-custom-light bg-gradient-to-b from-black-custom via-cyan-900 to-cyan-800">
      <div className="w-1/2 text-center items-center p-32 justify-center">
        <Clock />

        <h1 className="text-center font-semibold pb-12 text-4xl">
          Inventory Manager
        </h1>
        <BuyBlock />
        <br></br>
        <RowDisplay />
        <br></br>
        <div className="p-4 rounded-md  bg-black-custom shadow-lg shadow-slate-400">
          Total Purchase Price: {itemTotals.total_purchase_price}
          <br />
          Total Listed Price: {itemTotals.total_listed_price}
        </div>
      </div>
      <div className="w-1/2 text-center items-center p-32 justify-center">
        <h1 className="text-center font-semibold pb-12 text-4xl">
          Transaction Control
        </h1>
        <div className="p-4 rounded-full bg-black-custom shadow-lg shadow-slate-400">
          <StatsScraperButton />
          <LiveScraperButton />
          <ScreenReaderButton />
        </div>
        <h1 className="text-center font-semibold p-12 text-4xl">
          Visualizations
        </h1>
        <GraphGen />
      </div>
    </div>
  );
}
