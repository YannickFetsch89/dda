// Gemeinsame Schlüssel (Secrets) bereinigen – dieselbe Regel wie deploy.yml (tr -d ' \r\n\t') und
// pipeline/schluessel.py. Livetest 24.11.2026: Ein Zeilenumbruch im Newsletter-Secret machte alle Links ungültig.
export function schluesselBereinigen(s: string | null | undefined): string {
  return (s ?? "").replace(/[ \r\n\t]/g, "");
}
