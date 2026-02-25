"""
test_instagram.py – DiesDasDüsseldorf
Schnelltest für die Instagram Graph API Verbindung.
Schritt 1: Account-ID ermitteln
Schritt 2: Test-Post veröffentlichen (optional)
"""
import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://graph.facebook.com/v21.0"
TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")

if not TOKEN:
    print("FEHLER: INSTAGRAM_ACCESS_TOKEN fehlt in der .env Datei")
    sys.exit(1)


def schritt1_account_id_finden():
    """Findet die Instagram Business Account-ID über die verknüpfte Facebook Page."""
    print("\n=== Schritt 1: Instagram Account-ID ermitteln ===\n")

    # Alle Pages abrufen auf die der Token Zugriff hat
    url = f"{API_URL}/me/accounts"
    params = {"access_token": TOKEN, "fields": "id,name,instagram_business_account"}

    try:
        antwort = httpx.get(url, params=params, timeout=15)
        daten = antwort.json()
    except Exception as e:
        print(f"FEHLER: Netzwerkfehler – {e}")
        return None

    if "error" in daten:
        print(f"FEHLER von Meta API: {daten['error'].get('message', daten['error'])}")
        print("\nMögliche Ursache: Token fehlt die Berechtigung 'pages_show_list'")
        return None

    pages = daten.get("data", [])
    if not pages:
        print("Keine Facebook Pages gefunden.")
        print("Stelle sicher dass dein Instagram-Konto als Business/Creator-Konto")
        print("mit einer Facebook Page verknüpft ist.")
        return None

    print(f"{len(pages)} Facebook Page(s) gefunden:\n")
    instagram_id = None

    for page in pages:
        page_name = page.get("name", "?")
        page_id = page.get("id", "?")
        ig = page.get("instagram_business_account", {})
        ig_id = ig.get("id") if ig else None

        print(f"  Page: {page_name} (ID: {page_id})")

        if ig_id:
            print(f"  → Instagram Business Account-ID: {ig_id}")
            instagram_id = ig_id
        else:
            print("  → Kein Instagram Business Account verknüpft")
        print()

    if instagram_id:
        print(f"✓ Trage diese ID in deine .env ein:")
        print(f"  INSTAGRAM_ACCOUNT_ID={instagram_id}\n")
    else:
        print("FEHLER: Kein Instagram Business Account gefunden.")
        print("Gehe zu Instagram → Einstellungen → Konto → Zu Professional-Konto wechseln")

    return instagram_id


def schritt2_test_post(ig_account_id: str):
    """Postet ein Testbild auf Instagram."""
    print("\n=== Schritt 2: Test-Post veröffentlichen ===\n")

    # Öffentlich zugängliches Testbild (Unsplash – Düsseldorf Skyline)
    test_bild_url = "https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=1080&q=80"
    test_caption = (
        "🧪 Test-Post – dies.das.düsseldorf Pipeline läuft!\n\n"
        "Dieser Post wurde automatisch durch die DDA-Pipeline erstellt.\n\n"
        "#düsseldorf #test #diesdasduesseldorf"
    )

    print(f"Bild-URL: {test_bild_url}")
    print(f"Caption:  {test_caption[:80]}...\n")

    # Schritt A: Media-Container erstellen
    print("Schritt A: Erstelle Media-Container ...")
    url_a = f"{API_URL}/{ig_account_id}/media"
    params_a = {
        "image_url": test_bild_url,
        "caption": test_caption,
        "access_token": TOKEN,
    }

    try:
        antwort_a = httpx.post(url_a, params=params_a, timeout=30)
        daten_a = antwort_a.json()
    except Exception as e:
        print(f"FEHLER: Netzwerkfehler – {e}")
        return False

    if "error" in daten_a:
        print(f"FEHLER: {daten_a['error'].get('message', daten_a['error'])}")
        return False

    creation_id = daten_a.get("id")
    if not creation_id:
        print(f"FEHLER: Keine creation_id erhalten. Antwort: {daten_a}")
        return False

    print(f"✓ Media-Container erstellt (ID: {creation_id})")

    # Schritt B: Container veröffentlichen
    print("Schritt B: Veröffentliche Container ...")
    url_b = f"{API_URL}/{ig_account_id}/media_publish"
    params_b = {
        "creation_id": creation_id,
        "access_token": TOKEN,
    }

    try:
        antwort_b = httpx.post(url_b, params=params_b, timeout=30)
        daten_b = antwort_b.json()
    except Exception as e:
        print(f"FEHLER: Netzwerkfehler – {e}")
        return False

    if "error" in daten_b:
        print(f"FEHLER: {daten_b['error'].get('message', daten_b['error'])}")
        return False

    post_id = daten_b.get("id")
    if post_id:
        print(f"\n✓ POST ERFOLGREICH! Instagram Post-ID: {post_id}")
        print("→ Schau jetzt auf deinem Instagram-Profil nach dem Test-Post!")
        return True
    else:
        print(f"FEHLER: Keine Post-ID erhalten. Antwort: {daten_b}")
        return False


if __name__ == "__main__":
    # Schritt 1: Account-ID finden
    ig_id = os.getenv("INSTAGRAM_ACCOUNT_ID", "")

    if not ig_id:
        ig_id = schritt1_account_id_finden()
        if not ig_id:
            print("\nTest abgebrochen – bitte zuerst Instagram-Konto korrekt verknüpfen.")
            sys.exit(1)
        # Fragen ob gleich posten
        antwort = input("Account-ID gefunden. Test-Post jetzt veröffentlichen? (j/n): ")
        if antwort.lower() != "j":
            print("Abgebrochen. Trage die Account-ID in .env ein und starte erneut.")
            sys.exit(0)
    else:
        print(f"\n✓ INSTAGRAM_ACCOUNT_ID aus .env geladen: {ig_id}")
        antwort = input("Test-Post auf Instagram veröffentlichen? (j/n): ")
        if antwort.lower() != "j":
            print("Abgebrochen.")
            sys.exit(0)

    # Schritt 2: Test-Post
    erfolg = schritt2_test_post(ig_id)
    sys.exit(0 if erfolg else 1)
