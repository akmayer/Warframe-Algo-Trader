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
import settingsLogo from "./assets/settings.png";
import Settings from './settings';

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

  const [isSettingsVisible, setIsSettingsVisible] = useState(false);

  const toggleSettingsVisibility = () => {
    setIsSettingsVisible(prevState => !prevState);
  };

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
    <div className="">
      <Clock />

      <div className="main-subprocess-control-block">
        <div className="subprocess-header">
          Subprocess Control
        </div>
        <div className="module-row">
          <StatsScraperButton />
          <LiveScraperButton />
          <ScreenReaderButton />
        </div>
      </div>

      <div className="settings-container">
        <a><img src={settingsLogo.src} alt="Settings" className="settings-logo" onClick={toggleSettingsVisibility}/></a>
      </div>

      <div className="inventory-manager">
        
        {/*
        <h1 className="text-center font-semibold pb-12 text-4xl">
          Inventory Manager
        </h1>
  */}
        <BuyBlock />
        <br></br>
        <RowDisplay />
        <div className="inventory-summary">
          Total Purchase Price: {itemTotals.total_purchase_price}
          <br />
          Total Listed Price: {itemTotals.total_listed_price}
        </div>
      </div>

      <div className="visuals-block">
        <div className="module-header">
            Visualizations
        </div>
        <GraphGen />
      </div>

      {isSettingsVisible && <Settings/>}

    </div>
   
  );
}
