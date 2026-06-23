import { createErrorResponse, createSuccessResponse } from "./utils.js";

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Méthode non autorisée" });
  }

  const { password } = req.body || {};
  const expected = process.env.DPS_PASSWORD;

  if (!expected || password !== expected) {
    return res.status(401).json({ error: "Mot de passe incorrect" });
  }

  return res.status(200).json({ ok: true });
}
