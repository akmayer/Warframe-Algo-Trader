//import Image from 'next/image'
//import styles from './page.module.css'
import { environment } from "@/environment";
import { ChangeEvent, useState, useEffect } from "react";


export default function Settings() {
  const [allItemNames, setAllItemNames] = useState<string[]>([]);
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [unselectedItems, setUnselectedItems] = useState<string[]>([]);

  const [filteredSelected, setFilteredSelected] = useState<string[]>([]);
  const [filteredUnselected, setFilteredUnselected] = useState<string[]>([]);
  const [filterStringSel, setFilterStringSel] = useState<string>("");
  const [filterStringUnsel, setFilterStringUnsel] = useState<string>("");


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

  useEffect(() => {
    console.log("Set", settings);
    document.getElementById("strictWhitelist").checked = settings["strictWhitelist" as keyof {}];
    document.getElementById("pingOnNotif").checked = settings["pingOnNotif" as keyof {}];
  }, [settings])

  useEffect(() => {
    setFilteredUnselected(unselectedItems.filter(item => item.includes(filterStringUnsel)));
  }, [filterStringUnsel, unselectedItems])

  useEffect(() => {
    setFilteredSelected(selectedItems.filter(item => item.includes(filterStringSel)));
  }, [filterStringSel, selectedItems])


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
    }));
    }
    if (displayingWhitelist) {
      setSettings(prevState => ({
        ...prevState,
        "whitelistedItems" : selectedItems
    }));
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

  const pushToSelected = () => {
    setSelectedItems(selectedItems.concat(filteredUnselected));
    document.getElementById("filter-unselect").value="";
    setFilterStringUnsel("");
  }

  const pushToUnselected = () => {
    setSelectedItems(subtractList(selectedItems, filteredSelected));
    document.getElementById("filter-select").value="";
    setFilterStringSel("");
  }

  const writeSettings = async () => {
    try {
      const response = await fetch(`${environment.API_BASE_URL}/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });

      if (response.ok) {
        console.log('Settings successfully saved!');
      } else {
        console.error('Failed to save settings.');
      }
    } catch (error) {
      console.error('An error occurred:', error);
    }
  };



  return (
    <div className="settings-popup">  
      <div className="settings-scroll">
        <div className="settings-row module-header">
          Settings
        </div>
        <div className="settings-row">
          <div className="half-wide right">
            <button>
            Discard
            </button>
          </div>
          <div className="half-wide left">
            <button
            onClick={writeSettings}>
            Save
            </button>
          </div>
        </div>
        

        <div className="settings-row">
          <div className="flex-element half-wide">
            Price Shift Threshold:
            <input
            type="number"
            id="priceShiftThreshold"
            defaultValue={settings["priceShiftThreshold" as keyof {}]}
            onChange={(event) => setSettings(prevState => ({
              ...prevState,
              "priceShiftThreshold" : +event.target.value
            }))}
            />
          </div>
          <div className="flex-element half-wide">
            Volume Threshold:
            <input
            type="number"
            id="volumeThreshold"
            defaultValue={settings["volumeThreshold" as keyof {}]}
            onChange={(event) => setSettings(prevState => ({
              ...prevState,
              "volumeThreshold" : +event.target.value
            }))}
            />
          </div>
        </div>

        <div className="settings-row">
          <div className="flex-element half-wide">
            Range Threshold:
            <input 
            type="number"
            id="rangeThreshold"
            defaultValue={settings["rangeThreshold" as keyof {}]}
            onChange={(event) => setSettings(prevState => ({
              ...prevState,
              "rangeThreshold" : +event.target.value
            }))}
            />
          </div>
          <div className="flex-element half-wide">
            Avg. Price Cap:
            <input 
            type="number"
            id="avgPriceCap"
            defaultValue={settings["avgPriceCap" as keyof {}]}
            onChange={(event) => setSettings(prevState => ({
              ...prevState,
              "avgPriceCap" : +event.target.value
            }))}
            />
          </div>
        </div>

        <div className="settings-row">
          <div className="flex-element half-wide">
            Max Total Plat Cap:
            <input 
            type="number"
            id="maxTotalPlatCap"
            defaultValue={settings["maxTotalPlatCap" as keyof {}]}
            onChange={(event) => setSettings(prevState => ({
              ...prevState,
              "maxTotalPlatCap" : +event.target.value
            }))}
            />
          </div>
          <div className="flex-element half-wide">
            Strict Whitelist:
            <label className="switch">
              <input 
              type="checkbox"
              onClick={() => setSettings(prevState => ({
                ...prevState,
                "strictWhitelist" : !prevState["strictWhitelist" as keyof {}]
              }))}
              id="strictWhitelist"/>
              <span className="slider round" />
            </label>
          </div>
        </div>

        <div className="settings-row">
          <div className="flex-element">
            Ping On Notif: 
            <label className="switch">
              <input 
              type="checkbox"
              onClick={() => setSettings(prevState => ({
                ...prevState,
                "pingOnNotif" : !prevState["pingOnNotif" as keyof {}]
              }))}
              id="pingOnNotif"/>
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
            <div className="flex-element half-wide">
              <button onClick={discardList}>
              Discard Changes
              </button>
            </div>
            <div className="flex-element half-wide">
              <button onClick={saveList}>
              Save Changes (w/o writing to json)
              </button>
            </div>
          </div>

          <div className="settings-row">
            <div className="flex-element">
              <input 
              type="text"
              id="filter-unselect"
              onChange={(event) => setFilterStringUnsel(event.target.value.replace(/\s+/g, "_").toLowerCase())}/>
            </div>
            <div className="flex-element">
              <button
              onClick={pushToSelected}>
              Push filtered onto list -&gt;
              </button>
            </div>
            <div className="flex-element">
              <button
              onClick={pushToUnselected}>
              &lt;- Remove filtered off list
              </button>
            </div>
            <div className="flex-element">
              <input
              id="filter-select"
              onChange={(event) => setFilterStringSel(event.target.value.replace(/\s+/g, "_").toLowerCase())}/>
            </div>
          </div>

          <div className="settings-row">
            <div className="list flex-element">
              {filteredUnselected.map((name) => (
                <div className="list-element" onClick={(e) => {addToList(name)}}>{name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</div>
              ))}
            </div>
            <div className="list flex-element">
              {filteredSelected.map((name) => (
                <div className="list-element" onClick={(e) => {removeFromList(name)}}>{name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</div>
              ))}
            </div>
          </div>
        </div>}
  
      </div>
    </div>
  );
}