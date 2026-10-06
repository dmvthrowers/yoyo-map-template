/**
 * Fills {{token}} placeholders in message text from the values in map.config.ts. Unknown tokens
 * are left as they are, so a typo shows up on the page instead of vanishing.
 */
export function fillTokens(text: string, tokens: Record<string, string>): string {
  return text.replace(/\{\{\s*([A-Za-z][A-Za-z0-9]*)\s*\}\}/g, (whole, name: string) =>
    Object.prototype.hasOwnProperty.call(tokens, name) ? tokens[name] : whole,
  );
}

/** Every string in a (nested) messages object, with its tokens filled. */
export function fillMessages<T>(messages: T, tokens: Record<string, string>): T {
  if (typeof messages === 'string') return fillTokens(messages, tokens) as unknown as T;
  if (Array.isArray(messages)) return messages.map((m) => fillMessages(m, tokens)) as unknown as T;
  if (messages && typeof messages === 'object') {
    return Object.fromEntries(
      Object.entries(messages as Record<string, unknown>).map(([k, v]) => [k, fillMessages(v, tokens)]),
    ) as T;
  }
  return messages;
}

/** The names of the {{tokens}} used anywhere in a messages object that have no value. */
export function unknownTokens(messages: unknown, tokens: Record<string, string>): string[] {
  const found = new Set<string>();
  const walk = (m: unknown) => {
    if (typeof m === 'string') {
      for (const hit of m.matchAll(/\{\{\s*([A-Za-z][A-Za-z0-9]*)\s*\}\}/g)) {
        if (!Object.prototype.hasOwnProperty.call(tokens, hit[1])) found.add(hit[1]);
      }
    } else if (Array.isArray(m)) m.forEach(walk);
    else if (m && typeof m === 'object') Object.values(m as Record<string, unknown>).forEach(walk);
  };
  walk(messages);
  return [...found].sort();
}
