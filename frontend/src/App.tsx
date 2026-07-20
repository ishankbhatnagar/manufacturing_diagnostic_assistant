import { useState } from "react";
import "./App.css";
import TechnicianView from "./views/TechnicianView";
import ExpertView from "./views/ExpertView";

type Tab = "technician" | "expert";

function App() {
  const [tab, setTab] = useState<Tab>("technician");

  return (
    <div className="app">
      <header className="app-header">
        <h1>Manufacturing Diagnostic Assistant</h1>
        <nav className="tabs">
          <button
            className={tab === "technician" ? "tab tab-active" : "tab"}
            onClick={() => setTab("technician")}
          >
            Technician
          </button>
          <button
            className={tab === "expert" ? "tab tab-active" : "tab"}
            onClick={() => setTab("expert")}
          >
            Expert dashboard
          </button>
        </nav>
      </header>
      <main>{tab === "technician" ? <TechnicianView /> : <ExpertView />}</main>
    </div>
  );
}

export default App;
