const STATUS_COLOR = { normal: "green", warning: "orange", critical: "red" };
const STATUS_BADGE = { normal: "badge-green", warning: "badge-orange", critical: "badge-red" };
const STATUS_LABEL = { normal: "Normal", warning: "Essaimage", critical: "Alerte" };

async function load() {
  const hives = await get("/hives/");

  const alertCount = hives.filter(h => h.status !== "normal").length;
  document.getElementById("hive-summary").textContent =
    `${hives.length} ruches · ${alertCount} alerte${alertCount > 1 ? "s" : ""}`;

  document.getElementById("hive-grid").innerHTML = hives.map(h => {
    const r = h.last_reading;
    const color = STATUS_COLOR[h.status] || "green";
    const badge = STATUS_BADGE[h.status] || "badge-green";
    const label = STATUS_LABEL[h.status] || "Normal";
    const freq = r ? `${r.frequency_hz.toFixed(0)} Hz` : "—";
    const env  = r ? `${r.temperature_c.toFixed(1)}°C · ${r.humidity_pct.toFixed(0)}%` : "—";
    return `
      <a href="diag?hive=${h.id}" class="hive ${color}">
        <header><span class="badge ${badge}">${label}</span></header>
        <h3>${h.name}</h3>
        <p>${freq}</p>
        <p>${env}</p>
      </a>`;
  }).join("");
}

load().catch(console.error);
