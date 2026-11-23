// Admin-Bereich – GitHub Actions lesen (und ab Stufe 1c starten), Plan Admin-Dashboard 3.4 / E3.
// Token: Fine-grained, nur dieses Repo, Actions: read and write, Variables: read. Kommt als ADMIN_GITHUB_TOKEN über
// deploy.yml in web/.env.local. Ohne Token zeigt das Cockpit „nicht verbunden“ statt einer Ampel.
import "server-only";

export const WORKFLOWS = {
  scrape: "scrape.yml",
  deploy: "deploy.yml",
  waechter: "waechter.yml",
  geburtstag: "geburtstag.yml",
  magazin: "magazin.yml",
} as const;
export type WorkflowName = keyof typeof WORKFLOWS;

export interface WorkflowLauf {
  status: string; // queued | in_progress | completed …
  conclusion: string | null; // success | failure | cancelled …
  erstellt_am: string;
  url: string;
  titel: string;
}

export type GithubErgebnis =
  | { art: "ok"; lauf: WorkflowLauf | null; tokenAblauf: string | null }
  | { art: "kein_token" }
  | { art: "fehler"; meldung: string };

function repo(): string {
  return process.env.ADMIN_GITHUB_REPO?.trim() || "YannickFetsch89/dda";
}

function token(): string | null {
  return process.env.ADMIN_GITHUB_TOKEN?.trim() || null;
}

/** Arbeitszweig: Deploy und Läufe laufen auf diesem Zweig */
export const ZWEIG = "claude/setup-project-structure-5QNOf";

/** Startet einen Workflow per workflow_dispatch (braucht Actions: write). GitHub antwortet mit 204 ohne Lauf-ID. */
export async function workflowStarten(
  name: WorkflowName,
  inputs?: Record<string, string>,
): Promise<{ ok: true } | { ok: false; meldung: string }> {
  const t = token();
  if (!t) return { ok: false, meldung: "GitHub nicht verbunden (Token fehlt)." };
  try {
    const antwort = await fetch(`https://api.github.com/repos/${repo()}/actions/workflows/${WORKFLOWS[name]}/dispatches`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${t}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(inputs ? { ref: ZWEIG, inputs } : { ref: ZWEIG }),
      cache: "no-store",
      signal: AbortSignal.timeout(8000),
    });
    if (antwort.status === 204) return { ok: true };
    return { ok: false, meldung: `GitHub antwortet mit ${antwort.status}` };
  } catch (e) {
    return { ok: false, meldung: e instanceof Error ? e.message : String(e) };
  }
}

/** Letzter Lauf eines Workflows (egal welcher Zweig oder Auslöser). */
export async function letzterLauf(name: WorkflowName): Promise<GithubErgebnis> {
  const t = token();
  if (!t) return { art: "kein_token" };
  try {
    const antwort = await fetch(`https://api.github.com/repos/${repo()}/actions/workflows/${WORKFLOWS[name]}/runs?per_page=1`, {
      headers: { Authorization: `Bearer ${t}`, Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28" },
      cache: "no-store",
      signal: AbortSignal.timeout(6000),
    });
    if (!antwort.ok) return { art: "fehler", meldung: `GitHub antwortet mit ${antwort.status}` };
    const daten = (await antwort.json()) as {
      workflow_runs?: { status: string; conclusion: string | null; created_at: string; html_url: string; display_title?: string }[];
    };
    const r = daten.workflow_runs?.[0];
    return {
      art: "ok",
      tokenAblauf: antwort.headers.get("github-authentication-token-expiration"),
      lauf: r ? { status: r.status, conclusion: r.conclusion, erstellt_am: r.created_at, url: r.html_url, titel: r.display_title ?? "" } : null,
    };
  } catch (e) {
    return { art: "fehler", meldung: e instanceof Error ? e.message : String(e) };
  }
}
