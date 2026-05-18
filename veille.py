import requests
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# ── Configuration ──────────────────────────────────────────────
GMAIL_ADDRESS  = os.environ["GMAIL_ADDRESS"]
GMAIL_PASSWORD = os.environ["GMAIL_PASSWORD"]

DESTINATAIRES = [
    "contact@creativlight.fr",
    "mapping@creativlight.fr",
]

MOTS_CLES = [
    "mapping", "vidéomapping", "video mapping", "videomapping",
    "projection mapping", "projection architecturale",
    "projection facade", "projection façade",
    "projection monumentale", "projection sur facade",
    "projection sur bâtiment", "projections visuelles",
    "vidéoprojection", "images animées sur façade",
    "son et lumière", "son et lumiere",
    "spectacle son et lumière", "spectacle lumineux",
    "spectacle de lumière", "animation lumineuse",
    "animations lumineuses", "mise en lumière",
    "parcours lumière", "parcours lumineux",
    "fête des lumières", "festival lumière",
    "nuit des lumières", "illuminations",
    "scénographie lumineuse", "scénographie numérique",
    "installation lumineuse", "installation audiovisuelle",
    "fêtes de fin d'année", "fin d'année",
    "célébration", "animations noel",
]

CPV_CODES = ["92140000", "92312000", "92111300"]

BOAMP_URL = "https://boamp-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/boamp/records"

# ── Récupération via API BOAMP officielle ──────────────────────
def get_marches():
    resultats = []
    date_depuis = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    ids_vus = set()

    def ajouter(items):
        for item in items:
            uid = item.get("idweb") or item.get("id_boamp") or str(item)
            if uid not in ids_vus:
                ids_vus.add(uid)
                resultats.append(item)

    # Recherche par mots-clés dans l'objet du marché
    for mot in MOTS_CLES:
        try:
            r = requests.get(
                BOAMP_URL,
                params={
                    "where": f'objet like "%{mot}%" and dateparution >= "{date_depuis}"',
                    "limit": 20,
                    "order_by": "dateparution desc",
                },
                timeout=15,
            )
            if r.status_code == 200:
                ajouter(r.json().get("results", []))
            else:
                print(f"Erreur HTTP {r.status_code} pour '{mot}'")
        except Exception as e:
            print(f"Erreur mot-clé '{mot}': {e}")

    # Recherche par codes CPV
    for cpv in CPV_CODES:
        try:
            r = requests.get(
                BOAMP_URL,
                params={
                    "where": f'cpv like "%{cpv}%" and dateparution >= "{date_depuis}"',
                    "limit": 50,
                    "order_by": "dateparution desc",
                },
                timeout=15,
            )
            if r.status_code == 200:
                ajouter(r.json().get("results", []))
            else:
                print(f"Erreur HTTP {r.status_code} pour CPV '{cpv}'")
        except Exception as e:
            print(f"Erreur CPV '{cpv}': {e}")

    return resultats

# ── Construction de l'email HTML ───────────────────────────────
def formater_date(d):
    try:
        return datetime.strptime(str(d)[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        return d or "Non précisée"

def construire_email(marches):
    today = datetime.now().strftime("%d/%m/%Y")
    nb    = len(marches)

    if nb == 0:
        return f"""
        <div style="font-family:Arial,sans-serif;max-width:900px;margin:auto">
          <h2 style="color:#1a1a2e">🎥 Veille vidéo mapping — {today}</h2>
          <p>Aucun nouveau marché trouvé cette semaine.</p>
          <p style="color:#888;font-size:12px;">Source : API BOAMP officielle (DILA)</p>
        </div>
        """

    lignes = ""
    for m in marches:
        titre    = m.get("objet") or m.get("titre") or "Sans titre"
        acheteur = m.get("nomacheteur") or m.get("acheteur") or "Non précisé"
        parution = formater_date(m.get("dateparution"))
        deadline = formater_date(m.get("datelimitereponse") or m.get("date_limite"))
        dept     = m.get("department") or m.get("lieu") or ""
        idweb    = m.get("idweb") or ""
        lien     = f"https://www.boamp.fr/pages/avis/?q=idweb:{idweb}" if idweb else "#"

        lignes += f"""
        <tr>
          <td style="padding:12px;border-bottom:1px solid #eee">
            <strong><a href="{lien}" style="color:#1a1a2e;text-decoration:none">{titre}</a></strong><br>
            <span style="color:#555;font-size:13px">🏛 {acheteur} &nbsp;|&nbsp; 📍 {dept}</span>
          </td>
          <td style="padding:12px;border-bottom:1px solid #eee;white-space:nowrap;color:#555;font-size:13px">
            📅 {parution}
          </td>
          <td style="padding:12px;border-bottom:1px solid #eee;white-space:nowrap;color:#555;font-size:13px">
            ⏰ {deadline}
          </td>
          <td style="padding:12px;border-bottom:1px solid #eee">
            <span style="background:#e8f4fd;color:#1a6fa8;padding:3px 8px;border-radius:4px;font-size:11px">BOAMP</span>
          </td>
        </tr>
        """

    return f"""
    <div style="font-family:Arial,sans-serif;max-width:900px;margin:auto">
      <h2 style="color:#1a1a2e">🎥 Veille vidéo mapping — {today}</h2>
      <p style="color:#444">{nb} marché(s) trouvé(s) sur les 30 derniers jours</p>
      <table width="100%" cellpadding="0" cellspacing="0"
             style="border-collapse:collapse;border:1px solid #eee">
        <thead>
          <tr style="background:#1a1a2e;color:white">
            <th style="padding:12px;text-align:left">Marché</th>
            <th style="padding:12px;text-align:left">Publié le</th>
            <th style="padding:12px;text-align:left">Deadline</th>
            <th style="padding:12px;text-align:left">Source</th>
          </tr>
        </thead>
        <tbody>{lignes}</tbody>
      </table>
      <p style="color:#888;font-size:12px;margin-top:20px">
        Source : API BOAMP officielle (DILA) · CPV surveillés : 92140000, 92312000, 92111300
      </p>
    </div>
    """

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
    corps = construire_email(marches)
    envoyer_email(corps, len(marches))
    print("Terminé.")
