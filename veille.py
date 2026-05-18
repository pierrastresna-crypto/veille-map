import requests
import smtplib
import json
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# ── Configuration ──────────────────────────────────────────────
TENDERAPI_KEY   = os.environ["TENDERAPI_KEY"]
GMAIL_ADDRESS   = os.environ["GMAIL_ADDRESS"]
GMAIL_PASSWORD  = os.environ["GMAIL_PASSWORD"]

DESTINATAIRES = [
    "contact@creativlight.fr",
    "mapping@creativlight.fr",
]

MOTS_CLES = [
    # Termes directs mapping
    "mapping", "vidéomapping", "video mapping",
    "vidéo mapping", "projection mapping",
    "videomapping",

    # Projection architecturale
    "projection architecturale", "projection facade",
    "projection façade", "projection monumentale",
    "projection sur facade", "projection sur façade",
    "projection sur batiment", "projection sur bâtiment",
    "projections visuelles", "projections visuelles et sonores",
    "vidéoprojection", "vidéo projection",
    "images animées sur façade", "images animées sur facade",

    # Son et lumière / spectacles lumineux
    "son et lumière", "son et lumiere",
    "spectacle son et lumière", "spectacle son et lumiere",
    "spectacle lumineux", "spectacle lumière",
    "spectacle de lumière", "spectacle de lumiere",
    "animation lumineuse", "animations lumineuses",
    "création lumineuse", "creations lumineuses",
    "mise en lumière", "mise en lumiere",

    # Parcours / fêtes
    "parcours lumière", "parcours lumineux",
    "fête des lumières", "fete des lumieres",
    "festival lumière", "festival lumieres",
    "nuit des lumières", "nuit des lumieres",
    "illuminations", "illuminations de noel",
    "illuminations de noël",

    # Scénographie
    "scénographie lumineuse", "scenographie lumineuse",
    "scénographie numérique", "scenographie numerique",
    "installation lumineuse", "installations lumineuses",
    "installation audiovisuelle", "installations audiovisuelles",

    # Fêtes de fin d'année / célébrations
    "fêtes de fin d'année", "fetes de fin d'annee",
    "fin d'année", "fin d'annee",
    "célébration", "celebration",
    "animations noel", "animations noël",

    # Codes CPV officiels BOAMP
    "92140000",   # Services de projection de vidéos
    "92312000",   # Services fournis par les arts du spectacle
    "92111300",   # Production de films et vidéos d'information
]

# ── Récupération des marchés BOAMP via TenderAPI ───────────────
def get_marches():
    resultats = []
    date_depuis = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    for mot in MOTS_CLES:
        try:
            r = requests.get(
                "https://tenderapi.fr/tenders",
                headers={"X-API-Key": TENDERAPI_KEY},
                params={
                    "q": mot,
                    "published_after": date_depuis,
                    "limit": 20,
                },
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                for item in data.get("results", []):
                    # Déduplication par id
                    if not any(x["id"] == item["id"] for x in resultats):
                        resultats.append(item)
        except Exception as e:
            print(f"Erreur pour '{mot}': {e}")

    return resultats

# ── Construction de l'email HTML ───────────────────────────────
def construire_email(marches):
    today = datetime.now().strftime("%d/%m/%Y")
    nb    = len(marches)

    if nb == 0:
        corps = f"""
        <h2>🔍 Veille vidéo mapping — {today}</h2>
        <p>Aucun nouveau marché trouvé cette semaine.</p>
        <p style="color:#888;font-size:12px;">Sources : BOAMP + TED via TenderAPI</p>
        """
        return corps

    lignes = ""
    for m in marches:
        titre    = m.get("title", "Sans titre")
        acheteur = m.get("buyer_name", "Non précisé")
        deadline = m.get("deadline", "Non précisée")
        parution = m.get("published_at", m.get("publication_date", "Non précisée"))
        budget   = m.get("budget_max", "Non précisé")
        region   = m.get("region", "Non précisée")
        lien     = m.get("url", "#")
        source   = m.get("source", "boamp").upper()

        budget_str = f"{budget:,} €".replace(",", " ") if isinstance(budget, (int, float)) else str(budget)

        lignes += f"""
        <tr>
          <td style="padding:12px;border-bottom:1px solid #eee">
            <strong><a href="{lien}" style="color:#1a1a2e;text-decoration:none">{titre}</a></strong><br>
            <span style="color:#555;font-size:13px">🏛 {acheteur} &nbsp;|&nbsp; 📍 {region}</span>
          </td>
          <td style="padding:12px;border-bottom:1px solid #eee;white-space:nowrap;color:#555;font-size:13px">
            📅 Publié : {parution}
          </td>
          <td style="padding:12px;border-bottom:1px solid #eee;white-space:nowrap;color:#555;font-size:13px">
            ⏰ Deadline : {deadline}
          </td>
          <td style="padding:12px;border-bottom:1px solid #eee;white-space:nowrap;color:#555;font-size:13px">
            💶 {budget_str}
          </td>
          <td style="padding:12px;border-bottom:1px solid #eee">
            <span style="background:#f0f0f0;padding:3px 8px;border-radius:4px;font-size:11px">{source}</span>
          </td>
        </tr>
        """

    corps = f"""
    <div style="font-family:Arial,sans-serif;max-width:900px;margin:auto">
      <h2 style="color:#1a1a2e">🎥 Veille vidéo mapping — {today}</h2>
      <p style="color:#444">{nb} nouveau(x) marché(s) trouvé(s) cette semaine</p>

      <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;border:1px solid #eee;border-radius:8px">
        <thead>
          <tr style="background:#1a1a2e;color:white">
            <th style="padding:12px;text-align:left">Marché</th>
            <th style="padding:12px;text-align:left">Publié le</th>
            <th style="padding:12px;text-align:left">Deadline</th>
            <th style="padding:12px;text-align:left">Budget</th>
            <th style="padding:12px;text-align:left">Source</th>
          </tr>
        </thead>
        <tbody>
          {lignes}
        </tbody>
      </table>

      <p style="color:#888;font-size:12px;margin-top:20px">
        Sources : BOAMP + TED (Europe) via TenderAPI · Mots-clés : mapping, projection, son et lumière, illuminations…
      </p>
    </div>
    """
    return corps

# ── Envoi de l'email ───────────────────────────────────────────
def envoyer_email(corps_html, nb_marches):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎥 Veille mapping — {nb_marches} marché(s) — {datetime.now().strftime('%d/%m/%Y')}"
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = ", ".join(DESTINATAIRES)
    msg.attach(MIMEText(corps_html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, DESTINATAIRES, msg.as_string())
    print(f"Email envoyé à {DESTINATAIRES}")

# ── Point d'entrée ─────────────────────────────────────────────
if __name__ == "__main__":
    print("Démarrage de la veille vidéo mapping...")
    marches = get_marches()
    print(f"{len(marches)} marché(s) trouvé(s)")
    corps   = construire_email(marches)
    envoyer_email(corps, len(marches))
    print("Terminé.")
