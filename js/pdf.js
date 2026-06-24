import { getActivities } from "./api.js";

export async function generatePDF() {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF();

  const data = await getActivities();

  // 📊 STATS (comme ton Python)
  const total = data.length;
  const ok = data.filter((a) => a.inscrit).length;
  const ko = total - ok;

  doc.setFontSize(16);
  doc.text("Activités bénévoles de secourisme", 10, 10);

  doc.setFontSize(10);
  doc.text(`Total: ${total}`, 10, 20);
  doc.text(`Confirmées: ${ok}`, 10, 26);
  doc.text(`Souhaitées: ${ko}`, 10, 32);

  let y = 45;

  // 📄 LISTE
  data.forEach((a) => {
    const symbole = a.inscrit ? "■" : "→";

    const line = `${symbole} ${a.asso} | ${a.date} | ${a.activite} | ${a.lieu}`;

    doc.text(line, 10, y);
    y += 6;

    if (y > 280) {
      doc.addPage();
      y = 10;
    }
  });

  doc.save("Liste_activites_secours.pdf");
}
