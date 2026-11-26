"""Tests für tools/meta_pruefen.py (Social-Plan Schritt 0): Reel-Parameter, Atom-Prüfung, Token nie in der URL."""
import struct
import tempfile
import unittest
from pathlib import Path

from tools import meta_pruefen as mp


def _atom(name: bytes, inhalt: bytes = b"") -> bytes:
    return struct.pack(">I4s", 8 + len(inhalt), name) + inhalt


class ReelParameter(unittest.TestCase):
    def test_befehl_hat_meta_vorgaben(self):
        befehl = " ".join(mp.ffmpeg_reel_befehl(["a.jpg", "b.jpg"], "ziel.mp4"))
        for teil in ("-c:v libx264", "-pix_fmt yuv420p", "-r 30", "-flags +cgop", "-movflags +faststart",
                     "-use_editlist 0", "-c:a aac", "-ar 48000", "-ac 2", "1080:1920"):
            self.assertIn(teil, befehl)

    def test_atome_moov_vor_mdat_ohne_elst(self):
        with tempfile.TemporaryDirectory() as d:
            gut = Path(d) / "gut.mp4"
            gut.write_bytes(_atom(b"ftyp", b"isom") + _atom(b"moov", _atom(b"trak")) + _atom(b"mdat", b"\0" * 16))
            self.assertEqual(mp.mp4_atome(str(gut)), ["ftyp", "moov", "mdat"])
            schlecht = Path(d) / "schlecht.mp4"
            schlecht.write_bytes(_atom(b"ftyp") + _atom(b"mdat", b"\0" * 8) + _atom(b"moov", _atom(b"edts", _atom(b"elst"))))
            atome = mp.mp4_atome(str(schlecht))
            self.assertLess(atome.index("mdat"), atome.index("moov"))
            self.assertIn("elst!", atome)
            probleme = mp.video_pruefen(str(schlecht))
            self.assertTrue(any("moov" in p for p in probleme))
            self.assertTrue(any("elst" in p for p in probleme))


class TokenSchutz(unittest.TestCase):
    def test_token_steht_im_kopf_nicht_in_der_url(self):
        meta = mp.Meta("GEHEIM123")
        anfrage = meta.client.build_request("GET", f"{mp.GRAPH}/me", params={"fields": "id"})
        self.assertNotIn("GEHEIM123", str(anfrage.url))
        self.assertEqual(anfrage.headers["Authorization"], "Bearer GEHEIM123")

    def test_pflichtrechte_wie_plan(self):
        self.assertIn("ads_read", mp.PFLICHT_RECHTE)
        self.assertIn("instagram_content_publish", mp.PFLICHT_RECHTE)
        self.assertIn("pages_manage_posts", mp.PFLICHT_RECHTE)


if __name__ == "__main__":
    unittest.main()
