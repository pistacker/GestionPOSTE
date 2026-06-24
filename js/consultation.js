import { getActivities } from "./api.js";

async function load() {
  const data = await getActivities();

  const container = document.getElementById("list");

  container.innerHTML = data
    .map(
      (a) => `
    <div>
      <b>${a.date}</b> - ${a.activite} (${a.lieu})
      ${a.inscrit ? "■" : "→"}
    </div>
  `,
    )
    .join("");
}

load();
