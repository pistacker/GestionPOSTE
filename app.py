import streamlit as st
import json
import os
import datetime
# On importe la fonction de génération PDF depuis ton script existant
from gestion_dps import generer_pdf, JSON_FILE, PDF_FILE, MOIS, JOURS, charger, sauvegarder

st.set_page_config(page_title="Gestion DPS - Secourisme", page_icon="🚑", layout="wide")

st.title("🚑 Gestion des Activités de Secours")
st.write("Consultez, ajoutez, modifiez ou supprimez les activités en temps réel.")

# --- CHARGEMENT DES DONNÉES ---
activites = charger()

# Tri automatique par date pour l'affichage
try:
    activites.sort(key=lambda x: datetime.datetime.strptime(x["date"], "%d/%m/%Y"))
except Exception:
    pass

# --- EN-TÊTE / STATISTIQUES ---
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
    "📋 Liste & PDF", "➕ Ajouter", "✏️ Modifier", "❌ Supprimer"
])

# ═══════════════════════════════════════════════════════════════════════════════
#  ONGLET 1 : VOIR & TÉLÉCHARGER
# ═══════════════════════════════════════════════════════════════════════════════
with onglet_voir:
    st.subheader("Liste des activités enregistrées")
    
    # Bouton pour télécharger le PDF mis à jour
    if os.path.exists(PDF_FILE):
        with open(PDF_FILE, "rb") as f:
            st.download_button(
                label="📥 Télécharger le PDF Liste_activites_secours.pdf",
                data=f,
                file_name="Liste_activites_secours.pdf",
                mime="application/pdf"
            )
    else:
        st.info("Cliquez sur le bouton ci-dessous pour générer le premier PDF.")
        if st.button("Générer le PDF"):
            generer_pdf()
            st.rerun()

    if not activites:
        st.info("Aucune activité enregistrée.")
    else:
        # Affichage sous forme de tableau ou de cartes propres
        for i, a in enumerate(activites):
            statut = "✅ Confirmé (■)" if a["inscrit"] else "⏳ Souhaité (→)"
            color = "#EAF7EF" if a["inscrit"] else "#FEF0EE"
            
            with st.container():
                st.markdown(
                    f"""
                    <div style="background-color: {color}; padding: 15px; border-radius: 5px; margin-bottom: 10px; border: 1px solid #ddd;">
                        <h4>{statut} | {a['asso']} - {a['date']} : {a['activite']}</h4>
                        <p>📍 <b>Lieu :</b> {a['lieu']} | ⏰ <b>Horaire DPS :</b> {a['horaire']} {f'| 🏠 <b>RDV Local :</b> {a["rdv"]}' if a["rdv"] else ''}</p>
                        {f'<p style="font-style: italic; color: #555;">📝 Note : {a["note"]}</p>' if a["note"] else ''}
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

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
                    "asso": asso,
                    "date": date_str,
                    "activite": activite,
                    "lieu": lieu,
                    "horaire": horaire,
                    "rdv": rdv,
                    "inscrit": statut_choix == "Inscrit(e) / Confirmé(e)",
                    "note": note
                }
                activites.append(nouvelle_act)
                sauvegarder(activites) # Sauvegarde JSON + régénère le PDF via ton script
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
                    "asso": m_asso,
                    "date": m_date_obj.strftime("%d/%m/%Y"),
                    "activite": m_activite,
                    "lieu": m_lieu,
                    "horaire": m_horaire,
                    "rdv": m_rdv,
                    "inscrit": m_statut == "Inscrit(e) / Confirmé(e)",
                    "note": m_note
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