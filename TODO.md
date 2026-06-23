# TODO

- [x] Mettre à jour `api/pdf.js` pour renvoyer le PDF en binaire (Content-Type: application/pdf) au lieu de juste `{ok:true}`.

- [x] Mettre à jour `admin.html` pour que le bouton **Générer le PDF** télécharge/ouvre le PDF via `blob()`.

- [x] (Optionnel si nécessaire) Ajouter un affichage d’erreur plus explicite côté frontend si `res.ok` est faux.

- [ ] Tester localement / vérifier l’URL Vercel `GET /api/pdf` retourne bien un `application/pdf`.
