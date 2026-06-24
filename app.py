import streamlit as st
import json
import os
import datetime
import urllib.parse
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

# --- FONCTION POUR LES LIENS D'AGENDA (GOOGLE CALENDAR) ---
def generer_lien_google_calendar(act):
    """Génère un lien Google Calendar pour une activité ou une liste d'activités."""
    # Si on passe une liste d'activités (bouton global), on prend la première pour l'exemple
    if isinstance(act, list):
        if not act: return "#"
        act = act[0]
        titre = f"🚑 [Multi-DPS] Consulter mon planning secourisme"
    else:
        titre = f"[{act['asso']}] {act['activite']}"
        
    details = f"Lieu: {act['lieu']}\nNote: {act['note']}\nHoraire DPS: {act['horaire']}"
    if act.get('rdv'):
        details += f"\n◆ RDV local: {act['rdv']}"
        
    try:
        dt = datetime.datetime.strptime(act["date"], "%d/%m/%Y")
        date_str = dt.strftime("%Y%m%d")
    except:
        date_str = datetime.date.today().strftime("%Y%m%d")
        
    dates_param = f"{date_str}/{date_str}"
    try:
        if "-" in act["horaire"]:
            h_debut = act["horaire"].split("-")[0].strip().replace("h", "").replace("H", "")
            h_fin = act["horaire"].split("-")[1].strip().replace("h", "").replace("H", "")
            if ":" not in h_debut: h_debut = f"{int(h_debut):02d}:00"
            if ":" not in h_fin: h_fin = f"{int(h_fin):02d}:00"
            
            t_deb = datetime.datetime.strptime(f"{act['date']} {h_debut}", "%d/%m/%Y %H:%M")
            t_fin = datetime.datetime.strptime(f"{act['date']} {h_fin}", "%d/%m/%Y %H:%M")
            dates_param = f"{t_deb.strftime('%Y%m%dT%H%M%SZ')}/{t_fin.strftime('%Y%m%dT%H%M%SZ')}"
    except:
        pass

    base_url = "https://calendar.google.com/calendar/render?action=TEMPLATE"
    url = f"{base_url}&text={urllib.parse.quote(titre)}&dates={dates_param}&details={urllib.parse.quote(details)}&location={urllib.parse.quote(act['lieu'])}"
    return url

# --- CHARGEMENT DES DONNÉES ---
activites_brutes = charger()
for i, a in enumerate(activites_brutes):
    a["_index_original"] = i

# --- BANDEAU PRINCIPAL ---
st.markdown(
    f"""
    <div style="background-color: {C_BLEU_NUIT}; color: white; padding: 25px; border-radius: 8px; margin-bottom: 5px; border-bottom: 4px solid {C_BLEU_VIF};">
        <h1 style="color: white; margin: 0; font-size: 28px;">🚑 Activités bénévoles de secourisme</h1>
        <p style="color: #A0BED8; margin: 5px 0 0 0; font-weight: bold; font-size: 16px;">Console de Pilotage Interactive</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Barre de filtres principale
col_f1, col_f2 = st.columns([2, 1])
with col_f1:
    filtre_asso = st.radio("🔍 Filtrer l'affichage par association :", ["Toutes", "APC 🔵", "Unit 🔴"], horizontal=True)
with col_f2:
    st.write("") 
    if "act_selectionnee" not in st.session_state:
        st.session_state["act_selectionnee"] = None

# Filtrage de la liste selon le choix
asso_cible = None
if "APC" in filtre_asso: asso_cible = "APC"
elif "Unit" in filtre_asso: asso_cible = "Unit"

activites = [a for a in activites_brutes if asso_cible is None or a.get("asso") == lasso_cible]

# Tri automatique par date
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

# Statistiques exactes du PDF adaptées aux filtres
nb_total = len(activites)
nb_inscrit = sum(1 for a in activites if a.get("inscrit"))
nb_souhaite = nb_total - nb_inscrit
nb_apc = sum(1 for a in activites if a.get("asso") == "APC")
nb_unit = sum(1 for a in activites if a.get("asso") == "Unit")

# ═══════════════════════════════════════════════════════════════════════════════
#  ZONE DASHBOARD / CARTES STATISTIQUES (RETOUR DU MODÈLE PDF ORIGINAL)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(
    f"""
    <div style="background-color: #EEF3FA; padding: 15px; border-radius: 8px; margin-bottom: 25px; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px;">
        <div style="background-color: white; border-radius: 6px; padding: 12px; text-align: center; border-top: 5px solid {C_BLEU_VIF};">
            <div style="font-size: 26px; font-weight: bold; color: {C_BLEU_VIF};">{nb_total}</div>
            <div style="font-size: 11px; font-weight: bold; color: {C_GRIS_TEXTE}; border-top: 1px solid #DDD; padding-top: 4px; text-transform: uppercase;">TOTAL</div>
            <div style="font-size: 10px; color: #999;">{len(activites_a_venir)} à venir · {len(activites_passees)} passée(s)</div>
        </div>
        <div style="background-color: white; border-radius: 6px; padding: 12px; text-align: center; border-top: 5px solid {C_VERT};">
            <div style="font-size: 26px; font-weight: bold; color: {C_VERT};">{nb_inscrit}</div>
            <div style="font-size: 11px; font-weight: bold; color: {C_GRIS_TEXTE}; border-top: 1px solid #DDD; padding-top: 4px; text-transform: uppercase;">CONFIRMÉES</div>
            <div style="font-size: 10px; color: #999;">inscrit(e)</div>
        </div>
        <div style="background-color: white; border-radius: 6px; padding: 12px; text-align: center; border-top: 5px solid {C_ROUGE};">
            <div style="font-size: 26px; font-weight: bold; color: {C_ROUGE};">{nb_souhaite}</div>
            <div style="font-size: 11px; font-weight: bold; color: {C_GRIS_TEXTE}; border-top: 1px solid #DDD; padding-top: 4px; text-transform: uppercase;">SOUHAITÉES</div>
            <div style="font-size: 10px; color: #999;">à confirmer</div>
        </div>
        <div style="background-color: white; border-radius: 6px; padding: 12px; text-align: center; border-top: 5px solid {C_OR};">
            <div style="font-size: 26px; font-weight: bold; color: {C_OR};">{nb_apc} <span style="font-size:16px; color:#aaa;">/</span> {nb_unit}</div>
            <div style="font-size: 11px; font-weight: bold; color: {C_GRIS_TEXTE}; border-top: 1px solid #DDD; padding-top: 4px; text-transform: uppercase;">APC / UNIT</div>
            <div style="font-size: 10px; color: #999;">par association</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# --- PANEL DETAIL QUAND ON CLIQUE SUR UNE ACTIVITÉ (ZOOM) ---
if st.session_state["act_selectionnee"]:
    act_sel = st.session_state["act_selectionnee"]
    st.markdown(f"""
    <div style="background-color: {C_BLEU_CLAIR}; border: 2px solid {C_BLEU_VIF}; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
        <h4 style="margin:0; color:{C_BLEU_NUIT};">🔍 Zoom sur l'activité : {act_sel['activite']}</h4>
        <p style="margin:5px 0; font-size:13px;"><b>Association :</b> {act_sel['asso']} | <b>Date :</b> {act_sel['date']} | <b>Horaire :</b> {act_sel['horaire']} | <b>Lieu :</b> {act_sel['lieu']}</p>
        {f"<p style='margin:2px 0; font-size:12px; color:{C_OR};'>◆ <b>RDV Local :</b> {act_sel['rdv']}</p>" if act_sel.get('rdv') else ''}
        {f"<p style='margin:2px 0; font-size:12px; font-style:italic;'>✎ <b>Note :</b> {act_sel['note']}</p>" if act_sel.get('note') else ''}
    </div>
    """, unsafe_allow_html=True)
    
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        st.markdown(f'<a href="{generer_lien_google_calendar(act_sel)}" target="_blank" style="text-decoration:none;"><button style="background-color:#4285F4; color:white; border:none; padding:10px; border-radius:4px; font-weight:bold; cursor:pointer; width:100%;">📅 Ajouter ce DPS à mon Agenda</button></a>', unsafe_allow_html=True)
    with col_sel2:
        if st.button("Fermer le zoom", use_container_width=True):
            st.session_state["act_selectionnee"] = None
            st.rerun()

# --- ONGLETS PRINCIPAUX ---
onglet_voir, onglet_effectuees, onglet_ajouter = st.tabs([
    "📋 Activités à venir", "📜 Activités effectuées", "➕ Ajouter un secours"
])

# Fonction maîtresse d'affichage interactif
def afficher_liste_interactive(liste_a_afficher, cle_categorie):
    if not liste_a_afficher:
        st.info("Aucune activité enregistrée ici.")
        return

    # Regroupement par mois
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

        # Bandeau de Mois avec BOUTON DE TÉLÉCHARGEMENT PDF DU MOIS
        col_m1, col_m2 = st.columns([3, 1])
        with col_m1:
            st.markdown(
                f"""
                <div style="background-color: {C_BLEU_VIF}; color: white; padding: 10px 15px; border-radius: 4px 4px 0 0; margin-top: 15px; font-weight: bold; font-size: 15px; display: flex; justify-content: space-between; height: 38px; align-items: center;">
                    <span>📅 &nbsp; {label_mois}</span>
                    <span style="font-size: 13px; opacity: 0.9;">{nb_m} activité{'s' if nb_m > 1 else ''}</span>
                </div>
                """, unsafe_allow_html=True
            )
        with col_m2:
            st.write("") # Décalage pour aligner
            # Génération d'un fichier PDF contenant temporairement uniquement ce mois
            nom_fichier_mois = f"DPS_{label_mois.replace(' ', '_')}.pdf"
            try:
                generer_pdf(groupe["activites"]) # Utilise la fonction de ton fichier joint
                with open(PDF_FILE, "rb") as f_mois:
                    st.download_button(
                        label=f"🖨️ PDF {label_mois.split(' ')[0]}",
                        data=f_mois,
                        file_name=nom_fichier_mois,
                        mime="application/pdf",
                        key=f"dl_mois_{cle[0]}_{cle[1]}_{cle_categorie}",
                        use_container_width=True
                    )
            except:
                st.button(f"🖨️ PDF {label_mois.split(' ')[0]}", key=f"err_mois_{cle[0]}_{cle[1]}_{cle_categorie}", disabled=True, use_container_width=True)

        # En-tête des colonnes du tableau
        st.markdown(
            f"""
            <div style="background-color: {C_BLEU_MED}; color: white; padding: 6px 15px; font-size: 11px; font-weight: bold; display: flex; text-transform: uppercase; margin-bottom:4px;">
                <div style="width: 15%;">Orga.</div>
                <div style="width: 20%;">Date</div>
                <div style="width: 45%;">Activité · Lieu</div>
                <div style="width: 20%; text-align: right;">Horaire DPS</div>
            </div>
            """, unsafe_allow_html=True
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

            bg_color = "#FFFFFF" if idx % 2 == 0 else C_BLEU_PALE
            if not ok: bg_color = C_ROUGE_FOND
            text_color = C_ROUGE if not ok else C_GRIS_TEXTE
            asso_color = C_ROUGE if not ok else C_VERT
            act_color = C_ROUGE if not ok else C_BLEU_MED

            # Ligne d'activité et ses boutons d'actions
            col_ligne, col_actions = st.columns([5, 2])
            
            with col_ligne:
                st.markdown(
                    f"""
                    <div style="background-color: {bg_color}; padding: 10px 15px; display: flex; align-items: top; border-bottom: 1px solid #D8E2EE; color: {text_color}; min-height: 55px;">
                        <div style="width: 15%; font-weight: bold; color: {asso_color};">{symbole} {a.get('asso', '')}</div>
                        <div style="width: 23%; font-weight: bold;">{date_aff}</div>
                        <div style="width: 45%; font-weight: bold; color: {act_color};">{a.get('activite', '')}<br><span style="font-size:11px; font-weight:normal; color:#555;">📍 {a.get('lieu','')}</span></div>
                        <div style="width: 17%; text-align: right; font-weight: bold;">{a.get('horaire', '')}</div>
                    </div>
                    """, unsafe_allow_html=True
                )
                
            with col_actions:
                c_zoom, c_cal, c_edit, c_del = st.columns(4)
                with c_zoom:
                    if st.button("👁️", key=f"zoom_{idx_orig}_{cle_categorie}", help="Cliquez pour zoomer et voir le détail"):
                        st.session_state["act_selectionnee"] = a
                        st.rerun()
                with c_cal:
                    st.markdown(f'<a href="{generer_lien_google_calendar(a)}" target="_blank" style="text-decoration:none;"><button style="background-color:#e1eefc; border:1px solid #b6d7fa; border-radius:4px; height:35px; width:100%; cursor:pointer;" title="Ajouter à mon agenda">📅</button></a>', unsafe_allow_html=True)
                with c_edit:
                    btn_modifier = st.button("✏️", key=f"edit_{idx_orig}_{cle_categorie}")
                with c_del:
                    btn_supprimer = st.button("❌", key=f"del_{idx_orig}_{cle_categorie}")

            # --- LOGIQUE FORMULAIRE DE MODIFICATION ---
            if st.session_state.get(f"actif_edit_{idx_orig}", False) or btn_modifier:
                st.session_state[f"actif_edit_{idx_orig}"] = True
                with st.form(key=f"form_el_{idx_orig}_{cle_categorie}"):
                    m_asso = st.radio("Association", ["APC", "Unit"], index=0 if a["asso"] == "APC" else 1, horizontal=True)
                    m_activite = st.text_input("Activité", value=a["activite"])
                    m_lieu = st.text_input("Lieu", value=a["lieu"])
                    m_horaire = st.text_input("Horaire", value=a["horaire"])
                    m_rdv = st.text_input("RDV local", value=a["rdv"])
                    m_statut = st.radio("Statut", ["Inscrit(e) / Confirmé(e)", "Souhaité"], index=0 if a["inscrit"] else 1)
                    m_note = st.text_area("Note", value=a["note"])
                    
                    if st.form_submit_button("Enregistrer Changes"):
                        liste_brute = charger()
                        liste_brute[idx_orig] = {
                            "asso": m_asso, "date": a["date"], "activite": m_activite,
                            "lieu": m_lieu, "horaire": m_horaire, "rdv": m_rdv,
                            "inscrit": "Confirmé" in m_statut, "note": m_note
                        }
                        sauvegarder(liste_brute)
                        st.session_state[f"actif_edit_{idx_orig}"] = False
                        st.rerun()

            # --- LOGIQUE DE SUPPRESSION ---
            if st.session_state.get(f"actif_del_{idx_orig}", False) or btn_supprimer:
                st.session_state[f"actif_del_{idx_orig}"] = True
                st.warning(f"Supprimer définitivement : {a['activite']} ?")
                c_d1, c_d2 = st.columns(2)
                with c_d1:
                    if st.button("Oui, Supprimer", key=f"c_del_{idx_orig}_{cle_categorie}", type="primary"):
                        liste_brute = charger()
                        liste_brute.pop(idx_orig)
                        sauvegarder(liste_brute)
                        st.session_state[f"actif_del_{idx_orig}"] = False
                        st.rerun()
                with c_d2:
                    if st.button("Annuler", key=f"can_del_{idx_orig}_{cle_categorie}"):
                        st.session_state[f"actif_del_{idx_orig}"] = False
                        st.rerun()

legende_html = f"""
<h3 style="font-size: 15px; color: {C_BLEU_NUIT}; margin-bottom: 5px;">ℹ️ LÉGENDE & INFO</h3>
<div style="height: 2px; background-color: {C_BLEU_VIF}; margin-bottom: 12px;"></div>
<div style="display: flex; margin-bottom: 8px; align-items: center; font-size:12px;">
    <div style="background-color: {C_VERT}; color: white; width: 20px; height: 20px; border-radius: 4px; text-align: center; font-weight: bold; line-height: 20px; margin-right: 10px;">■</div>
    <b>Inscrit(e) / Confirmé(e)</b>
</div>
<div style="display: flex; margin-bottom: 8px; align-items: center; font-size:12px;">
    <div style="background-color: {C_ROUGE}; color: white; width: 20px; height: 20px; border-radius: 4px; text-align: center; font-weight: bold; line-height: 20px; margin-right: 10px;">→</div>
    <b>Souhaité(e) / En attente</b>
</div>
"""

# ═══════════════════════════════════════════════════════════════════════════════
#  ONGLET 1 : À VENIR
# ═══════════════════════════════════════════════════════════════════════════════
with onglet_voir:
    col_gauche, col_droite = st.columns([3, 1])
    with col_gauche:
        # BOUTON D'AGENDA GLOBAL (EN HAUT)
        if activites_a_venir:
            st.markdown(f'<a href="{generer_lien_google_calendar(activites_a_venir)}" target="_blank" style="text-decoration:none;"><button style="background-color:#1a73e8; color:white; border:none; padding:11px; border-radius:6px; font-weight:bold; cursor:pointer; width:100%; margin-bottom:15px;">📅 Ajouter les activités de la liste à mon Agenda</button></a>', unsafe_allow_html=True)
        afficher_liste_interactive(activites_a_venir, "avenir")
    with col_droite:
        st.markdown("### 🖨️ Impression Filtrée")
        st.caption(f"Le PDF complet inclura : **{filtre_asso}**")
        try:
            generer_pdf(activites) # Régénère le PDF global basé sur ton filtre choisi
            if os.path.exists(PDF_FILE):
                with open(PDF_FILE, "rb") as f:
                    st.download_button(label="📥 Télécharger le PDF complet", data=f, file_name=f"DPS_{filtre_asso.split(' ')[0]}.pdf", mime="application/pdf", use_container_width=True)
        except:
            st.info("Aperçu PDF indisponible")
        st.markdown("---")
        st.markdown(legende_html, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  ONGLET 2 : EFFECTUÉES
# ═══════════════════════════════════════════════════════════════════════════════
with onglet_effectuees:
    col_gauche, col_droite = st.columns([3, 1])
    with col_gauche:
        afficher_liste_interactive(activites_passees, "passees")
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
        horaire = st.text_input("Horaire DPS (ex: 14h00 - 18h00)")
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
                st.success("Activité ajoutée !")
                st.rerun()