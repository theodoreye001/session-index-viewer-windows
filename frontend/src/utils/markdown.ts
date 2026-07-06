import { marked } from "marked";

// Configure marked once. GFM + line breaks matches the original
// single-file viewer's behaviour.
marked.setOptions({ breaks: true, gfm: true });

export function renderMarkdown(text: string): string {
  const raw = text || " ";
  return marked.parse(raw, { async: false }) as string;
}
