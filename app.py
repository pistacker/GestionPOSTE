import streamlit as st
import json
import os
import datetime
# On importe la fonction de génération PDF depuis ton script existant
from gestion_dps import generer_pdf, JSON_FILE, PDF_FILE, MOIS, JOURS, charger, sauvegarder

st.set_page_config(page_title="Gestion DPS - Secourisme", page_icon="🚑", layout="wide")

# --- COULEURS IDENTIQUES AU PDF ---
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

# --- CHARGEMENT DES DONNÉES ---
activites = charger()

# Pour pouvoir modifier/supprimer précisément, on ajoute un identifiant unique temporaire indexé
for i, a in enumerate(activites):
    a["_index_original"] = i

# Tri automatique de toutes les activités par date
try:
    activites.sort(key=lambda x: datetime.datetime.strptime(x["date"], "%d/%m/%Y"))
except Exception:
    pass

# --- SÉPARATION : À VENIR VS PASSÉES ---
aujourdhui = datetime.date.today()
activites_a_venir = []
activites_passees = []

for a in activites:
    try:
        date_act = datetime.datetime.strptime(a["date"], "%d/%m/%Y").date()
        if date_act >= aujourdhui:
            activites_a_venir.append(a)
        else:
            activites_passees.append(a)
    except Exception:
        activites_a_venir.append(a)

# Calcul des statistiques globales
nb_total = len(activites)
nb_inscrit = sum(1 for a in activites if a.get("inscrit"))
nb_souhaite = nb_total - nb_inscrit
nb_apc = sum(1 for a in activites if a.get("asso") == "APC")
nb_unit = sum(1 for a in activites if a.get("asso") == "Unit")

# ═══════════════════════════════════════════════════════════════════════════════
#  EN-TÊTE PRINCIPAL & DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(
    f"""
    <div style="background-color: {C_BLEU_NUIT}; color: white; padding: 25px; border-radius: 8px; margin-bottom: 5px; border-bottom: 4px solid {C_BLEU_VIF};">
        <h1 style="color: white; margin: 0; font-size: 28px;">🚑 Activités bénévoles de secourisme</h1>
        <p style="color: #A0BED8; margin: 5px 0 0 0; font-weight: bold; font-size: 16px;">Protection Civile &nbsp;·&nbsp; Unit' Secours</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div style="background-color: #EEF3FA; padding: 15px; border-radius: 8px; margin-bottom: 25px; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px;">
        <div style="background-color: white; border-radius: 6px; padding: 12px; text-align: center; border-top: 5px solid {C_BLEU_VIF};">
            <div style="font-size: 26px; font-weight: bold; color: {C_BLEU_VIF};">{nb_total}</div>
            <div style="font-size: 11px; font-weight: bold; color: {C_GRIS_TEXTE}; border-top: 1px solid #DDD; padding-top: 4px;">TOTAL GENERAL</div>
            <div style="font-size: 10px; color: #999;">{len(activites_a_venir)} à venir · {len(activites_passees)} effectuée(s)</div>
        </div>
        <div style="background-color: white; border-radius: 6px; padding: 12px; text-align: center; border-top: 5px solid {C_VERT};">
            <div style="font-size: 26px; font-weight: bold; color: {C_VERT};">{nb_inscrit}</div>
            <div style="font-size: 11px; font-weight: bold; color: {C_GRIS_TEXTE}; border-top: 1px solid #DDD; padding-top: 4px;">CONFIRMÉES</div>
        </div>
        <div style="background-color: white; border-radius: 6px; padding: 12px; text-align: center; border-top: 5px solid {C_ROUGE};">
            <div style="font-size: 26px; font-weight: bold; color: {C_ROUGE};">{nb_souhaite}</div>
            <div style="font-size: 11px; font-weight: bold; color: {C_GRIS_TEXTE}; border-top: 1px solid #DDD; padding-top: 4px;">SOUHAITÉES</div>
        </div>
        <div style="background-color: white; border-radius: 6px; padding: 12px; text-align: center; border-top: 5px solid {C_OR};">
            <div style="font-size: 26px; font-weight: bold; color: {C_OR};">{nb_apc} <span style="font-size:16px; color:#aaa;">/</span> {nb_unit}</div>
            <div style="font-size: 11px; font-weight: bold; color: {C_GRIS_TEXTE}; border-top: 1px solid #DDD; padding-top: 4px;">APC / UNIT</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# --- ONGLETS RESTRUCTURÉS ---
onglet_voir, onglet_effectuees, onglet_ajouter = st.tabs([
    "📋 Activités à venir", "📜 Activités effectuées", "➕ Ajouter un secours"
])

# Fonction pour afficher la liste interactive avec gestion de modification et suppression en ligne
def afficher_liste_interactive(liste_a_afficher):
    if not liste_a_afficher:
        st.info("Aucune activité dans cette catégorie.")
        return

    groupes = {}
    ordre_mois = []
    for a in liste_a_afficher:
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

    for cle in ordre_mois:
        groupe = groupes[cle]
        label_mois = groupe["label"]
        nb_m = len(groupe["activites"])

        st.markdown(
            f"""
            <div style="background-color: {C_BLEU_VIF}; color: white; padding: 10px 15px; border-radius: 4px 4px 0 0; margin-top: 15px; font-weight: bold; font-size: 15px; display: flex; justify-content: space-between;">
                <span>📅 &nbsp; {label_mois}</span>
                <span style="font-size: 13px; opacity: 0.9;">{nb_m} activité{'s' if nb_m > 1 else ''}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        for idx, a in enumerate(groupe["activites"]):
            idx_orig = a["_index_original"]
            ok = a.get("inscrit", True)
            symbole = "■" if ok else "→"

            try:
                dt = datetime.datetime.strptime(a["date"], "%d/%m/%Y")
                jour_sem = JOURS[dt.weekday()]
                jour_num = dt.strftime("%d")
                mois_abr = MOIS[dt.month][:3].capitalize()
                date_aff = f"{jour_sem} {jour_num} {mois_abr}."
            except Exception:
                date_aff = a.get("date", "")

            if ok:
                bg_color = "#FFFFFF" if idx % 2 == 0 else C_BLEU_PALE
                text_color = C_GRIS_TEXTE
                asso_color = C_VERT
                act_color = C_BLEU_MED
            else:
                bg_color = C_ROUGE_FOND
                text_color = C_ROUGE
                asso_color = C_ROUGE
                act_color = C_ROUGE

            details_html = f"<div style='font-weight: bold; font-size: 14px; color: {act_color};'>{a.get('activite', '')}</div>"
            if a.get('lieu'):
                details_html += f"<div style='font-size: 12px; color: {text_color}; margin-top: 2px;'>📍 {a['lieu']}</div>"
            if a.get('rdv'):
                details_html += f"<div style='font-size: 11px; color: {C_OR}; font-weight: bold; margin-top: 2px;'>◆ RDV : {a['rdv']}</div>"
            if a.get('note'):
                details_html += f"<div style='font-size: 11px; font-style: italic; color: #777; margin-top: 2px;'>✎ {a['note']}</div>"

            # Création de la ligne avec deux colonnes : 1 pour le visuel PDF, 1 pour les actions rapides
            col_contenu, col_actions = st.columns([6, 1])
            
            with col_contenu:
                st.markdown(
                    f"""
                    <div style="background-color: {bg_color}; padding: 10px 15px; display: flex; align-items: top; border-bottom: 1px solid #D8E2EE; color: {text_color}; min-height: 85px;">
                        <div style="width: 18%; font-weight: bold; color: {asso_color};">{symbole} {a.get('asso', '')}</div>
                        <div style="width: 25%; font-weight: bold;">{date_aff}</div>
                        <div style="width: 40%;">{details_html}</div>
                        <div style="width: 17%; text-align: right; font-weight: bold; color: {act_color};">{a.get('horaire', '')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
            with col_actions:
                # Boutons d'action alignés verticalement
                st.write("") # Petit espacement pour centrer
                c_edit, c_del = st.columns(2)
                with c_edit:
                    btn_modifier = st.button("✏️", key=f"edit_{idx_orig}", help="Modifier cette activité")
                with c_del:
                    btn_supprimer = st.button("❌", key=f"del_{idx_orig}", help="Supprimer cette activité")

            # --- ZONE DE MODIFICATION EN LIGNE (DYNAMIQUE) ---
            if st.session_state.get(f"actif_edit_{idx_orig}", False) or btn_modifier:
                st.session_state[f"actif_edit_{idx_orig}"] = True
                st.markdown(f"<div style='border: 2px solid {C_BLEU_VIF}; padding: 15px; border-radius: 5px; background-color: #f9f9f9; margin: 10px 0;'>", unsafe_allow_html=True)
                st.info(f"Modification de l'activité : {a['activite']}")
                
                with st.form(key=f"form_en_ligne_{idx_orig}"):
                    m_asso = st.radio("Association", ["APC", "Unit"], index=0 if a["asso"] == "APC" else 1, horizontal=True)
                    try:
                        current_date = datetime.datetime.strptime(a["date"], "%d/%m/%Y").date()
                    except:
                        current_date = datetime.date.today()
                    m_date_obj = st.date_input("Date", current_date)
                    m_activite = st.text_input("Activité", value=a["activite"])
                    m_lieu = st.text_input("Lieu", value=a["lieu"])
                    m_horaire = st.text_input("Horaire DPS", value=a["horaire"])
                    m_rdv = st.text_input("RDV local", value=a["rdv"])
                    m_statut = st.radio("Statut", ["Inscrit(e) / Confirmé(e)", "Souhaité (non inscrit)"], index=0 if a["inscrit"] else 1, horizontal=True)
                    m_note = st.text_area("Note", value=a["note"])
                    
                    c_form1, c_form2 = st.columns(2)
                    with c_form1:
                        if st.form_submit_button("💾 Enregistrer"):
                            # On recharge la liste brute globale, applique le changement à l'index d'origine
                            liste_brute = charger()
                            liste_brute[idx_orig] = {
                                "asso": m_asso, "date": m_date_obj.strftime("%d/%m/%Y"),
                                "activite": m_activite, "lieu": m_lieu, "horaire": m_horaire,
                                "rdv": m_rdv, "inscrit": m_statut == "Inscrit(e) / Confirmé(e)", "note": m_note
                            }
                            sauvegarder(liste_brute)
                            st.session_state[f"actif_edit_{idx_orig}"] = False
                            st.rerun()
                    with c_form2:
                        if st.form_submit_button("Annuler"):
                            st.session_state[f"actif_edit_{idx_orig}"] = False
                            st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            # --- ZONE DE SUPPRESSION EN LIGNE (DYNAMIQUE) ---
            if st.session_state.get(f"actif_del_{idx_orig}", False) or btn_supprimer:
                st.session_state[f"actif_del_{idx_orig}"] = True
                st.warning(f"Êtes-vous sûr de vouloir supprimer définitivement : {a['activite']} ?")
                c_del1, c_del2 = st.columns(2)
                with c_del1:
                    if st.button("🗑️ Oui, supprimer", key=f"conf_del_{idx_orig}", type="primary"):
                        liste_brute = charger()
                        liste_brute.pop(idx_orig)
                        sauvegarder(liste_brute)
                        st.session_state[f"actif_del_{idx_orig}"] = False
                        st.rerun()
                with c_del2:
                    if st.button("Annuler", key=f"canc_del_{idx_orig}"):
                        st.session_state[f"actif_del_{idx_orig}"] = False
                        st.rerun()


# Légende commune
legende_html = f"""
<h3 style="font-size: 16px; color: {C_BLEU_NUIT}; margin-bottom: 5px;">ℹ️ LÉGENDE & INFO</h3>
<div style="height: 2px; background-color: {C_BLEU_VIF}; margin-bottom: 15px;"></div>
<div style="display: flex; margin-bottom: 12px; align-items: center;">
    <div style="background-color: {C_VERT}; color: white; width: 24px; height: 24px; border-radius: 4px; text-align: center; font-weight: bold; line-height: 24px; margin-right: 10px;">■</div>
    <div style="font-size: 12px; font-weight: bold; color: {C_GRIS_TEXTE};">Inscrit(e) et confirmé(e)</div>
</div>
<div style="display: flex; margin-bottom: 12px; align-items: center;">
    <div style="background-color: {C_ROUGE}; color: white; width: 24px; height: 24px; border-radius: 4px; text-align: center; font-weight: bold; line-height: 24px; margin-right: 10px;">→</div>
    <div style="font-size: 12px; font-weight: bold; color: {C_GRIS_TEXTE};">Souhaité(e) / En attente</div>
</div>
<div style="display: flex; margin-bottom: 12px; align-items: center;">
    <div style="background-color: {C_OR}; color: white; width: 24px; height: 24px; border-radius: 4px; text-align: center; font-weight: bold; line-height: 24px; margin-right: 10px;">◆</div>
    <div style="font-size: 12px; font-weight: bold; color: {C_GRIS_TEXTE};">RDV au local</div>
</div>
"""

# ═══════════════════════════════════════════════════════════════════════════════
#  ONGLET 1 : À VENIR
# ═══════════════════════════════════════════════════════════════════════════════
with onglet_voir:
    col_gauche, col_droite = st.columns([3, 1])
    with col_gauche:
        afficher_liste_interactive(activites_a_venir)
    with col_droite:
        st.markdown("### 🖨️ Action")
        if os.path.exists(PDF_FILE):
            with open(PDF_FILE, "rb") as f:
                st.download_button(label="📥 Télécharger le PDF", data=f, file_name="Liste_activites_secours.pdf", mime="application/pdf", use_container_width=True)
        st.markdown("---")
        st.markdown(legende_html, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  ONGLET 2 : EFFECTUÉES
# ═══════════════════════════════════════════════════════════════════════════════
with onglet_effectuees:
    col_gauche, col_droite = st.columns([3, 1])
    with col_gauche:
        afficher_liste_interactive(activites_passees)
    with col_droite:
        st.markdown(legende_html, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  ONGLET 3 : AJOUTER UN SECOURS
# ═══════════════════════════════════════════════════════════════════════════════
with onglet_ajouter:
    st.subheader("Ajouter une nouvelle activité")
    with st.form("form_ajouter", clear_on_submit=True):
        asso = st.radio("Association", ["APC", "Unit"], horizontal=True)
        date_obj = st.date_input("Date de l'activité", datetime.date.today())
        activite = st.text_input("Nom de l'activité")
        lieu = st.text_input("Lieu")
        horaire = st.text_input("Horaire DPS")
        rdv = st.text_input("Horaire RDV local (optionnel)")
        statut_choix = st.radio("Statut", ["Inscrit(e) / Confirmé(e)", "Souhaité (non inscrit)"], horizontal=True)
        note = st.text_area("Note (optionnel)")
        
        if st.form_submit_button("Enregistrer l'activité"):
            if not activite or not lieu:
                st.error("Veuillez remplir au moins l'activité et le lieu.")
            else:
                date_str = date_obj.strftime("%d/%m/%Y")
                liste_brute = charger()
                liste_brute.append({
                    "asso": asso, "date": date_str, "activite": activite,
                    "lieu": lieu, "horaire": horaire, "rdv": rdv,
                    "inscrit": statut_choix == "Inscrit(e) / Confirmé(e)", "note": note
                })
                sauvegarder(liste_brute)
                st.success("Activité ajoutée avec succès !")
                st.rerun()