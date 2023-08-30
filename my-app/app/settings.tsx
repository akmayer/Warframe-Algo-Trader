//import Image from 'next/image'
//import styles from './page.module.css'
import { environment } from "@/environment";
import { ChangeEvent, useState, useEffect } from "react";


export default function Settings() {
  const [allItemNames, setAllItemNames] = useState<string[]>([]);
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [unselectedItems, setUnselectedItems] = useState<string[]>([]);
  const [displayingBlacklist, setDisplayingBlacklist] = useState<boolean>(false);
  const [displayingWhitelist, setDisplayingWhitelist] = useState<boolean>(false);
  const [listSaved, setListSaved] = useState<boolean>(true);

  const [settings, setSettings] = useState<{}>({});

  useEffect(() => {
    fetch(`${environment.API_BASE_URL}/all_items`)
      .then((response) => response.json())
      .then((data) => {
        setAllItemNames(data.item_names);
        setSelectedItems([]);
      })
      .catch((error) => console.log(error));
    fetch(`${environment.API_BASE_URL}/settings`)
      .then((response) => response.json())
      .then((data) => {
        setSettings(data);
      })
      .catch((error) => console.log(error));
  }, []);

  useEffect(() => {
    setUnselectedItems(subtractList(allItemNames, selectedItems));
  }, [selectedItems]);

  useEffect(() => {
    console.log("S", settings);
  }, [settings])

  useEffect(() => {
    console.log(listSaved);
    if (!listSaved) {
      if (displayingBlacklist) {
        console.log(settings["blacklistedItems" as keyof {}]);
        setSelectedItems(settings["blacklistedItems" as keyof {}]);
      }
      else if (displayingWhitelist) {
        setSelectedItems(settings["whitelistedItems" as keyof {}]);
      }
    }
  }, [listSaved])


  const subtractList = (largerList: string[], smallerList: string[]) => {
    return largerList.filter(item => !smallerList.includes(item));
  }

  const addToList = (name: string) => {
    setSelectedItems(prevItems => [...prevItems, name]);
  }

  const removeFromList = (name: string) => {
    setSelectedItems(subtractList(selectedItems, [name]));
  }

  const toggleShowBlacklist = () => {
    setDisplayingBlacklist(true);
    setListSaved(false);
  }

  const toggleShowWhitelist = () => {
    setDisplayingWhitelist(true);
    setListSaved(false);
  }

  const saveList = () => {
    console.log("Selected before saving", selectedItems);
    if (displayingBlacklist) {
      setSettings(prevState => ({
        ...prevState,
        "blacklistedItems" : selectedItems
    }));;
    }
    if (displayingWhitelist) {
      setSettings(prevState => ({
        ...prevState,
        "whitelistedItems" : selectedItems
    }));;
    }
    setDisplayingBlacklist(false);
    setDisplayingWhitelist(false);
    setSelectedItems([]);
    setListSaved(true);
  }

  const discardList = () => {
    setDisplayingBlacklist(false);
    setDisplayingWhitelist(false);
    setSelectedItems([]);
    setListSaved(true);
  }



  return (
    <div className="settings-popup">  
      <div className="settings-scroll">
        <div className="settings-row module-header">
          Settings
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

        {listSaved && <div className="settings-row">
          <div className="flex-element">
            <button onClick={toggleShowBlacklist}>
            Edit Blacklist
            </button>
          </div>
          <div className="flex-element">
            <button onClick={toggleShowWhitelist}>
            Edit Whitelist
            </button>
          </div>
        </div>}
        
        {(displayingBlacklist || displayingWhitelist) && <div className="list-container">
          <div className="settings-row">
            {displayingBlacklist && <div className="flex-element subprocess-header">Editing Blacklist</div>}
            {displayingWhitelist && <div className="flex-element subprocess-header">Editing Whitelist</div>}
          </div>

          <div className="settings-row">
            <div className="flex-element">
              <button onClick={discardList}>
              Discard
              </button>
            </div>
            <div className="flex-element">
              <button onClick={saveList}>
              Save
              </button>
            </div>
          </div>

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
        </div>}
  
      </div>
    </div>
  );
}