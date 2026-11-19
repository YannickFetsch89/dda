// Kontozustand vor dem ersten Paint (Plan Mein Bereich 3.0): setzt html[data-konto] aus dem Hinweis-Cookie ddd_konto
// (0/1), ohne Cookie nichts. Liest body nicht (im <head> noch nicht da). Steht nur bei KONTEN_AKTIV im HTML (layout.tsx).
// Danach hält kontoAttributAbgleichen() (merk-store.ts) Attribut und Cookie gleich.
export const KONTO_SCRIPT = `try{var k=document.cookie.match(/(?:^|;\\s*)ddd_konto=([01])(?:;|$)/);if(k)document.documentElement.dataset.konto=k[1]}catch(e){}`;
