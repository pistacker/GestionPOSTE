const API_URL = "https://dps-api.thepewst.workers.dev/";

export async function getActivities() {
  const res = await fetch(API_URL);
  return await res.json();
}

export async function addActivity(data) {
  await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function deleteActivity(id) {
  await fetch(API_URL, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id }),
  });
}
