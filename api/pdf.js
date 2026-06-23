import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { execFileSync } from "child_process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DATA_FILE = path.join(__dirname, "..", "activites.json");
const PYTHON_FILE = path.join(__dirname, "..", "gestion_dps.py");

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

export default async function handler(req, res) {
  if (req.method !== "GET") {
    return res.status(405).json({ error: "Méthode non autorisée" });
  }

  try {
    const python = process.env.PYTHON || "python";
    execFileSync(python, [PYTHON_FILE], {
      cwd: path.join(__dirname, ".."),
      stdio: "pipe",
    });
    return res
      .status(200)
      .json({ ok: true, file: "/Liste_activites_secours.pdf" });
  } catch (error) {
    return res
      .status(500)
      .json({ error: "Échec de génération du PDF", details: String(error) });
  }
}
