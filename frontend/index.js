const STATUS_DOT   = { normal: "green", warning: "orange", critical: "red" };
const STATUS_LABEL = { normal: "État normal", warning: "Risque d'essaimage", critical: "Alerte critique" };

async function load() {
  const [hives, alerts] = await Promise.all([get("/hives/"), get("/alerts/")]);

  document.getElementById("hive-count").textContent = `${hives.length} ruches surveillées`;

  // Bannière alerte critique
  const critical = alerts.filter(a => a.severity === "critical");
  const banner = document.getElementById("alert-banner");
  if (critical.length > 0) {
    const a = critical[0];
    banner.querySelector("strong").textContent = `Alerte IA · Ruche n°${a.hive_id}`;
    banner.querySelector("p").textContent = a.message;
    banner.hidden = false;
  } else {
    banner.hidden = true;
  }

  // KPIs — moyenne des dernières lectures
  const withReading = hives.filter(h => h.last_reading);
  if (withReading.length > 0) {
    const avg = key => withReading.reduce((s, h) => s + h.last_reading[key], 0) / withReading.length;
    document.getElementById("kpi-freq").textContent = `${avg("frequency_hz").toFixed(0)} Hz`;
    document.getElementById("kpi-temp").textContent = `${avg("temperature_c").toFixed(1)}°C`;
    document.getElementById("kpi-humidity").textContent = `${avg("humidity_pct").toFixed(0)}%`;
  }

  // Liste des ruches
  document.getElementById("hive-list").innerHTML = hives.map(h => {
    const r = h.last_reading;
    const color = STATUS_DOT[h.status] || "green";
    const label = r
      ? `${r.frequency_hz.toFixed(0)} Hz · ${r.temperature_c.toFixed(1)}°C · ${STATUS_LABEL[h.status]}`
      : STATUS_LABEL[h.status];
    return `
      <a href="map.html" class="row">
        <span class="dot dot-${color}"></span>
        <div>
          <strong>${h.name} · ${h.location}</strong>
          <small>${label}</small>
        </div>
      </a>`;
  }).join("");
}

load().catch(console.error);
