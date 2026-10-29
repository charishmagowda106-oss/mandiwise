// Friendly emoji per crop — matched on name first, then category, with a sprout fallback.
const NAME_EMOJI = [
  [/tomato/i, '🍅'], [/potato/i, '🥔'], [/onion/i, '🧅'], [/maize|corn/i, '🌽'],
  [/rice|paddy/i, '🍚'], [/wheat/i, '🌾'], [/jowar|sorghum|bajra|millet|ragi/i, '🌾'],
  [/gram|chana|lentil|tur\b|toor|pea\b/i, '🫘'], [/soybean/i, '🫘'],
  [/groundnut|peanut/i, '🥜'], [/sunflower/i, '🌻'], [/sesame/i, '🌰'],
  [/banana/i, '🍌'], [/grape/i, '🍇'], [/apple/i, '🍎'], [/mango/i, '🥭'],
  [/coconut/i, '🥥'], [/cotton/i, '💮'], [/chilli|chili|pepper/i, '🌶️'],
  [/okra|ladies/i, '🥬'], [/brinjal|eggplant/i, '🍆'], [/capsicum/i, '🫑'],
  [/carrot/i, '🥕'], [/sweet.?potato/i, '🍠'], [/turmeric/i, '🟡'],
  [/areca|betel/i, '🌴'], [/tobacco/i, '🍃'], [/cabbage|cauliflower/i, '🥬'],
];

const CATEGORY_EMOJI = [
  [/vegetable/i, '🥕'], [/fruit/i, '🥭'], [/pulse|legume/i, '🫘'],
  [/cereal|grain|millet/i, '🌾'], [/oilseed/i, '🥜'], [/spice/i, '🌶️'],
  [/plantation|coconut/i, '🌴'], [/commercial|fiber|cash/i, '💮'],
];

export const cropEmoji = (name = '', category = '') => {
  for (const [pattern, emoji] of NAME_EMOJI) if (pattern.test(name)) return emoji;
  for (const [pattern, emoji] of CATEGORY_EMOJI) if (pattern.test(category)) return emoji;
  return '🌱';
};
