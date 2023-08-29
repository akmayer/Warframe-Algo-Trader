//import Image from 'next/image'
//import styles from './page.module.css'
import { environment } from "@/environment";
import { ChangeEvent, useState, useEffect } from "react";


export default function Settings() {
  const [allItemNames, setAllItemNames] = useState<string[]>([]);
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [unselectedItems, setUnselectedItems] = useState<string[]>([]);

  useEffect(() => {
    fetch(`${environment.API_BASE_URL}/all_items`)
      .then((response) => response.json())
      .then((data) => {
        setAllItemNames(data.item_names);
        setUnselectedItems(data.item_names);
      })
      .catch((error) => console.log(error));
  }, []);

  useEffect(() => {
    setUnselectedItems(subtractList(allItemNames, selectedItems));
  }, [selectedItems]);


  const subtractList = (largerList: string[], smallerList: string[]) => {
    return largerList.filter(item => !smallerList.includes(item));
  }

  const addToList = (name: string) => {
    setSelectedItems(prevItems => [...prevItems, name]);
  }

  const removeFromList = (name: string) => {
    setSelectedItems(subtractList(selectedItems, [name]));
  }

  return (
    <div className="settings-popup">  
      <div className="settings-scroll">
        <div className="settings-row">
          Input Settings
        </div>

        <div className="settings-row">
          <div className="flex-element">
            Price Shift Threshold:
            <input />
          </div>
          <div className="flex-element">
            Volume Threshold:
            <input />
          </div>
        </div>

        <div className="settings-row">
          <div className="flex-element">
            Range Threshold:
            <input />
          </div>
          <div className="flex-element">
            Avg. Price Cap:
            <input />
          </div>
        </div>

        <div className="settings-row">
          <div className="flex-element">
            Max Total Plat Cap:
            <input />
          </div>
          <div className="flex-element">
            Strict Whitelist:
            <label className="switch">
              <input type="checkbox" />
              <span className="slider round" />
            </label>
          </div>
        </div>

        <div className="settings-row">
          <div className="flex-element">
            Ping On Notif: 
            <label className="switch">
              <input type="checkbox" />
              <span className="slider round" />
            </label>
          </div>
        </div>

        <div className="settings-row">
          <div className="flex-element">
            <button>
            Edit Blacklist
            </button>
          </div>
          <div className="flex-element">
            <button>
            Edit Whitelist
            </button>
          </div>
        </div>
        
        <div className="list-container">
          <div className="settings-row">
            <div className="flex-element">
              <input />
            </div>
            <div className="flex-element">
              <button>
              Push filtered onto list -&gt;
              </button>
            </div>
            <div className="flex-element">
              <button>
              &lt;- Remove filtered off list
              </button>
            </div>
            <div className="flex-element">
              <input />
            </div>
          </div>

          <div className="settings-row">
            <div className="list flex-element">
              {unselectedItems.map((name) => (
                <div className="list-element" onClick={(e) => {addToList(name)}}>{name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</div>
              ))}
            </div>
            <div className="list flex-element">
              {selectedItems.map((name) => (
                <div className="list-element" onClick={(e) => {removeFromList(name)}}>{name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</div>
              ))}
            </div>
          </div>
        </div>

        
        
      </div>
    </div>
  );
}