async function loadHives() {
  const hives = await get("/hives/");
  const select = document.getElementById("hive");
  const preselect = new URLSearchParams(location.search).get("hive");
  select.innerHTML = hives.map(h =>
    `<option value="${h.id}" ${h.id == preselect ? "selected" : ""}>${h.name} · ${h.location}</option>`
  ).join("");
}

document.getElementById("btn-diagnose").addEventListener("click", async () => {
  const hiveId   = parseInt(document.getElementById("hive").value);
  const duration = parseInt(document.getElementById("duration").value);

  document.getElementById("loader").hidden = false;
  document.getElementById("result").hidden = true;
  document.getElementById("btn-diagnose").disabled = true;

  try {
    const d = await post("/diagnose/", { hive_id: hiveId, duration_seconds: duration });

    document.getElementById("res-title").textContent    = `${d.hive_name} · Résultat`;
    document.getElementById("res-prob").textContent     = `${d.swarming_probability} %`;
    document.getElementById("res-freq").textContent     = `${d.dominant_frequency.toFixed(0)} Hz`;
    document.getElementById("res-stress").textContent   = d.stress_level;
    document.getElementById("res-duration").textContent = `${d.duration_seconds} s`;
    document.getElementById("res-reco").textContent     = d.recommendation;

    document.getElementById("res-prob").className   = d.swarming_probability >= 60 ? "warn" : "";
    document.getElementById("res-stress").className = d.stress_level === "Normal" ? "" : "warn";

    document.getElementById("result").hidden = false;
  } catch (e) {
    console.error(e);
  } finally {
    document.getElementById("loader").hidden = true;
    document.getElementById("btn-diagnose").disabled = false;
  }
});

loadHives().catch(console.error);
