function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const min  = Math.floor(diff / 60000);
  if (min < 1)  return "À l'instant";
  if (min < 60) return `Il y a ${min} min`;
  const h = Math.floor(min / 60);
  if (h < 24)   return `Il y a ${h}h`;
  return new Date(iso).toLocaleDateString("fr-FR", { day: "numeric", month: "long" });
}

function barClass(severity) {
  return { critical: "alert", warning: "warn", info: "info" }[severity] || "ok";
}

function severityLabel(severity) {
  return { critical: "Alerte critique", warning: "Avertissement", info: "Info" }[severity] || severity;
}

function groupByDay(alerts) {
  const groups = {};
  for (const a of alerts) {
    const day = new Date(a.timestamp).toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" });
    if (!groups[day]) groups[day] = [];
    groups[day].push(a);
  }
  return groups;
}

async function load() {
  const alerts = await get("/alerts/");
  const el = document.getElementById("event-list");

  if (alerts.length === 0) {
    el.innerHTML = `<p style="padding:1.5rem;color:var(--muted,#888)">Aucune alerte enregistrée.</p>`;
    return;
  }

  const groups = groupByDay(alerts);
  el.innerHTML = Object.entries(groups).map(([day, items]) => `
    <section class="day">
      <h2>${day}</h2>
      ${items.map(a => `
        <article class="event">
          <span class="event-bar ${barClass(a.severity)}"></span>
          <div class="event-body">
            <h3>${severityLabel(a.severity)} — Ruche n°${a.hive_id}</h3>
            <p>${a.message}</p>
            <time>${timeAgo(a.timestamp)}</time>
          </div>
        </article>`).join("")}
    </section>`).join("");
}

load().catch(console.error);
