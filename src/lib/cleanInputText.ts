// Expand common English contractions with configurable ambiguities.
// Options:
//   treatSAs: "is" | "has" | "possessive"  (default "is")
//   treatDAssumes: "would" | "had"         (default "would")
export function expandContractions(
  input: string,
  {
    treatSAs = "is",
    treatDAssumes = "would",
  }: {
    treatSAs?: "is" | "has" | "possessive";
    treatDAssumes?: "would" | "had";
  } = {}
): string {
  // 1) Normalize curly quotes to straight
  let text = input
    .replace(/[’‘]/g, "'")
    .replace(/[“”]/g, '"');

  // 2) A helper to apply a batch of regex rules
  type Rule = [RegExp, string | ((...m: string[]) => string)];
  const applyRules = (t: string, rules: Rule[]) =>
    rules.reduce((acc, [re, rep]) => acc.replace(re, rep as any), t);

  // 3) Irregular & special cases (run early)
  const irregularRules: Rule[] = [
    [/\bwon't\b/gi, "will not"],
    [/\bcan't\b/gi, "cannot"],
    [/\bshan't\b/gi, "shall not"],
    [/\bain't\b/gi, "is not"],       // heuristic
    [/\blet's\b/gi, "let us"],
    [/\bma'am\b/gi, "madam"],
    [/\bc'mon\b/gi, "come on"],
    [/\by'all\b/gi, "you all"],
    // y'all variants
    [/\by'all're\b/gi, "you all are"],
    [/\by'all've\b/gi, "you all have"],
    [/\by'all'd\b/gi, "you all would"],
    [/\by'all'd've\b/gi, "you all would have"],
  ];

  // 4) Stacked forms first (…'d've, …'ll've)
  const stackedRules: Rule[] = [
    // would/had + have
    [
      /\b(\w+)'d've\b/gi,
      (_all, w) => `${w} ${treatDAssumes} have`,
    ],
    // will + have
    [/\b(\w+)'ll've\b/gi, (_all, w) => `${w} will have`],
  ];

  // 5) General families
  const generalRules: Rule[] = [
    // Negative n't (don't, isn't, couldn't…)
    [/\b(\w+)n't\b/gi, (_all, w) => `${w} not`],

    // 're  (we're, they're, you're, where're…)
    [
      /\b(you|we|they|who|what|where|when|why|how|there|here|that|these|those)'re\b/gi,
      (_all, p1) => `${p1} are`,
    ],

    // 've  (I've, you've, we've, they've, who've, would’ve etc.)
    // We purposefully keep it broad for heads that often occur with 've.
    [/\b(i|you|we|they|who|there|could|would|should|might|must)'ve\b/gi, (_a, p1) => `${p1} have`],

    // 'll  (I'll, you'll, it'll, that'll, there'll…)
    [
      /\b(i|you|he|she|it|we|they|there|that|these|those|who|what|where|when|why|how)'ll\b/gi,
      (_all, p1) => `${p1} will`,
    ],

    // 'd   (I'd, you'd, he'd… → would/had)
    [
      /\b(i|you|he|she|it|we|they)'d\b/gi,
      (_all, p1) => `${p1} ${treatDAssumes}`,
    ],

    // 'm   (I'm)
    [/\bi'm\b/gi, "i am"],
  ];

  // 6) Smarter handling for "'s"
  // We try to expand to "is"/"has" for common copular/aux heads; otherwise leave as possessive if chosen.
  const copulaHeads =
    "(it|that|there|here|this|these|those|who|what|where|when|why|how|he|she|it)";
  const sRules: Rule[] =
    treatSAs === "possessive"
      ? [
          // If user wants possessive behavior, *only* expand where it's almost certainly "is/has":
          [new RegExp(String.raw`\b${copulaHeads}'s\b`, "gi"), (_a, w) => `${w} is`],
          [/\bwho's\b/gi, "who is"], // common question head
          [/\bwhat's\b/gi, "what is"],
          [/\bwhere's\b/gi, "where is"],
          [/\bwhen's\b/gi, "when is"],
          [/\bwhy's\b/gi, "why is"],
          [/\bhow's\b/gi, "how is"],
          // Otherwise keep possessive by removing the apostrophe only if you prefer that downstream,
          // but here we *leave it as-is* to avoid altering meaning prematurely.
        ]
      : [
          // Expand everything to the selected auxiliary ("is"/"has")
          [/\b(\w+)'s\b/gi, (_a, w) => `${w} ${treatSAs}`],
        ];

  // 7) Do multiple passes to fully expand stacked/nested forms
  const all = [...irregularRules, ...stackedRules, ...generalRules, ...sRules];

  let prev: string;
  let guard = 0;
  do {
    prev = text;
    text = applyRules(text, all);
    guard += 1;
  } while (text !== prev && guard < 5); // 5 passes is plenty for real text

  return text;
}

// Main text cleaning function for Auslan processing
export const cleanInputText = (text: string): string => {
  return expandContractions(text, { treatSAs: "is", treatDAssumes: "would" })
    .trim()                         // Remove leading/trailing whitespace
    .replace(/[^\w\s]|_/g, "")      // Remove remaining symbols/underscores
    .replace(/\s+/g, " ")           // Normalize whitespace
    .replace(/\b[Ii]\b/g, "me");    // Convert "I" → "me" for Auslan grammar
};

export default cleanInputText;
