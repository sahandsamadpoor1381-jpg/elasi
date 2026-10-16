/**
 * Formatting helpers — one source for how money and numbers are shown.
 *
 * Money rule: the API and the database always speak RIAL (integers).
 * Customers always see TOMAN, derived here and never computed from
 * anything but the server value.
 */

const tomanFormatter = new Intl.NumberFormat("fa-IR");
const numberFormatter = new Intl.NumberFormat("fa-IR");


export function rialToToman(priceRial: number): number {
  return Math.floor(priceRial / 10);
}


/** "۱٬۲۵۰٬۰۰۰" — amount only, no unit. */
export function formatToman(priceRial: number): string {
  return tomanFormatter.format(rialToToman(priceRial));
}


/** "۱٬۲۵۰٬۰۰۰ تومان" */
export function formatTomanWithUnit(priceRial: number): string {
  return `${formatToman(priceRial)} تومان`;
}


export function formatNumber(value: number): string {
  return numberFormatter.format(value);
}


export function formatCount(
  value: number,
  singular: string,
  plural: string = singular,
): string {
  return `${formatNumber(value)} ${value === 1 ? singular : plural}`;
}


const GENDER_LABELS: Record<string, string> = {
  women: "زنانه",
  men: "مردانه",
  unisex: "زنانه و مردانه",
};


export function genderLabel(gender: string): string {
  return GENDER_LABELS[gender] ?? gender;
}


const MATERIAL_LABELS: Record<string, string> = {
  gold: "طلا",
  silver: "نقره",
};


export function materialLabel(material: string): string {
  return MATERIAL_LABELS[material] ?? material;
}


const ORDERING_LABELS: Record<string, string> = {
  newest: "جدیدترین",
  featured: "پیشنهاد ELASI",
  price_asc: "ارزان‌ترین",
  price_desc: "گران‌ترین",
  name: "ترتیب الفبا",
};


export function orderingLabel(ordering: string): string {
  return ORDERING_LABELS[ordering] ?? ORDERING_LABELS.newest;
}
