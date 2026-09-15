function Result({ result, form, activeStage, onContinue, reportPayload }) {
  const [drawingType, setDrawingType] = useState("section");
  const [drawingUrl, setDrawingUrl] = useState("");
  const [zoom, setZoom] = useState(1);
  const [exporting, setExporting] = useState("");
  const [exportError, setExportError] = useState("");
  const viewerRef = React.useRef(null);
  const labels = {
    technical: "Τεχνικό φύλλο",
    section: "Μεγάλη διατομή",
    vertical: "Κατακόρυφη όψη",
  };
  useEffect(() => {
    if (activeStage !== 3 || !result?.result) return;
    let active = true;
    setDrawingUrl("");
    setZoom(1);
    fetch(`${API}/api/drawing/${drawingType}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    })
      .then((response) => response.blob())
      .then((blob) => {
        if (active) setDrawingUrl(URL.createObjectURL(blob));
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [drawingType, result, form]);
  const exportReport = async (type, filename) => {
    setExporting(type);
    setExportError("");
    try {
      await download(`/api/project/report/${type}`, filename, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(reportPayload),
      });
    } catch (error) {
      setExportError(error.message || "Η εξαγωγή απέτυχε.");
    } finally {
      setExporting("");
    }
  };
  const r = result?.result;
  if (!r)
    return (
      <div className="workspace">
        <div className="empty">
          Συμπλήρωσε τις παραμέτρους και πάτησε <b>ΥΠΟΛΟΓΙΣΜΟΣ</b>.
        </div>
      </div>
    );
  return (
    <div className="workspace result-workspace">
      <div className="results card result-card">
        {activeStage === 3 && (
          <>
        <div className="card-head">
          <div>
            <span>CALCULATION OUTPUT</span>
            <h2>{r.case}</h2>
          </div>
          <span className="success">
            <ShieldCheck size={14} /> OK
          </span>
        </div>
        <div className="metrics">
          <Metric label="d" value={`${r.d_cm.toFixed(2)} cm`} />
          <Metric
            label="Gunite dimensions"
            value={`${(r.gunite_width_m * 100).toFixed(1)} × ${(r.gunite_height_m * 100).toFixed(1)} cm`}
          />
          <Metric
            label="Διαμήκεις"
            value={`${r.longitudinal_bars_total} τεμ.`}
          />
          <Metric
            label="Gunite volume"
            value={`${r.gunite_volume_m3.toFixed(3)} m³`}
          />
        </div>
        <div className="drawing-preview">
          <div className="preview-toolbar">
            <div>
              <span>ENGINEERING DRAWING</span>
              <h3>{labels[drawingType]}</h3>
            </div>
            <div className="drawing-controls">
              <select
                value={drawingType}
                onChange={(e) => setDrawingType(e.target.value)}
              >
                {Object.entries(labels).map(([value, label]) => (
                  <option value={value} key={value}>
                    {label}
                  </option>
                ))}
              </select>
              <button
                className="icon-button"
                title="Σμίκρυνση"
                onClick={() => setZoom((value) => Math.max(0.5, value - 0.25))}
              >
                <ZoomOut size={16} />
              </button>
              <button
                className="icon-button"
                title="Μεγέθυνση"
                onClick={() => setZoom((value) => Math.min(2.5, value + 0.25))}
              >
                <ZoomIn size={16} />
              </button>
              <button
                className="icon-button"
                title="Επαναφορά μεγέθυνσης"
                onClick={() => setZoom(1)}
              >
                <RotateCcw size={16} />
              </button>
              <button
                className="icon-button"
                title="Πλήρης οθόνη"
                onClick={() => viewerRef.current?.requestFullscreen?.()}
              >
                <Maximize2 size={16} />
              </button>
            </div>
          </div>
          <div className="drawing-canvas" ref={viewerRef}>
            {drawingUrl ? (
              <img
                src={drawingUrl}
                alt="Τεχνικό σχέδιο GUNITE"
                style={{ transform: `scale(${zoom})` }}
              />
            ) : (
              <div className="drawing-loading">Δημιουργία σχεδίου…</div>
            )}
          </div>
        </div>
        <section className="results-section">
          <div className="section-kicker">CALCULATION DETAILS</div>
          <h3>Αποτελέσματα υπολογισμού</h3>
          <p className="section-intro">Οι τιμές που προέκυψαν από τα δεδομένα του στοιχείου και του μανδύα.</p>
        </section>
        <div className="result-table calculation-details">
          {(result.result_table || []).map((row, i) => (
            <Row key={i} a={row["Κατηγορία"]} b={row["Τιμή"]} />
          ))}
        </div>
        <div className="drawing-actions">
          {["section", "vertical", "technical"].map((type) => (
            <button
              className="tool"
              key={type}
              onClick={() => setDrawingType(type)}
            >
              {labels[type]}
            </button>
          ))}
        </div>
        <button className="tool full" onClick={onContinue}>
          Συνέχεια → Παραγγελία
        </button>
          </>
        )}
        {activeStage === 4 && (
        <section className="order-section">
          <div className="section-kicker">BILL OF MATERIALS</div>
          <div className="order-heading">
            <div>
              <h3>Παραγγελία υλικών</h3>
              <p className="section-intro">Τα υλικά και οι ποσότητες που προκύπτουν για την κατασκευή.</p>
            </div>
            <span className="order-count">{(result.order_rows || []).length} γραμμές</span>
          </div>
          <div className="order-table">
            <div className="order-table-head"><span>Περιγραφή</span><span>Προδιαγραφή / θέση</span><span>Ποσότητα</span></div>
            {(result.order_rows || []).map((row, i) => (
              <div className="order-row" key={i}>
                <b>{row.Περιγραφή}</b>
                <small>{row.Τύπος} · {row.Θέση}</small>
                <strong>{row.Τεμάχια} τεμ.</strong>
              </div>
            ))}
          </div>
          <div className="report-actions">
            <button
              className="tool"
              onClick={() => exportReport("excel", "gunite-project.xlsx")}
              disabled={Boolean(exporting)}
            >
              <Download size={16} /> {exporting === "excel" ? "Εξαγωγή Excel…" : "Εξαγωγή Excel"}
            </button>
            <button
              className="tool"
              onClick={() => exportReport("pdf", "gunite-project.pdf")}
              disabled={Boolean(exporting)}
            >
              <Download size={16} /> {exporting === "pdf" ? "Εξαγωγή PDF…" : "Εξαγωγή PDF"}
            </button>
          </div>
          {exportError && <div className="error">{exportError}</div>}
        </section>
        )}
      </div>
    </div>
  );
}
function DrawingViewer({ drawingUrl }) {
  return (
    <div className="drawing-canvas">
      {drawingUrl ? (
        <img src={drawingUrl} alt="Τεχνικό σχέδιο GUNITE" />
      ) : (
        <div className="drawing-loading">Δημιουργία σχεδίου…</div>
      )}
    </div>
  );
}
import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowRight,
  Calculator,
  Download,
  FileText,
  FolderOpen,
  Layers3,
  Maximize2,
  Plus,
  RotateCcw,
  Settings2,
  ShieldCheck,
  Trash2,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import "./styles.css";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const fresh = () => ({
  name: "K1",
  caseType: "4Π",
  x1b: 45,
  x2b: 45,
  y1b: 35,
  y2b: 35,
  fd_mm: 25,
  corner_fd_mm: null,
  x_side_fd_mm: null,
  y_side_fd_mm: null,
  fs_mm: 10,
  spacing_mm: 100,
  a1_cm: 1,
  a2_cm: 0.5,
  tgun_cm: 7.5,
  dh_cm: 5,
  floor_height_m: 3.46,
  waiting_m: 1,
  nx: 3,
  ny: 4,
  overlap_factor: 80,
  development_option: "1a",
  beam: {
    enabled: false,
    side: "Καμία",
    interrupted_bars: 0,
    beam_bottom_m: 1.2,
    beam_height_m: 0.5,
    lower_piece_m: 3,
    upper_piece_m: 2,
  },
  floor_name: "Στάθμη 1",
  study_dimensions: "",
  remarks: "",
  designer_remarks: "",
});
const caseGeometry = (form, key, value) => {
  const next = { ...form, [key]: value };
  if (key === "caseType") {
    if (value === "4Π")
      return {
        ...next,
        x1b: form.x1b || 45,
        x2b: form.x1b || 45,
        y1b: form.y1b || 35,
        y2b: form.y1b || 35,
      };
    if (value === "3Π")
      return {
        ...next,
        x1b: form.x1b || 45,
        x2b: form.x1b || 45,
        y1b: 0,
        y2b: form.y1b || 35,
      };
    return {
      ...next,
      x1b: 0,
      x2b: form.x1b || 45,
      y1b: 0,
      y2b: form.y1b || 35,
    };
  }
  return next;
};
async function api(path, options = {}) {
  const r = await fetch(API + path, options);
  const content = r.headers.get("content-type") || "";
  const data = content.includes("json") ? await r.json() : await r.blob();
  if (!r.ok) throw Error(data.detail || "Σφάλμα");
  return data;
}
async function download(path, filename, options) {
  const blob = await api(path, options);
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
function FloorSelector({ floors, value, onChange }) {
  return (
    <label className="field floor-selector">
      <span>Στάθμη υπολογισμού</span>
      <select
        value={value || ""}
        onChange={(e) => {
          const floor = floors.find((item) => item.name === e.target.value);
          if (floor) onChange(floor);
        }}
      >
        <option value="" disabled>
          Επίλεξε στάθμη
        </option>
        {floors.map((floor, index) => (
          <option value={floor.name} key={`${floor.name}-${index}`}>
            {floor.name}
          </option>
        ))}
      </select>
    </label>
  );
}
function Num({ label, value, onChange, step = 0.1, min }) {
  const floorControl =
    label === "tgun (cm)" ? (
      <FloorSelector
        floors={window.__guniteFloors || []}
        value={window.__guniteFloorName}
        onChange={(floor) =>
          window.dispatchEvent(
            new CustomEvent("gunite:select-floor", { detail: floor }),
          )
        }
      />
    ) : null;
  return (
    <>
      {floorControl}
      <label className="field">
        <span>{label}</span>
        <input
          type="number"
          value={value ?? ""}
          step={step}
          min={min}
          onChange={(e) =>
            onChange(e.target.value === "" ? null : Number(e.target.value))
          }
        />
      </label>
    </>
  );
}
function App() {
  const [form, setForm] = useState(fresh),
    [result, setResult] = useState(null),
    [view, setView] = useState("calculation"),
    [tab, setTab] = useState("geometry"),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(false),
    [editingIndex, setEditingIndex] = useState(null),
    [showHome, setShowHome] = useState(true),
    [activeStage, setActiveStage] = useState(2);
  const [project, setProject] = useState({
    name: "Νέο έργο",
    id: null,
    floors: [{ name: "Στάθμη 1", height: 3.46, tgun: 7.5, a1: 1, a2: 0.5 }],
    elements: [],
  });
  const set = (key, value) =>
    setForm((f) =>
      key === "caseType" ? caseGeometry(f, key, value) : { ...f, [key]: value },
    );
  const setBeam = (key, value) =>
    setForm((f) => ({ ...f, beam: { ...f.beam, [key]: value } }));
  useEffect(() => {
    const addFloor = () =>
      setProject((p) => ({
        ...p,
        floors: [
          ...p.floors,
          {
            name: `Στάθμη ${p.floors.length + 1}`,
            height: 3.46,
            tgun: 7.5,
            a1: 1,
            a2: 0.5,
          },
        ],
      }));
    const updateFloor = (e) =>
      setProject((p) => {
        const oldFloor = p.floors[e.detail.index];
        const nextFloor = e.detail.value;
        setForm((current) =>
          current.floor_name === (oldFloor?.name || "Στάθμη 1")
            ? {
                ...current,
                floor_name: nextFloor.name,
                floor_height_m: nextFloor.height,
                tgun_cm: nextFloor.tgun,
                a1_cm: nextFloor.a1,
                a2_cm: nextFloor.a2,
              }
            : current,
        );
        return {
          ...p,
          floors: p.floors.map((floor, index) =>
            index === e.detail.index ? nextFloor : floor,
          ),
          elements:
            oldFloor?.name === nextFloor.name
              ? p.elements
              : p.elements.map((item) =>
                  (item.floor_name || "Στάθμη 1") === oldFloor.name
                    ? { ...item, floor_name: nextFloor.name }
                    : item,
                ),
        };
      });
    const selectFloor = (e) =>
      setForm((current) => ({
        ...current,
        floor_name: e.detail.name,
        floor_height_m: e.detail.height,
        tgun_cm: e.detail.tgun,
        a1_cm: e.detail.a1,
        a2_cm: e.detail.a2,
      }));
    window.addEventListener("gunite:add-floor", addFloor);
    window.addEventListener("gunite:update-floor", updateFloor);
    window.addEventListener("gunite:select-floor", selectFloor);
    return () => {
      window.removeEventListener("gunite:add-floor", addFloor);
      window.removeEventListener("gunite:update-floor", updateFloor);
      window.removeEventListener("gunite:select-floor", selectFloor);
    };
  }, []);
  const calculate = async (supplied) => {
    setLoading(true);
    setError("");
    try {
      const nextResult = await api("/api/calculate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(supplied || form),
        });
      setResult(nextResult);
      setActiveStage(3);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };
  const addElement = () => {
    setProject((p) => {
      const elements = [...p.elements];
      if (editingIndex === null) elements.push({ ...form });
      else elements[editingIndex] = { ...form };
      return { ...p, elements };
    });
    setEditingIndex(null);
    setView("elements");
  };
  const openElement = (element, index) => {
    const input = element.input || element;
    const caseType =
      input.y1b === 0 && input.x1b > 0 && input.x2b > 0 && input.y2b > 0
        ? "3Π"
        : input.x1b === 0 && input.y1b === 0
          ? "2Π"
          : "4Π";
    setEditingIndex(index);
    setForm({ ...fresh(), ...input, caseType });
    setResult(
      element.result
        ? {
            input,
            result: element.result,
            result_table: element.result_table,
            order_rows: element.order_rows,
          }
        : { ...result },
    );
    setView("calculation");
    if (!element.result) calculate(input);
  };
  const deleteElement = (i) =>
    setProject((p) => ({
      ...p,
      elements: p.elements.filter((_, index) => index !== i),
    }));
  const updateFloor = (index, nextFloor) =>
    setProject((p) => {
      const oldFloor = p.floors[index];
      setForm((current) =>
        current.floor_name === (oldFloor?.name || "Στάθμη 1")
          ? {
              ...current,
              floor_name: nextFloor.name,
              floor_height_m: nextFloor.height,
              tgun_cm: nextFloor.tgun,
              a1_cm: nextFloor.a1,
              a2_cm: nextFloor.a2,
            }
          : current,
      );
      return {
        ...p,
        floors: p.floors.map((floor, floorIndex) =>
          floorIndex === index ? nextFloor : floor,
        ),
        elements:
          oldFloor?.name === nextFloor.name
            ? p.elements
            : p.elements.map((item) =>
                (item.floor_name || "Στάθμη 1") === oldFloor.name
                  ? { ...item, floor_name: nextFloor.name }
                  : item,
              ),
      };
    });
  const addFloor = () =>
    setProject((p) => ({
      ...p,
      floors: [
        ...p.floors,
        {
          name: `Στάθμη ${p.floors.length + 1}`,
          height: 3.46,
          tgun: 7.5,
          a1: 1,
          a2: 0.5,
        },
      ],
    }));
  const newElement = () => {
    setForm((current) => ({
      ...fresh(),
      floor_name: current.floor_name,
      floor_height_m: current.floor_height_m,
      tgun_cm: current.tgun_cm,
      a1_cm: current.a1_cm,
      a2_cm: current.a2_cm,
    }));
    setResult(null);
    setShowHome(false);
    setView("calculation");
  };
  const newFloor = () =>
    setProject((p) => ({
      ...p,
      floors: [
        ...p.floors,
        {
          name: `Στάθμη ${p.floors.length + 1}`,
          height: 3.46,
          tgun: 7.5,
          a1: 1,
          a2: 0.5,
        },
      ],
    }));
  window.__guniteFloors = project.floors;
  window.__guniteFloorName = form.floor_name;
  if (showHome)
    return (
      <Landing
        onNew={() => {
          setProject({
            name: "Νέο έργο",
            id: null,
            floors: [
              { name: "Στάθμη 1", height: 3.46, tgun: 7.5, a1: 1, a2: 0.5 },
            ],
            elements: [],
          });
          newElement();
        }}
      />
    );
  return (
    <div className="app">
      <aside className="side">
        <div className="brand">
          <div className="logo">G</div>
          <div>
            <b>GUNITE</b>
            <small>ENGINEERING CALCULATOR</small>
          </div>
        </div>
        <div className="project">
          <span>PROJECT</span>
          <strong>{project.name}</strong>
          <small>
            {project.elements.length} στοιχεία · {project.floors.length} στάθμες
          </small>
        </div>
        <nav>
          <button
            className={view === "calculation" ? "active" : ""}
            onClick={() => setView("calculation")}
          >
            <Calculator size={17} /> Υπολογισμός
          </button>
          <button
            className={view === "elements" ? "active" : ""}
            onClick={() => setView("elements")}
          >
            <Layers3 size={17} /> Στοιχεία / στάθμες
          </button>
          <button
            className={view === "reports" ? "active" : ""}
            onClick={() => setView("reports")}
          >
            <FileText size={17} /> Reports
          </button>
          <button
            className={view === "catalog" ? "active" : ""}
            onClick={() => setView("catalog")}
          >
            <Settings2 size={17} /> Κατάλογος
          </button>
        </nav>
        <div className="side-bottom">
          <ShieldCheck size={16} /> Python calculation engine
        </div>
      </aside>
      <main>
        <header>
          <div>
            <div className="eyebrow">GUNITE / PROJECT WORKSPACE</div>
            <h1>
              {view === "calculation"
                ? "Υπολογισμός μανδύα"
                : view === "elements"
                  ? "Στοιχεία και στάθμες"
                  : view === "reports"
                    ? "Αναφορές έργου"
                    : "Κατάλογος υλικών"}
            </h1>
            <p>
              Πλήρες workflow έργου και όλοι οι υπολογισμοί της μηχανής GUNITE.
            </p>
          </div>
          <div className="header-status">
            <span className="dot" /> ENGINE ONLINE
          </div>
        </header>
        <div className="toolbar">
          <label className="field">
            <span>Όνομα έργου</span>
            <input
              value={project.name}
              onChange={(e) =>
                setProject((p) => ({ ...p, name: e.target.value }))
              }
            />
          </label>
        </div>
        {error && <div className="error">{error}</div>}
        {view === "calculation" ? (
          <Calculation
            form={form}
            set={set}
            setBeam={setBeam}
            tab={tab}
            setTab={setTab}
            calculate={() => calculate()}
            loading={loading}
            result={result}
            addElement={addElement}
            floors={project.floors}
            project={project}
            activeStage={activeStage}
            setActiveStage={setActiveStage}
          />
        ) : view === "elements" ? (
          <Elements
            project={project}
            onOpen={openElement}
            onDelete={deleteElement}
            onNew={newElement}
            onUpdateFloor={updateFloor}
          />
        ) : view === "reports" ? (
          <Reports project={project} />
        ) : (
          <Catalog />
        )}
      </main>
    </div>
  );
}
function Calculation({
  form,
  set,
  setBeam,
  tab,
  setTab,
  calculate,
  loading,
  result,
  addElement,
  floors,
  project,
  activeStage,
  setActiveStage,
}) {
  const r = result?.result;
  const availableFloors = floors || window.__guniteFloors || [];
  const applyFloor = (floor) => {
    set("floor_name", floor.name);
    set("floor_height_m", floor.height);
    set("tgun_cm", floor.tgun);
    set("a1_cm", floor.a1);
    set("a2_cm", floor.a2);
  };
  return (
    <>
      <div className="calculation-flow" aria-label="Ροή υπολογισμού">
        <div className={activeStage > 1 ? "flow-node active" : "flow-node primary"}><span>01</span> Εισαγωγή δεδομένων</div>
        <div className="flow-arrow">→</div>
        <div className={activeStage > 2 ? "flow-node active" : activeStage === 2 ? "flow-node primary" : "flow-node"}><span>02</span> Υπολογισμός</div>
        <div className="flow-arrow">→</div>
        <div className={activeStage > 3 ? "flow-node active" : activeStage === 3 ? "flow-node primary" : "flow-node"}><span>03</span> Αποτελέσματα</div>
        <div className="flow-arrow">→</div>
        <div className={activeStage === 4 ? "flow-node primary" : "flow-node"}><span>04</span> Παραγγελία</div>
      </div>
      <section className="layout">
        <div className="panel input-panel">
          <div className="panel-title">
            <div>
              <h2>Παράμετροι</h2>
              <span>Γεωμετρία, οπλισμός και τεχνικές λεπτομέρειες</span>
            </div>
          </div>
          <div className="tabs">
            <button
              className={tab === "geometry" ? "sel" : ""}
              onClick={() => setTab("geometry")}
            >
              Γεωμετρία
            </button>
            <button
              className={tab === "steel" ? "sel" : ""}
              onClick={() => setTab("steel")}
            >
              Οπλισμός
            </button>
            <button
              className={tab === "beam" ? "sel" : ""}
              onClick={() => setTab("beam")}
            >
              Λεπτομέρειες
            </button>
          </div>
          {tab === "geometry" && (
            <div className="section">
              <div className="input-group existing-group">
                <h3>Στοιχεία υφιστάμενου στοιχείου</h3>
                <p className="input-help">Τα γεωμετρικά δεδομένα και η μορφή του υφιστάμενου στοιχείου.</p>
              <label className="field">
                <span>Όνομα</span>
                <input
                  value={form.name}
                  onChange={(e) => set("name", e.target.value)}
                />
              </label>
              <label className="field">
                <span>Πλευρές μανδύα</span>
                <select
                  value={form.caseType}
                  onChange={(e) => set("caseType", e.target.value)}
                >
                  <option value="4Π">4Π · τετραπλεύρος</option>
                  <option value="3Π">3Π · ελεύθερη κάτω πλευρά</option>
                  <option value="2Π">2Π · γωνιακός</option>
                </select>
              </label>
              <div className="grid2">
                <Num
                  label="X1b (cm)"
                  value={form.x1b}
                  onChange={(v) => set("x1b", v)}
                />
                <Num
                  label="X2b (cm)"
                  value={form.x2b}
                  onChange={(v) => set("x2b", v)}
                />
                <Num
                  label="Y1b (cm)"
                  value={form.y1b}
                  onChange={(v) => set("y1b", v)}
                />
                <Num
                  label="Y2b (cm)"
                  value={form.y2b}
                  onChange={(v) => set("y2b", v)}
                />
              </div>
              </div>
              <div className="input-group cover-group">
                <h3>Στοιχεία μανδύα</h3>
                <p className="input-help">Οι διαστάσεις και οι κατασκευαστικές παράμετροι του μανδύα.</p>
              <div className="grid2">
                <Num
                  label="tgun (cm)"
                  value={form.tgun_cm}
                  onChange={(v) => set("tgun_cm", v)}
                />
                <Num
                  label="dh (cm)"
                  value={form.dh_cm}
                  onChange={(v) => set("dh_cm", v)}
                />
                <Num
                  label="a1 (cm)"
                  value={form.a1_cm}
                  onChange={(v) => set("a1_cm", v)}
                />
                <Num
                  label="a2 (cm)"
                  value={form.a2_cm}
                  onChange={(v) => set("a2_cm", v)}
                />
                <Num
                  label="Ύψος ορόφου (m)"
                  value={form.floor_height_m}
                  onChange={(v) => set("floor_height_m", v)}
                />
                <Num
                  label="Αναμονή (m)"
                  value={form.waiting_m}
                  onChange={(v) => set("waiting_m", v)}
                />
              </div>
              {form.caseType === "4Π" && (
                <div className="option-row">
                  <span>Ανάπτυξη 4Π</span>
                  <button
                    className={
                      form.development_option === "1a"
                        ? "option active"
                        : "option"
                    }
                    onClick={() => set("development_option", "1a")}
                  >
                    1a
                  </button>
                  <button
                    className={
                      form.development_option === "1b"
                        ? "option active"
                        : "option"
                    }
                    onClick={() => set("development_option", "1b")}
                  >
                    1b
                  </button>
                </div>
              )}
              </div>
            </div>
          )}
          {tab === "steel" && (
            <div className="section">
              <h3>Οπλισμός</h3>
              <p className="input-help">Οι διάμετροι, οι αποστάσεις και η διάταξη του οπλισμού.</p>
              <div className="grid2">
                <Num
                  label="Φd (mm)"
                  value={form.fd_mm}
                  onChange={(v) => set("fd_mm", v)}
                />
                <Num
                  label="Φs (mm)"
                  value={form.fs_mm}
                  onChange={(v) => set("fs_mm", v)}
                />
                <Num
                  label="s (mm)"
                  value={form.spacing_mm}
                  step={10}
                  onChange={(v) => set("spacing_mm", v)}
                />
                <Num
                  label="Υπερκάλυψη ×Φd"
                  value={form.overlap_factor}
                  onChange={(v) => set("overlap_factor", v)}
                />
                <Num
                  label="nx"
                  value={form.nx}
                  step={1}
                  min={1}
                  onChange={(v) => set("nx", v)}
                />
                <Num
                  label="ny"
                  value={form.ny}
                  step={1}
                  min={1}
                  onChange={(v) => set("ny", v)}
                />
              </div>
              <div className="grid3">
                <Num
                  label="Γωνίες Φ"
                  value={form.corner_fd_mm}
                  step={1}
                  onChange={(v) => set("corner_fd_mm", v)}
                />
                <Num
                  label="Πλευρές X Φ"
                  value={form.x_side_fd_mm}
                  step={1}
                  onChange={(v) => set("x_side_fd_mm", v)}
                />
                <Num
                  label="Πλευρές Y Φ"
                  value={form.y_side_fd_mm}
                  step={1}
                  onChange={(v) => set("y_side_fd_mm", v)}
                />
              </div>
            </div>
          )}
          {tab === "beam" && (
            <div className="section">
              <h3>Λεπτομέρειες κατασκευής</h3>
              <p className="input-help">Προαιρετικές παράμετροι για δοκό ή κατασκευαστικό εμπόδιο.</p>
              <div className="toggle">
                <b>Ενεργοποίηση δοκού / εμποδίου</b>
                <input
                  type="checkbox"
                  checked={form.beam.enabled}
                  onChange={(e) => setBeam("enabled", e.target.checked)}
                />
              </div>
              {form.beam.enabled && (
                <div className="grid2">
                  <label className="field">
                    <span>Πλευρά</span>
                    <select
                      value={form.beam.side}
                      onChange={(e) => setBeam("side", e.target.value)}
                    >
                      <option>Αριστερά</option>
                      <option>Δεξιά</option>
                      <option>Κάτω</option>
                      <option>Πάνω</option>
                    </select>
                  </label>
                  <Num
                    label="Διακοπτόμενες"
                    value={form.beam.interrupted_bars}
                    step={1}
                    onChange={(v) => setBeam("interrupted_bars", v)}
                  />
                  <Num
                    label="Κάτω στάθμη (m)"
                    value={form.beam.beam_bottom_m}
                    onChange={(v) => setBeam("beam_bottom_m", v)}
                  />
                  <Num
                    label="Ύψος δοκού (m)"
                    value={form.beam.beam_height_m}
                    onChange={(v) => setBeam("beam_height_m", v)}
                  />
                </div>
              )}
            </div>
          )}
          <button className="calculate" onClick={calculate} disabled={loading}>
            {loading ? "Υπολογισμός…" : "ΥΠΟΛΟΓΙΣΜΟΣ"}
          </button>
          {r && (
            <button className="tool full" onClick={addElement}>
              <Plus size={16} /> Προσθήκη στο έργο
            </button>
          )}
        </div>
        {activeStage >= 3 && (
          <Result
            result={result}
            form={form}
            activeStage={activeStage}
            onContinue={() => setActiveStage(4)}
            reportPayload={{
              name: project.name,
              floors: project.floors,
              elements: [result.input],
            }}
          />
        )}
      </section>
    </>
  );
}

function Landing({ onNew }) {
  return (
    <div className="landing">
      <div className="landing-top">
        <div className="brand large">
          <div className="logo">G</div>
          <div>
            <b>GUNITE</b>
            <small>ENGINEERING CALCULATOR</small>
          </div>
        </div>
        <span className="landing-status">
          <span className="dot" /> ENGINE ONLINE
        </span>
      </div>
      <div className="landing-hero">
        <div className="landing-copy">
          <div className="eyebrow">STRUCTURAL STRENGTHENING WORKSPACE</div>
          <h1>Υπολόγισε, οργάνωσε και τεκμηρίωσε κάθε μανδύα.</h1>
          <p>
            Ένα ενιαίο περιβάλλον για έργα, στάθμες, κολώνες, οπλισμό,
            προμέτρηση και τεχνικές αναφορές.
          </p>
          <button className="primary-action" onClick={onNew}>
            <Plus size={18} /> Νέο έργο <ArrowRight size={17} />
          </button>
        </div>
        <div className="landing-diagram">
          <div className="diagram-outer">
            <div className="diagram-inner"></div>
            <span className="diagram-label">GUNITE</span>
          </div>
          <div className="diagram-line line-one"></div>
          <div className="diagram-line line-two"></div>
          <span className="diagram-note note-one">4Π / 3Π / 2Π</span>
          <span className="diagram-note note-two">Υπολογισμός διατομής</span>
        </div>
      </div>
      <section className="landing-console">
        <div className="landing-console-item">
          <span className="eyebrow">CALCULATION WORKSPACE</span>
          <strong>Νέο stateless engineering session</strong>
          <small>Οι υπολογισμοί και τα reports δημιουργούνται για την τρέχουσα συνεδρία.</small>
        </div>
        <div className="landing-console-item muted">
          <span className="eyebrow">PROJECT STORAGE</span>
          <strong>Χωρίς server-side αποθήκευση</strong>
          <small>Δεν εμφανίζονται ψεύτικα saved projects ή μη λειτουργικά open/save actions.</small>
        </div>
      </section>
      <div className="landing-footer">
        <span>GUNITE Logic · 4Π cases 1a / 1b</span>
        <span>Python calculation engine</span>
      </div>
    </div>
  );
}
function LegacyResult({ result, form }) {
  const [drawingType, setDrawingType] = useState("technical");
  const [drawingUrl, setDrawingUrl] = useState("");
  useEffect(() => {
    if (!result?.result) return;
    let active = true;
    setDrawingUrl("");
    fetch(`${API}/api/drawing/${drawingType}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    })
      .then((response) => response.blob())
      .then((blob) => {
        if (active) setDrawingUrl(URL.createObjectURL(blob));
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [drawingType, result, form]);
  const r = result?.result;
  if (!r)
    return (
      <div className="workspace">
        <div className="empty">
          Συμπλήρωσε τις παραμέτρους και πάτησε <b>ΥΠΟΛΟΓΙΣΜΟΣ</b>.
        </div>
      </div>
    );
  return (
    <div className="workspace">
      <div className="results card">
        <div className="card-head">
          <div>
            <span>CALCULATION OUTPUT</span>
            <h2>{r.case}</h2>
          </div>
          <span className="success">
            <ShieldCheck size={14} /> OK
          </span>
        </div>
        <div className="metrics">
          <Metric label="d" value={`${r.d_cm.toFixed(2)} cm`} />
          <Metric
            label="Gunite"
            value={`${(r.gunite_width_m * 100).toFixed(1)} × ${(r.gunite_height_m * 100).toFixed(1)} cm`}
          />
          <Metric
            label="Διαμήκεις"
            value={`${r.longitudinal_bars_total} τεμ.`}
          />
          <Metric
            label="Gunite"
            value={`${r.gunite_volume_m3.toFixed(3)} m³`}
          />
        </div>
        <div className="drawing-preview">
          <div className="preview-toolbar">
            <div>
              <span>TECHNICAL PREVIEW</span>
              <h3>Σχέδιο που δημιουργήθηκε</h3>
            </div>
            <select
              value={drawingType}
              onChange={(e) => setDrawingType(e.target.value)}
            >
              <option value="technical">Τεχνικό φύλλο</option>
              <option value="section">Διατομή</option>
              <option value="vertical">Κατακόρυφη όψη</option>
            </select>
          </div>
          {drawingUrl ? (
            <img src={drawingUrl} alt="Τεχνικό σχέδιο GUNITE" />
          ) : (
            <div className="drawing-loading">Δημιουργία σχεδίου…</div>
          )}
        </div>
        <div className="result-table">
          {(result.result_table || []).map((row, i) => (
            <Row key={i} a={row["Κατηγορία"]} b={row["Τιμή"]} />
          ))}
        </div>
        <div className="drawing-actions">
          {["section", "vertical", "technical"].map((type) => (
            <button
              className="tool"
              key={type}
              onClick={() =>
                download(`/api/drawing/${type}`, `${form.name}-${type}.png`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify(form),
                })
              }
            >
              <Download size={14} /> Λήψη {type}
            </button>
          ))}
        </div>
        <h3>Παραγγελία</h3>
        {(result.order_rows || []).map((row, i) => (
          <div className="order-row" key={i}>
            <div>
              <b>{row.Περιγραφή}</b>
              <small>
                {row.Τύπος} · {row.Θέση}
              </small>
            </div>
            <strong>{row.Τεμάχια} τεμ.</strong>
          </div>
        ))}
      </div>
    </div>
  );
}
function FloorEditor({ floor, index, onUpdateFloor, onSelectFloor }) {
  const [draft, setDraft] = useState(floor);
  useEffect(() => setDraft(floor), [floor]);
  const update = (key, value) => {
    const next = { ...draft, [key]: value };
    setDraft(next);
    onUpdateFloor(index, next);
  };
  const select = () => onSelectFloor(draft);
  return (
    <div className="floor-editor">
      <div className="floor-editor-top">
        <label className="field">
          <span>Όνομα στάθμης</span>
          <input
            value={draft.name || ""}
            onChange={(e) => update("name", e.target.value)}
          />
        </label>
        <button className="tool floor-select" onClick={select}>
          Χρήση στον υπολογισμό
        </button>
      </div>
      <div className="floor-fields">
        <Num
          label="Ύψος (m)"
          value={draft.height}
          step={0.01}
          min={0.01}
          onChange={(v) => update("height", v)}
        />
        <Num
          label="tgun (cm)"
          value={draft.tgun}
          step={0.5}
          min={0}
          onChange={(v) => update("tgun", v)}
        />
        <Num
          label="a1 (cm)"
          value={draft.a1}
          step={0.1}
          min={0}
          onChange={(v) => update("a1", v)}
        />
        <Num
          label="a2 (cm)"
          value={draft.a2}
          step={0.1}
          min={0}
          onChange={(v) => update("a2", v)}
        />
      </div>
    </div>
  );
}
function Elements({
  project,
  onOpen,
  onDelete,
  onNew,
  onAddFloor,
  onUpdateFloor,
}) {
  const addFloor =
    onAddFloor || (() => window.dispatchEvent(new Event("gunite:add-floor")));
  const selectFloor = (floor) =>
    window.dispatchEvent(
      new CustomEvent("gunite:select-floor", { detail: floor }),
    );
  return (
    <div className="card table-card">
      <div className="card-head">
        <div>
          <span>PROJECT STRUCTURE</span>
          <h2>Στάθμες και στοιχεία</h2>
        </div>
        <div className="report-actions">
          <button className="tool" onClick={addFloor}>
            + Νέα στάθμη
          </button>
          <button className="tool" onClick={onNew}>
            <Plus size={15} /> Νέο στοιχείο
          </button>
        </div>
      </div>
      {project.floors.map((floor, index) => (
        <section className="floor" key={`${floor.name}-${index}`}>
          <h3>{floor.name}</h3>
          <FloorEditor
            floor={floor}
            index={index}
            onUpdateFloor={onUpdateFloor}
            onSelectFloor={selectFloor}
          />
          {project.elements.map(
            (item, itemIndex) =>
              (item.floor_name || "Στάθμη 1") === floor.name && (
                <div className="element-row" key={`${item.name}-${itemIndex}`}>
                  <span>
                    <b>{item.name}</b>
                    <small>
                      {item.x1b}/{item.x2b} × {item.y1b}/{item.y2b} cm · Φ
                      {item.fd_mm}
                    </small>
                  </span>
                  <button
                    className="icon-button"
                    onClick={() => onOpen(item, itemIndex)}
                  >
                    <FolderOpen size={16} />
                  </button>
                  <button
                    className="icon-button danger"
                    onClick={() => onDelete(itemIndex)}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ),
          )}
        </section>
      ))}
      {!project.elements.length && (
        <div className="empty">Δεν υπάρχουν στοιχεία στο έργο.</div>
      )}
    </div>
  );
}
function Reports({ project }) {
  return (
    <div className="card report-card">
      <div className="card-head">
        <div>
          <span>EXPORT CENTER</span>
          <h2>Αναφορές και αρχεία έργου</h2>
        </div>
        <FileText size={20} />
      </div>
      <p>
        Πλήρης συγκεντρωτική παραγγελία, τεχνικοί υπολογισμοί, Excel και PDF.
      </p>
      <div className="report-actions">
        <button
          className="tool"
          onClick={() =>
            download("/api/project/report/excel", "gunite-project.xlsx", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(project),
            })
          }
        >
          <Download size={16} /> Excel
        </button>
        <button
          className="tool"
          onClick={() =>
            download("/api/project/report/pdf", "gunite-project.pdf", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(project),
            })
          }
        >
          <Download size={16} /> PDF
        </button>
      </div>
    </div>
  );
}
function Catalog() {
  const [data, setData] = useState({ items: [] });
  useEffect(() => {
    api("/api/catalog")
      .then(setData)
      .catch(() => {});
  }, []);
  return (
    <div className="card table-card">
      <div className="card-head">
        <div>
          <span>CATALOG</span>
          <h2>Κατάλογος πραγματικών προϊόντων</h2>
        </div>
      </div>
      <div className="catalog-grid">
        {data.items.map((item, i) => (
          <div className="catalog-item" key={i}>
            <b>{item.name}</b>
            <span>
              Φ{item.diameter_mm} · s={item.spacing_mm} mm
            </span>
            <small>
              {item.development_m.toFixed(2)} m · {item.weight_kg.toFixed(2)} kg
            </small>
          </div>
        ))}
      </div>
    </div>
  );
}
function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <b>{value}</b>
    </div>
  );
}
function Row({ a, b }) {
  return (
    <div className="row">
      <span>{a}</span>
      <b>{b}</b>
    </div>
  );
}
createRoot(document.getElementById("root")).render(<App />);
