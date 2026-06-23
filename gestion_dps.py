# gestion_dps.py

import json
import os
import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, NextPageTemplate
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE_DIR, "activites.json")
PDF_FILE  = os.path.join(BASE_DIR, "Liste_activites_secours.pdf")

MOIS = {
    1: "JANVIER",   2: "FÉVRIER",  3: "MARS",
    4: "AVRIL",     5: "MAI",      6: "JUIN",
    7: "JUILLET",   8: "AOÛT",     9: "SEPTEMBRE",
    10: "OCTOBRE", 11: "NOVEMBRE", 12: "DÉCEMBRE",
}

JOURS = {
    0: "Lun.", 1: "Mar.", 2: "Mer.",
    3: "Jeu.", 4: "Ven.", 5: "Sam.", 6: "Dim.",
}

# ═══════════════════════════════════════════════════════════════════════════════
#  CRUD
# ═══════════════════════════════════════════════════════════════════════════════

def charger():
    if not os.path.exists(JSON_FILE):
        return []
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def sauvegarder(data):
    os.makedirs(os.path.dirname(JSON_FILE), exist_ok=True)
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    generer_pdf()


def ajouter_activite():
    print("\nAssociation :")
    print("1 - Protection Civile")
    print("2 - Unit' Secours")
    choix = input("\nChoix : ")
    if choix == "1":
        asso = "APC"
    elif choix == "2":
        asso = "Unit"
    else:
        print("Choix invalide.")
        return

    date    = input("Date (JJ/MM/AAAA) : ")
    activite = input("Activité : ")
    lieu    = input("Lieu : ")
    horaire = input("Horaire DPS : ")
    rdv     = input("Horaire RDV local (vide si aucun) : ")

    print("\nStatut :")
    print("1 - Inscrit(e)")
    print("2 - Souhaité (non inscrit)")
    statut = input("Choix : ").strip()
    if statut not in {"1", "2"}:
        print("Choix invalide.")
        return
    inscrit = statut == "1"
    note = input("Note (facultatif) : ")

    activites = charger()
    activites.append({
        "asso": asso, "date": date, "activite": activite,
        "lieu": lieu, "horaire": horaire, "rdv": rdv,
        "inscrit": inscrit, "note": note,
    })
    sauvegarder(activites)
    print("\nActivité enregistrée.")


def afficher():
    activites = charger()
    if not activites:
        print("\nAucune activité.")
        return
    print()
    for i, a in enumerate(activites, start=1):
        statut = "■" if a["inscrit"] else "→"
        print(f"{i} - {statut} {a['asso']} | {a['date']} | {a['activite']}")


def supprimer():
    activites = charger()
    if not activites:
        print("\nAucune activité.")
        return
    afficher()
    try:
        num = int(input("\nNuméro à supprimer : "))
    except:
        return
    if num < 1 or num > len(activites):
        return
    if input("Confirmer ? (o/n) : ").lower() == "o":
        activites.pop(num - 1)
        sauvegarder(activites)
        print("Activité supprimée.")


def modifier():
    activites = charger()
    if not activites:
        print("\nAucune activité.")
        return
    afficher()
    try:
        num = int(input("\nNuméro à modifier : "))
    except:
        return
    if num < 1 or num > len(activites):
        return
    a = activites[num - 1]
    print("\nEntrée pour conserver la valeur actuelle.\n")
    for champ in ("date", "activite", "lieu", "horaire", "rdv", "note"):
        val = input(f"{champ.capitalize()} [{a[champ]}] : ")
        if val:
            a[champ] = val
    sauvegarder(activites)
    print("\nModification enregistrée.")


# ═══════════════════════════════════════════════════════════════════════════════
#  PDF
# ═══════════════════════════════════════════════════════════════════════════════

def generer_pdf():
    activites = charger()
    try:
        activites.sort(key=lambda x: datetime.datetime.strptime(x["date"], "%d/%m/%Y"))
    except Exception:
        pass

    # ── Palette ──────────────────────────────────────────────────────────────
    C_BLEU_NUIT  = colors.HexColor("#0D2137")   # bandeau principal
    C_BLEU_MED   = colors.HexColor("#1A4A7A")   # accents foncés
    C_BLEU_VIF   = colors.HexColor("#1E6FBB")   # badges, barres mois
    C_BLEU_CLAIR = colors.HexColor("#E8F1FB")   # fond en-tête tableau
    C_BLEU_PALE  = colors.HexColor("#F0F6FF")   # fond ligne paire
    C_ROUGE      = colors.HexColor("#C0392B")   # souhaitée
    C_ROUGE_FOND = colors.HexColor("#FEF0EE")   # fond ligne souhaitée
    C_ROUGE_BORD = colors.HexColor("#E8A89E")
    C_VERT       = colors.HexColor("#1A7A4A")   # confirmée (badge)
    C_VERT_FOND  = colors.HexColor("#EAF7EF")   # fond ligne confirmée (option)
    C_OR         = colors.HexColor("#D4A017")   # RDV
    C_GRIS_TEXTE = colors.HexColor("#333333")
    C_GRIS_MED   = colors.HexColor("#666666")
    C_GRIS_CLAIR = colors.HexColor("#F5F7FA")
    C_GRIS_LIGNE = colors.HexColor("#D8E2EE")
    C_BLANC      = colors.white

    W, H = A4
    now  = datetime.datetime.now()
    date_gen = now.strftime("%d/%m/%Y à %H:%M")

    # ── Stats rapides ─────────────────────────────────────────────────────────
    nb_total    = len(activites)
    nb_inscrit  = sum(1 for a in activites if a.get("inscrit"))
    nb_souhaite = nb_total - nb_inscrit
    nb_apc      = sum(1 for a in activites if a.get("asso") == "APC")
    nb_unit     = sum(1 for a in activites if a.get("asso") == "Unit")

    # ── Helpers de style ─────────────────────────────────────────────────────
    def P(text, **kw):
        return Paragraph(text, ParagraphStyle("_", **kw))

    # ── Sommaire par mois (calculé à l'avance) ───────────────────────────────
    sommaire = {}  # {(year,month): {"label":…, "nb":…, "nb_ok":…, "nb_ko":…}}
    for a in activites:
        try:
            dt  = datetime.datetime.strptime(a["date"], "%d/%m/%Y")
            cle = (dt.year, dt.month)
            lab = f"{MOIS[dt.month]} {dt.year}"
        except Exception:
            cle, lab = (9999, 0), "AUTRES"
        if cle not in sommaire:
            sommaire[cle] = {"label": lab, "nb": 0, "nb_ok": 0, "nb_ko": 0}
        sommaire[cle]["nb"] += 1
        if a.get("inscrit"):
            sommaire[cle]["nb_ok"] += 1
        else:
            sommaire[cle]["nb_ko"] += 1
    ordre_som = sorted(sommaire.keys())

    # ── Canvas callbacks ─────────────────────────────────────────────────────
    def _croix(c, cx, cy, r, bras, long_bras, fill_col, cross_col):
        """Dessine une croix de secours centrée en (cx, cy)."""
        c.setFillColor(fill_col)
        c.circle(cx, cy, r, fill=True, stroke=False)
        c.setFillColor(cross_col)
        c.rect(cx - bras,      cy - long_bras, bras * 2,      long_bras * 2, fill=True, stroke=False)
        c.rect(cx - long_bras, cy - bras,      long_bras * 2, bras * 2,      fill=True, stroke=False)

    def _page_cover(c, doc):
        """Page de garde avec zones clairement séparées et sans chevauchement."""

        # ═══════════════════════════════════════════════════════════════════════
        # ZONE 1 — BANDEAU TITRE  (y = H-80mm → H)   hauteur 80 mm
        # ═══════════════════════════════════════════════════════════════════════
        BAND_H   = 78*mm
        BAND_BOT = H - BAND_H          # y bas du bandeau

        c.setFillColor(C_BLEU_NUIT)
        c.rect(0, BAND_BOT, W, BAND_H, fill=True, stroke=False)

        # Trait bleu vif en bas du bandeau
        c.setFillColor(C_BLEU_VIF)
        c.rect(0, BAND_BOT, W, 2*mm, fill=True, stroke=False)

        # Croix de secours — coin haut droit, bien dans le bandeau
        _croix(c, cx=W - 25*mm, cy=H - 22*mm,
               r=14*mm, bras=4*mm, long_bras=9*mm,
               fill_col=C_BLEU_VIF, cross_col=C_BLANC)

        # Titre principal (à gauche, centré verticalement dans le bandeau)
        c.setFillColor(C_BLANC)
        c.setFont("Helvetica-Bold", 22)
        c.drawString(20*mm, H - 28*mm, "Activités bénévoles de secourisme")

        # Sous-titre
        c.setFillColor(colors.HexColor("#A0BED8"))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20*mm, H - 42*mm, "Protection Civile  ·  Unit' Secours")

        # Description (2 lignes)
        c.setFillColor(colors.HexColor("#7FA8C8"))
        c.setFont("Helvetica", 9)
        c.drawString(20*mm, H - 55*mm,
            "Ce document récapitule mes prochaines activités bénévoles.")
        c.drawString(20*mm, H - 64*mm,
            f"Généré le {date_gen}  ·  {nb_total} activité{'s' if nb_total > 1 else ''} au total")

        # ═══════════════════════════════════════════════════════════════════════
        # ZONE 2 — CARTES STATISTIQUES  (y = H-150mm → H-82mm)  hauteur 66 mm
        # ═══════════════════════════════════════════════════════════════════════
        CARD_TOP = BAND_BOT - 4*mm      # 4 mm d'air sous le bandeau
        CARD_H   = 44*mm
        CARD_BOT = CARD_TOP - CARD_H

        # Fond gris très clair pour la zone cartes
        c.setFillColor(colors.HexColor("#EEF3FA"))
        c.rect(0, CARD_BOT - 4*mm, W, CARD_H + 8*mm, fill=True, stroke=False)

        stats = [
            ("TOTAL",        str(nb_total),           C_BLEU_VIF, "activités"),
            ("CONFIRMÉES",   str(nb_inscrit),          C_VERT,     "inscrit(e)"),
            ("SOUHAITÉES",   str(nb_souhaite),         C_ROUGE,    "à confirmer"),
            ("APC / UNIT",   f"{nb_apc}  /  {nb_unit}", C_OR,     "par association"),
        ]
        MARG  = 20*mm
        GAP   = 3*mm
        card_w = (W - 2*MARG - 3*GAP) / 4

        for i, (label, valeur, couleur, sous) in enumerate(stats):
            cx_card = MARG + i * (card_w + GAP)
            cy_card = CARD_BOT

            # Fond blanc de la carte
            c.setFillColor(C_BLANC)
            c.roundRect(cx_card, cy_card, card_w, CARD_H, 5, fill=True, stroke=False)

            # Barre couleur EN HAUT de la carte (intérieure)
            c.setFillColor(couleur)
            c.roundRect(cx_card, cy_card + CARD_H - 5*mm, card_w, 5*mm, 3,
                        fill=True, stroke=False)
            # Re-dessiner les coins bas de la barre en rectangle plein
            c.rect(cx_card, cy_card + CARD_H - 5*mm, card_w, 2*mm,
                   fill=True, stroke=False)

            mid_x = cx_card + card_w / 2

            # Grande valeur numérique
            c.setFillColor(couleur)
            c.setFont("Helvetica-Bold", 22)
            c.drawCentredString(mid_x, cy_card + 22*mm, valeur)

            # Séparateur fin
            c.setStrokeColor(colors.HexColor("#DDDDDD"))
            c.setLineWidth(0.5)
            c.line(cx_card + 6*mm, cy_card + 18*mm, cx_card + card_w - 6*mm, cy_card + 18*mm)

            # Label catégorie
            c.setFillColor(C_GRIS_TEXTE)
            c.setFont("Helvetica-Bold", 7.5)
            c.drawCentredString(mid_x, cy_card + 12*mm, label)

            # Sous-label
            c.setFillColor(colors.HexColor("#999999"))
            c.setFont("Helvetica", 7)
            c.drawCentredString(mid_x, cy_card + 6*mm, sous)

        # ═══════════════════════════════════════════════════════════════════════
        # ZONE 3 — SOMMAIRE PAR MOIS  (y = CARD_BOT - 8mm vers le bas)
        # ═══════════════════════════════════════════════════════════════════════
        SOM_TOP = CARD_BOT - 10*mm
        LINE_H  = 9*mm

        # Titre section
        c.setFillColor(C_BLEU_NUIT)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(20*mm, SOM_TOP, "SOMMAIRE DES ACTIVITÉS PAR MOIS")
        c.setFillColor(C_BLEU_VIF)
        c.rect(20*mm, SOM_TOP - 1.5*mm, W - 40*mm, 1.5, fill=True, stroke=False)

        y_som = SOM_TOP - LINE_H
        nb_cols = 2
        col_w   = (W - 40*mm) / nb_cols

        for k, cle in enumerate(ordre_som):
            s = sommaire[cle]
            col_idx = k % nb_cols
            row_idx = k // nb_cols
            x_s = 20*mm + col_idx * col_w
            y_s = y_som - row_idx * LINE_H

            # Pastille mois
            c.setFillColor(C_BLEU_CLAIR)
            c.roundRect(x_s, y_s - 1*mm, col_w - 4*mm, 7*mm, 3, fill=True, stroke=False)

            c.setFillColor(C_BLEU_MED)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(x_s + 3*mm, y_s + 1.5*mm, s["label"])

            # Compteurs compacts
            c.setFillColor(C_VERT)
            c.setFont("Helvetica-Bold", 7.5)
            c.drawRightString(x_s + col_w - 18*mm, y_s + 1.5*mm, f"■ {s['nb_ok']}")
            c.setFillColor(C_ROUGE)
            c.drawRightString(x_s + col_w - 6*mm,  y_s + 1.5*mm, f"→ {s['nb_ko']}")

        # Calcul du bas du sommaire
        nb_rows = (len(ordre_som) + 1) // 2
        SOM_BOT = y_som - nb_rows * LINE_H - 4*mm

        # ═══════════════════════════════════════════════════════════════════════
        # ZONE 4 — LÉGENDE  (sous le sommaire)
        # ═══════════════════════════════════════════════════════════════════════
        LEG_TOP = SOM_BOT - 6*mm

        c.setFillColor(C_BLEU_NUIT)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(20*mm, LEG_TOP, "LÉGENDE")
        c.setFillColor(C_BLEU_VIF)
        c.rect(20*mm, LEG_TOP - 1.5*mm, W - 40*mm, 1.5, fill=True, stroke=False)

        legende_items = [
            (C_VERT,  "■",  "Inscrit(e) et confirmé(e)",    "Place réservée, présence confirmée"),
            (C_ROUGE, "→",  "Souhaité(e), non encore inscrit(e)", "En attente d'inscription"),
            (C_OR,    "◆",  "RDV au local",                 "Horaire de départ depuis le local"),
        ]
        LEG_LINE = 14*mm
        for j, (col, sym, titre, detail) in enumerate(legende_items):
            y_l = LEG_TOP - 8*mm - j * LEG_LINE

            # Puce colorée
            c.setFillColor(col)
            c.roundRect(20*mm, y_l - 1*mm, 8*mm, 8*mm, 2, fill=True, stroke=False)
            c.setFillColor(C_BLANC)
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(24*mm, y_l + 1.5*mm, sym)

            # Texte titre
            c.setFillColor(C_GRIS_TEXTE)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(31*mm, y_l + 2*mm, titre)

            # Texte détail
            c.setFillColor(C_GRIS_MED)
            c.setFont("Helvetica", 8)
            c.drawString(31*mm, y_l - 3.5*mm, detail)

        # ═══════════════════════════════════════════════════════════════════════
        # ZONE 5 — PIED DE PAGE
        # ═══════════════════════════════════════════════════════════════════════
        c.setFillColor(C_BLEU_NUIT)
        c.rect(0, 0, W, 16*mm, fill=True, stroke=False)
        c.setFillColor(C_BLEU_VIF)
        c.rect(0, 16*mm, W, 1.5, fill=True, stroke=False)

        c.setFillColor(colors.HexColor("#7FA8C8"))
        c.setFont("Helvetica", 7.5)
        c.drawString(20*mm, 6*mm,
            "Document établi à titre personnel  ·  Activités bénévoles de secourisme  ·  Unité Secours & APC – Protection Civile")
        c.setFillColor(colors.HexColor("#A0BED8"))
        c.setFont("Helvetica-Bold", 7.5)
        c.drawRightString(W - 20*mm, 6*mm, "Page 1 / Garde")

    def _page_header(c, doc):
        """En-tête compact pages de contenu."""
        # Bandeau fin bleu nuit
        c.setFillColor(C_BLEU_NUIT)
        c.rect(0, H - 22*mm, W, 22*mm, fill=True, stroke=False)
        # Trait bleu vif
        c.setFillColor(C_BLEU_VIF)
        c.rect(0, H - 24*mm, W, 2*mm, fill=True, stroke=False)
        # Logo croix mini
        cx2, cy2 = W - 15*mm, H - 11*mm
        c.setFillColor(C_BLEU_VIF)
        c.circle(cx2, cy2, 5*mm, fill=True, stroke=False)
        c.setFillColor(C_BLANC)
        b2 = 1.3*mm
        c.rect(cx2 - b2, cy2 - 3.5*mm, b2*2, 7*mm, fill=True, stroke=False)
        c.rect(cx2 - 3.5*mm, cy2 - b2, 7*mm, b2*2, fill=True, stroke=False)
        # Textes
        c.setFillColor(C_BLANC)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20*mm, H - 11*mm, "Activités bénévoles de secourisme")
        c.setFillColor(colors.HexColor("#A0BED8"))
        c.setFont("Helvetica", 8)
        c.drawString(20*mm, H - 17*mm, "Protection Civile  ·  Unit' Secours")

    def _page_footer(c, doc):
        """Pied de page pages de contenu."""
        c.setFillColor(C_BLEU_NUIT)
        c.rect(0, 0, W, 14*mm, fill=True, stroke=False)
        c.setFillColor(C_BLEU_VIF)
        c.rect(0, 14*mm, W, 1, fill=True, stroke=False)
        c.setFillColor(colors.HexColor("#7FA8C8"))
        c.setFont("Helvetica", 7.5)
        c.drawString(20*mm, 5*mm,
            "■ Inscrit(e)  ·  → Souhaité(e)  ·  APC = Association de Protection Civile  ·  Unit = Unit' Secours")
        c.setFillColor(C_BLANC)
        c.setFont("Helvetica-Bold", 8)
        c.drawRightString(W - 20*mm, 5*mm, f"Page {doc.page - 1}")

    def on_cover(c, doc):
        _page_cover(c, doc)

    def on_content(c, doc):
        _page_header(c, doc)
        _page_footer(c, doc)

    # ── Frames & templates ────────────────────────────────────────────────────
    frame_cover = Frame(0, 0, W, H, leftPadding=0, rightPadding=0,
                        topPadding=0, bottomPadding=0, id="cover")
    frame_content = Frame(
        20*mm, 18*mm, W - 40*mm, H - 18*mm - 30*mm,
        id="content",
    )

    doc = BaseDocTemplate(PDF_FILE, pagesize=A4,
                          leftMargin=20*mm, rightMargin=20*mm,
                          topMargin=30*mm, bottomMargin=18*mm)
    doc.addPageTemplates([
        PageTemplate(id="Cover",   frames=[frame_cover],   onPage=on_cover),
        PageTemplate(id="Content", frames=[frame_content], onPage=on_content),
    ])

    # ── Styles partagés ───────────────────────────────────────────────────────
    def S(**kw):
        return ParagraphStyle("_", **kw)

    s_body    = S(fontName="Helvetica",      fontSize=9,  textColor=C_GRIS_TEXTE, leading=13)
    s_bold    = S(fontName="Helvetica-Bold", fontSize=9,  textColor=C_GRIS_TEXTE, leading=13)
    s_act_ok  = S(fontName="Helvetica-Bold", fontSize=10, textColor=C_BLEU_MED,   leading=14)
    s_act_ko  = S(fontName="Helvetica-Bold", fontSize=10, textColor=C_ROUGE,      leading=14)
    s_lieu_ok = S(fontName="Helvetica",      fontSize=8.5,textColor=C_GRIS_MED,   leading=12)
    s_lieu_ko = S(fontName="Helvetica",      fontSize=8.5,textColor=C_ROUGE,      leading=12)
    s_note_ok = S(fontName="Helvetica-Oblique", fontSize=8, textColor=colors.HexColor("#888888"), leading=11)
    s_note_ko = S(fontName="Helvetica-Oblique", fontSize=8, textColor=C_ROUGE,    leading=11)
    s_rdv     = S(fontName="Helvetica-Bold", fontSize=8,  textColor=C_OR,         leading=11)
    s_asso_ok = S(fontName="Helvetica-Bold", fontSize=9,  textColor=C_VERT)
    s_asso_ko = S(fontName="Helvetica-Bold", fontSize=9,  textColor=C_ROUGE)
    s_date_ok = S(fontName="Helvetica-Bold", fontSize=9,  textColor=C_GRIS_TEXTE, leading=12)
    s_date_ko = S(fontName="Helvetica-Bold", fontSize=9,  textColor=C_ROUGE,      leading=12)
    s_hor_ok  = S(fontName="Helvetica-Bold", fontSize=9,  textColor=C_BLEU_MED,   alignment=TA_RIGHT)
    s_hor_ko  = S(fontName="Helvetica-Bold", fontSize=9,  textColor=C_ROUGE,      alignment=TA_RIGHT)
    s_col_hdr = S(fontName="Helvetica-Bold", fontSize=7.5,textColor=C_BLANC,      leading=10)
    s_col_hdr_r = S(fontName="Helvetica-Bold", fontSize=7.5, textColor=C_BLANC, leading=10, alignment=TA_RIGHT)
    s_mois    = S(fontName="Helvetica-Bold", fontSize=12, textColor=C_BLANC)

    # ── Story ─────────────────────────────────────────────────────────────────
    story = []
    # Page de garde : flowable invisible pour déclencher la page
    story.append(Spacer(W, H))
    story.append(NextPageTemplate("Content"))

    if not activites:
        story.append(Spacer(1, 10*mm))
        story.append(P("Aucune activité enregistrée pour le moment.",
                       fontName="Helvetica", fontSize=11, textColor=C_GRIS_MED,
                       alignment=TA_CENTER))
        doc.build(story)
        print(f"\nPDF généré : {PDF_FILE}")
        return

    # Regroupement par mois
    groupes, ordre_mois = {}, []
    for a in activites:
        try:
            dt  = datetime.datetime.strptime(a["date"], "%d/%m/%Y")
            cle = (dt.year, dt.month)
            label = f"{MOIS[dt.month]} {dt.year}"
        except Exception:
            cle, label = (9999, 0), "AUTRES"
        if cle not in groupes:
            groupes[cle] = {"label": label, "activites": []}
            ordre_mois.append(cle)
        groupes[cle]["activites"].append(a)

    # Colonnes
    col_asso  = 18*mm
    col_date  = 26*mm
    col_act   = 84*mm
    col_hor   = 28*mm
    col_total = col_asso + col_date + col_act + col_hor   # ≈ 156 mm

    for cle in ordre_mois:
        groupe = groupes[cle]
        nb_m   = len(groupe["activites"])
        label_mois = groupe["label"]

        # ── Titre mois ────────────────────────────────────────────────────
        hdr_mois = Table(
            [[
                Paragraph(f"  {label_mois}", s_mois),
                Paragraph(
                    f"{nb_m} activité{'s' if nb_m > 1 else ''}",
                    S(fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#A8CCE8"),
                      alignment=TA_RIGHT),
                ),
            ]],
            colWidths=[col_total * 0.72, col_total * 0.28],
        )
        hdr_mois.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), C_BLEU_VIF),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))

        # ── En-tête colonnes ──────────────────────────────────────────────
        hdr_cols = [
            [
                Paragraph("ORGA.", s_col_hdr),
                Paragraph("DATE", s_col_hdr),
                Paragraph("ACTIVITÉ  ·  LIEU  ·  NOTE", s_col_hdr),
                Paragraph("HORAIRE DPS", s_col_hdr_r),
            ]
        ]
        hdr_tab = Table(hdr_cols, colWidths=[col_asso, col_date, col_act, col_hor])
        hdr_tab.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), C_BLEU_MED),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))

        # ── Lignes ────────────────────────────────────────────────────────
        data_rows  = []
        row_styles = []

        for idx, a in enumerate(groupe["activites"]):
            ok = a.get("inscrit", True)

            # Formater la date lisiblement
            try:
                dt  = datetime.datetime.strptime(a["date"], "%d/%m/%Y")
                jour_sem = JOURS[dt.weekday()]
                jour_num = dt.strftime("%d")
                mois_abr = MOIS[dt.month][:3].capitalize()
                date_aff = f"{jour_sem} {jour_num} {mois_abr}."
            except Exception:
                date_aff = a.get("date", "")

            # Cellule activité / lieu / rdv / note
            parts = []
            parts.append(Paragraph(a.get("activite", ""), s_act_ok if ok else s_act_ko))
            if a.get("lieu"):
                parts.append(Paragraph(
                    f"📍 {a['lieu']}" if False else f"  {a['lieu']}",
                    s_lieu_ok if ok else s_lieu_ko,
                ))
            if a.get("rdv"):
                parts.append(Paragraph(f"◆  RDV : {a['rdv']}", s_rdv))
            if a.get("note"):
                parts.append(Paragraph(f"✎  {a['note']}", s_note_ok if ok else s_note_ko))

            symbole = "■" if ok else "→"
            row = [
                Paragraph(f"{symbole} {a.get('asso', '')}", s_asso_ok if ok else s_asso_ko),
                Paragraph(date_aff, s_date_ok if ok else s_date_ko),
                parts,
                Paragraph(a.get("horaire", ""), s_hor_ok if ok else s_hor_ko),
            ]
            data_rows.append(row)

            if ok:
                bg = C_BLANC if idx % 2 == 0 else C_BLEU_PALE
                row_styles += [
                    ("BACKGROUND", (0, idx), (-1, idx), bg),
                ]
            else:
                row_styles += [
                    ("BACKGROUND", (0, idx), (-1, idx), C_ROUGE_FOND),
                    ("LINEABOVE",  (0, idx), (-1, idx), 0.6, C_ROUGE_BORD),
                    ("LINEBELOW",  (0, idx), (-1, idx), 0.6, C_ROUGE_BORD),
                ]

        tab = Table(
            data_rows,
            colWidths=[col_asso, col_date, col_act, col_hor],
            repeatRows=0,
        )
        ts = TableStyle([
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW",     (0, 0), (-1, -1), 0.3, C_GRIS_LIGNE),
            ("BOX",           (0, 0), (-1, -1), 0.8, C_GRIS_LIGNE),
        ])
        for s in row_styles:
            ts.add(*s)
        tab.setStyle(ts)

        story.append(KeepTogether([
            hdr_mois,
            hdr_tab,
            tab,
            Spacer(1, 8*mm),
        ]))

    doc.build(story)
    print(f"\nPDF généré : {PDF_FILE}")


# ═══════════════════════════════════════════════════════════════════════════════
#  MENU
# ═══════════════════════════════════════════════════════════════════════════════

def menu():
    while True:
        print("\n" + "=" * 36)
        print("          GESTION DPS")
        print("=" * 36)
        print("1 - Ajouter une activité")
        print("2 - Modifier une activité")
        print("3 - Supprimer une activité")
        print("4 - Afficher les activités")
        print("5 - Générer le PDF")
        print("6 - Quitter")
        choix = input("\nChoix : ")
        if   choix == "1": ajouter_activite()
        elif choix == "2": modifier()
        elif choix == "3": supprimer()
        elif choix == "4": afficher()
        elif choix == "5": generer_pdf()
        elif choix == "6": break


if __name__ == "__main__":
    menu()
