// Küche eines Ortes aus dem Google-Primärtyp (orte.extras.google_primaertyp) ableiten.
// Allgemeine Typen ("restaurant", "cafe") ergeben keine Küche – dann bleibt das Feld leer.

export interface Kueche {
  slug: string;
  name: string;
}

const KUECHEN: Record<string, string> = {
  italian_restaurant: "Italienisch",
  pizza_restaurant: "Pizza",
  japanese_restaurant: "Japanisch",
  ramen_restaurant: "Ramen",
  sushi_restaurant: "Sushi",
  chinese_restaurant: "Chinesisch",
  dim_sum_restaurant: "Chinesisch",
  hot_pot_restaurant: "Chinesisch",
  korean_restaurant: "Koreanisch",
  korean_barbecue_restaurant: "Koreanisch",
  vietnamese_restaurant: "Vietnamesisch",
  thai_restaurant: "Thailändisch",
  indian_restaurant: "Indisch",
  pakistani_restaurant: "Indisch",
  nepalese_restaurant: "Indisch",
  asian_restaurant: "Asiatisch",
  asian_fusion_restaurant: "Asiatisch",
  indonesian_restaurant: "Asiatisch",
  filipino_restaurant: "Asiatisch",
  turkish_restaurant: "Türkisch",
  kebab_shop: "Döner & Kebab",
  greek_restaurant: "Griechisch",
  lebanese_restaurant: "Orientalisch",
  middle_eastern_restaurant: "Orientalisch",
  persian_restaurant: "Orientalisch",
  afghani_restaurant: "Orientalisch",
  syrian_restaurant: "Orientalisch",
  israeli_restaurant: "Orientalisch",
  falafel_restaurant: "Orientalisch",
  mediterranean_restaurant: "Mediterran",
  spanish_restaurant: "Spanisch",
  tapas_restaurant: "Spanisch",
  portuguese_restaurant: "Portugiesisch",
  french_restaurant: "Französisch",
  german_restaurant: "Deutsch",
  austrian_restaurant: "Deutsch",
  brewpub: "Brauhaus",
  american_restaurant: "Amerikanisch",
  hamburger_restaurant: "Burger",
  steak_house: "Steak",
  barbecue_restaurant: "Steak",
  mexican_restaurant: "Mexikanisch",
  latin_american_restaurant: "Lateinamerikanisch",
  peruvian_restaurant: "Lateinamerikanisch",
  brazilian_restaurant: "Lateinamerikanisch",
  argentinian_restaurant: "Lateinamerikanisch",
  african_restaurant: "Afrikanisch",
  ethiopian_restaurant: "Afrikanisch",
  seafood_restaurant: "Fisch & Meeresfrüchte",
  fish_and_chips_restaurant: "Fisch & Meeresfrüchte",
  vegan_restaurant: "Vegan & Vegetarisch",
  vegetarian_restaurant: "Vegan & Vegetarisch",
  breakfast_restaurant: "Frühstück & Brunch",
  brunch_restaurant: "Frühstück & Brunch",
  sandwich_shop: "Sandwiches & Bowls",
  deli: "Sandwiches & Bowls",
  fast_food_restaurant: "Fast Food",
  fine_dining_restaurant: "Fine Dining",
  bistro: "Bistro",
  gastropub: "Bistro",
  bar_and_grill: "Bistro",
  coffee_shop: "Kaffee",
  coffee_roastery: "Kaffee",
  tea_house: "Tee",
  bakery: "Bäckerei & Kuchen",
  pastry_shop: "Bäckerei & Kuchen",
  confectionery: "Bäckerei & Kuchen",
  dessert_shop: "Bäckerei & Kuchen",
  chocolate_shop: "Bäckerei & Kuchen",
  donut_shop: "Bäckerei & Kuchen",
  ice_cream_shop: "Eis",
};

/** URL-Slug aus einem Anzeigenamen ("Fisch & Meeresfrüchte" → "fisch-meeresfruechte"). */
export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/ä/g, "ae").replace(/ö/g, "oe").replace(/ü/g, "ue").replace(/ß/g, "ss")
    .normalize("NFKD").replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function kuecheVonTyp(primaertyp: unknown): Kueche | null {
  if (typeof primaertyp !== "string") return null;
  const name = KUECHEN[primaertyp];
  return name ? { slug: slugify(name), name } : null;
}
