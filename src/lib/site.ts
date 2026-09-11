export const localPreview = import.meta.env.DEV || process.env.LOCAL_PREVIEW === 'true';
export const sitePath = (path = '') => `${import.meta.env.BASE_URL.replace(/\/$/, '')}/${path.replace(/^\//, '')}`;

type BlockBase = { id: string; hint?: string };
export type KnowledgeBlock = BlockBase & (
  | { type: 'definition'; term: string; text: string }
  | { type: 'bullets' | 'steps'; title: string; items: string[] }
  | { type: 'comparison'; title: string; columns: string[]; rows: string[][] }
  | { type: 'example'; title: string; problem: string; steps: string[]; result: string }
  | { type: 'equivalence'; title: string; values: { label: string; value: string }[] }
  | { type: 'callout'; title: string; text: string }
);

export interface Checklist {
  id: string;
  title: string;
  subtitle?: string;
  label: string;
  version: string;
  syllabus: string;
  sample?: boolean;
  sections: {
    id: string;
    title: string;
    summary?: string;
    blocks: KnowledgeBlock[];
  }[];
  reviewTopics?: { id: string; label: string }[];
}
