import streamlit as st
import json
import os
import datetime
# On importe la fonction de génération PDF depuis ton script existant
from gestion_dps import generer_pdf, JSON_FILE, PDF_FILE, MOIS, JOURS, charger, sauvegarder

st.set_page_config(page_title="Gestion DPS - Secourisme", page_icon="🚑", layout="wide")

# Palette de couleurs identique au PDF
C_BLEU_NUIT  = "#0D2137"
C_BLEU_MED   = "#1A4A7A"
C_BLEU_VIF   = "#1E6FBB"
C_BLEU_CLAIR = "#E8F1FB"
C_BLEU_PALE  = "#F0F6FF"
C_ROUGE      = "#C0392B"
C_ROUGE_FOND = "#FEF0EE"
C_ROUGE_BORD = "#E8A89E"
C_VERT       = "#1A7A4A"
C_VERT_FOND  = "#EAF7EF"
C_OR         = "#D4A017"
C_GRIS_TEXTE = "#333333"
C_GRIS_MED   = "#666666"

st.title("🚑 Gestion des Activités de Secours")
st.write("Consultez, ajoutez, modifiez ou supprimez les activités en temps réel.")

# --- CHARGEMENT DES DONNÉES ---
activites = charger()

# Tri automatique par date
try:
    activites.sort(key=lambda x: datetime.datetime.strptime(x["date"], "%d/%m/%Y"))
except Exception:
    pass

# --- EN-TÊTE / STATISTIQUES COPIÉES DU STYLE DU PDF ---
nb_total = len(activites)
nb_inscrit = sum(1 for a in activites if a.get("inscrit"))
nb_souhaite = nb_total - nb_inscrit

col_stat1, col_stat2, col_stat3 = st.columns(3)
col_stat1.metric("Total Activités", nb_total)
col_stat2.metric("Confirmées (■)", nb_inscrit)
col_stat3.metric("Souhaitées (→)", nb_souhaite)

st.markdown("---")

# --- ONGLETS PRINCIPAUX ---
onglet_voir, onglet_ajouter, onglet_modifier, onglet_supprimer = st.tabs([
    "📋 Liste comme le PDF", "➕ Ajouter", "✏️ Modifier", "❌ Supprimer"
])

# ═══════════════════════════════════════════════════════════════════════════════
#  ONGLET 1 : VOIR & TÉLÉCHARGER (STYLE ALIGNÉ SUR LE PDF)
# ═══════════════════════════════════════════════════════════════════════════════
with onglet_voir:
    col_btn1, col_btn2 = st.columns([2, 1])
    with col_btn1:
        st.subheader("Visualisation de la liste des secours")
    with col_btn2:
        # Bouton pour télécharger le PDF mis à jour
        if os.path.exists(PDF_FILE):
            with open(PDF_FILE, "rb") as f:
                st.download_button(
                    label="📥 Télécharger le fichier PDF",
                    data=f,
                    file_name="Liste_activites_secours.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        else:
            if st.button("Générer le PDF", use_container_width=True):
                generer_pdf()
                st.rerun()

    if not activites:
        st.info("Aucune activité enregistrée.")
    else:
        # Regroupement par mois identique à la logique de ton PDF
        groupes = {}
        ordre_mois = []
        for a in activites:
            try:
                dt = datetime.datetime.strptime(a["date"], "%d/%m/%Y")
                cle = (dt.year, dt.month)
                label = f"{MOIS[dt.month]} {dt.year}"
            except Exception:
                cle, label = (9999, 0), "AUTRES"
            if cle not in groupes:
                groupes[cle] = {"label": label, "activites": []}
                ordre_mois.append(cle)
            groupes[cle]["activites"].append(a)

        # Affichage des blocs par mois comme dans le PDF
        for cle in ordre_mois:
            groupe = groupes[cle]
            label_mois = groupe["label"]
            nb_m = len(groupe["activites"])

            # 1. Bandeau du Mois (Bleu Vif)
            st.markdown(
                f"""
                <div style="background-color: {C_BLEU_VIF}; color: white; padding: 10px 15px; border-radius: 4px 4px 0 0; margin-top: 20px; font-weight: bold; font-size: 16px; display: flex; justify-content: space-between;">
                    <span>📅 &nbsp; {label_mois}</span>
                    <span style="font-size: 14px; opacity: 0.9;">{nb_m} activité{'s' if nb_m > 1 else ''}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

            # 2. En-tête des colonnes (Bleu Médium)
            st.markdown(
                f"""
                <div style="background-color: {C_BLEU_MED}; color: white; padding: 6px 15px; font-size: 12px; font-weight: bold; display: flex; text-transform: uppercase;">
                    <div style="width: 15%;">Orga.</div>
                    <div style="width: 20%;">Date</div>
                    <div style="width: 45%;">Activité · Lieu · Note</div>
                    <div style="width: 20%; text-align: right;">Horaire DPS</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # 3. Lignes d'activités (Couleurs alternées / Rouge si souhaité)
            for idx, a in enumerate(groupe["activites"]):
                ok = a.get("inscrit", True)
                symbole = "■" if ok else "→"

                # Formatage de la date lisible
                try:
                    dt = datetime.datetime.strptime(a["date"], "%d/%m/%Y")
                    jour_sem = JOURS[dt.weekday()]
                    jour_num = dt.strftime("%d")
                    mois_abr = MOIS[dt.month][:3].capitalize()
                    date_aff = f"{jour_sem} {jour_num} {mois_abr}."
                except Exception:
                    date_aff = a.get("date", "")

                # Définition des couleurs de fond et bordures selon le statut (comme le PDF)
                if ok:
                    bg_color = "#FFFFFF" if idx % 2 == 0 else C_BLEU_PALE
                    border_style = "border-bottom: 1px solid #D8E2EE;"
                    text_color = C_GRIS_TEXTE
                    asso_color = C_VERT
                    act_color = C_BLEU_MED
                else:
                    bg_color = C_ROUGE_FOND
                    border_style = f"border-top: 1px solid {C_ROUGE_BORD}; border-bottom: 1px solid {C_ROUGE_BORD};"
                    text_color = C_ROUGE
                    asso_color = C_ROUGE
                    act_color = C_ROUGE

                # Construction de la zone détails (Lieu, RDV, Notes)
                details_html = f"<div style='font-weight: bold; font-size: 14px; color: {act_color};'>{a.get('activite', '')}</div>"
                if a.get('lieu'):
                    details_html += f"<div style='font-size: 12px; color: {text_color}; margin-top: 2px;'>📍 {a['lieu']}</div>"
                if a.get('rdv'):
                    details_html += f"<div style='font-size: 11px; color: {C_OR}; font-weight: bold; margin-top: 2px;'>◆ RDV : {a['rdv']}</div>"
                if a.get('note'):
                    details_html += f"<div style='font-size: 11px; font-style: italic; color: #777; margin-top: 2px;'>✎ {a['note']}</div>"

                # Rendu de la ligne
                st.markdown(
                    f"""
                    <div style="background-color: {bg_color}; padding: 10px 15px; display: flex; align-items: top; {border_style} color: {text_color};">
                        <div style="width: 15%; font-weight: bold; color: {asso_color};">{symbole} {a.get('asso', '')}</div>
                        <div style="width: 20%; font-weight: bold;">{date_aff}</div>
                        <div style="width: 45%;">{details_html}</div>
                        <div style="width: 20%; text-align: right; font-weight: bold; color: {act_color};">{a.get('horaire', '')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            # Espacement après le bloc du mois
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  ONGLET 2 : AJOUTER
# ═══════════════════════════════════════════════════════════════════════════════
with onglet_ajouter:
    st.subheader("Ajouter une nouvelle activité")
    with st.form("form_ajouter", clear_on_submit=True):
        asso = st.radio("Association", ["APC", "Unit"], horizontal=True)
        date_obj = st.date_input("Date de l'activité", datetime.date.today())
        activite = st.text_input("Nom de l'activité")
        lieu = st.text_input("Lieu")
        horaire = st.text_input("Horaire DPS (ex: 14h00 - 18h00)")
        rdv = st.text_input("Horaire RDV local (laisser vide si aucun)")
        statut_choix = st.radio("Statut", ["Inscrit(e) / Confirmé(e)", "Souhaité (non inscrit)"], horizontal=True)
        note = st.text_area("Note (facultatif)")
        
        soumettre = st.form_submit_button("Enregistrer l'activité")
        
        if soumettre:
            if not activite or not lieu:
                st.error("Veuillez remplir au moins l'activité et le lieu.")
            else:
                date_str = date_obj.strftime("%d/%m/%Y")
                nouvelle_act = {
                    "asso": asso, "date": date_str, "activite": activite,
                    "lieu": lieu, "horaire": horaire, "rdv": rdv,
                    "inscrit": statut_choix == "Inscrit(e) / Confirmé(e)", "note": note
                }
                activites.append(nouvelle_act)
                sauvegarder(activites)
                st.success("Activité ajoutée avec succès ! Le PDF a été mis à jour.")
                st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
#  ONGLET 3 : MODIFIER
# ═══════════════════════════════════════════════════════════════════════════════
with onglet_modifier:
    st.subheader("Modifier une activité existante")
    if not activites:
        st.write("Aucune activité à modifier.")
    else:
        options_modif = [f"{i+1} - {a['date']} | {a['asso']} | {a['activite']}" for i, a in enumerate(activites)]
        choix_modif = st.selectbox("Sélectionnez l'activité à modifier", options_modif)
        index_modif = options_modif.index(choix_modif)
        act_a_modifier = activites[index_modif]
        
        with st.form("form_modifier"):
            m_asso = st.radio("Association", ["APC", "Unit"], index=0 if act_a_modifier["asso"] == "APC" else 1, horizontal=True)
            try:
                current_date = datetime.datetime.strptime(act_a_modifier["date"], "%d/%m/%Y").date()
            except:
                current_date = datetime.date.today()
                
            m_date_obj = st.date_input("Date de l'activité", current_date)
            m_activite = st.text_input("Nom de l'activité", value=act_a_modifier["activite"])
            m_lieu = st.text_input("Lieu", value=act_a_modifier["lieu"])
            m_horaire = st.text_input("Horaire DPS", value=act_a_modifier["horaire"])
            m_rdv = st.text_input("Horaire RDV local", value=act_a_modifier["rdv"])
            m_statut = st.radio("Statut", ["Inscrit(e) / Confirmé(e)", "Souhaité (non inscrit)"], index=0 if act_a_modifier["inscrit"] else 1, horizontal=True)
            m_note = st.text_area("Note", value=act_a_modifier["note"])
            
            valider_modif = st.form_submit_button("Enregistrer les modifications")
            
            if valider_modif:
                activites[index_modif] = {
                    "asso": m_asso, "date": m_date_obj.strftime("%d/%m/%Y"),
                    "activite": m_activite, "lieu": m_lieu, "horaire": m_horaire,
                    "rdv": m_rdv, "inscrit": m_statut == "Inscrit(e) / Confirmé(e)", "note": m_note
                }
                sauvegarder(activites)
                st.success("Modifications enregistrées et PDF mis à jour !")
                st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
#  ONGLET 4 : SUPPRIMER
# ═══════════════════════════════════════════════════════════════════════════════
with onglet_supprimer:
    st.subheader("Supprimer une activité")
    if not activites:
        st.write("Aucune activité à supprimer.")
    else:
        options_suppr = [f"{i+1} - {a['date']} | {a['asso']} | {a['activite']}" for i, a in enumerate(activites)]
        choix_suppr = st.selectbox("Sélectionnez l'activité à supprimer", options_suppr)
        index_suppr = options_suppr.index(choix_suppr)
        
        if st.button("❌ Supprimer définitivement", type="primary"):
            activites.pop(index_suppr)
            sauvegarder(activites)
            st.success("Activité supprimée avec succès !")
            st.rerun()