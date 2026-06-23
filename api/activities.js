import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { createErrorResponse, createSuccessResponse } from "./utils.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DATA_FILE = path.join(__dirname, "..", "activites.json");

function readData() {
  if (!fs.existsSync(DATA_FILE)) return [];
  try {
    const raw = fs.readFileSync(DATA_FILE, "utf8");
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeData(data) {
  fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2), "utf8");
}

export default async function handler(req, res) {
  if (req.method === "GET") {
    return res.status(200).json(readData());
  }

  if (req.method === "POST") {
    const item = req.body || {};
    if (!item.activite || !item.date) {
      return res.status(400).json({ error: "Activité et date obligatoires" });
    }
    const data = readData();
    data.push({
      asso: item.asso || "APC",
      date: item.date,
      activite: item.activite,
      lieu: item.lieu || "",
      horaire: item.horaire || "",
      rdv: item.rdv || "",
      inscrit: Boolean(item.inscrit),
      note: item.note || "",
    });
    writeData(data);
    return res.status(200).json({ ok: true });
  }

  if (req.method === "DELETE") {
    const idx = Number(req.query.index || req.query.id || 0);
    const data = readData();
    if (idx < 0 || idx >= data.length) {
      return res.status(404).json({ error: "Activité introuvable" });
    }
    data.splice(idx, 1);
    writeData(data);
    return res.status(200).json({ ok: true });
  }

  return res.status(405).json({ error: "Méthode non autorisée" });
}
