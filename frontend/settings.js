const DEFAULTS = {
  freq_warning: 260, freq_critical: 280,
  temp_warning: 36,  temp_critical: 38,
  humidity_min: 50,  humidity_max: 80,
  weight_drop_threshold: 2,
};

async function load() {
  const s = await get("/settings/");
  document.getElementById("inp-freq-warning").value  = s.freq_warning;
  document.getElementById("inp-freq-critical").value = s.freq_critical;
  document.getElementById("inp-temp-warning").value  = s.temp_warning;
  document.getElementById("inp-humidity-max").value  = s.humidity_max;
}

function feedback(msg, ok) {
  const el = document.getElementById("save-feedback");
  el.textContent = msg;
  el.style.color = ok ? "var(--green, #2D6A4F)" : "var(--red, #E63946)";
  setTimeout(() => el.textContent = "", 2500);
}

document.getElementById("btn-save").addEventListener("click", async () => {
  try {
    await put("/settings/", {
      ...DEFAULTS,
      freq_warning:  parseFloat(document.getElementById("inp-freq-warning").value),
      freq_critical: parseFloat(document.getElementById("inp-freq-critical").value),
      temp_warning:  parseFloat(document.getElementById("inp-temp-warning").value),
      humidity_max:  parseFloat(document.getElementById("inp-humidity-max").value),
    });
    feedback("Paramètres enregistrés ✓", true);
  } catch {
    feedback("Erreur lors de la sauvegarde", false);
  }
});

document.getElementById("btn-reset").addEventListener("click", async () => {
  try {
    await put("/settings/", DEFAULTS);
    load();
    feedback("Valeurs réinitialisées ✓", true);
  } catch {
    feedback("Erreur lors de la réinitialisation", false);
  }
});

load().catch(console.error);
