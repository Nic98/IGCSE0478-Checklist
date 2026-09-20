export const localPreview = import.meta.env.DEV || process.env.LOCAL_PREVIEW === 'true';
export const sitePath = (path = '') => `${import.meta.env.BASE_URL.replace(/\/$/, '')}/${path.replace(/^\//, '')}`;

type BlockBase = { id: string; hint?: string; printPage?: number };
export type KnowledgeBlock = BlockBase & (
  | { type: 'definition'; term: string; text: string }
  | { type: 'bullets' | 'steps' | 'answer-points'; title: string; items: string[] }
  | { type: 'comparison'; title: string; columns: string[]; rows: string[][] }
  | { type: 'example'; title: string; problem: string; steps: string[]; result: string }
  | { type: 'equivalence'; title: string; values: { label: string; value: string }[] }
  | { type: 'callout'; title: string; text: string }
  | { type: 'division'; title: string; value: number; base: 2 | 16 }
  | { type: 'bit-grid'; title: string; width: 8 | 16; weights?: number[]; rows: { label: string; bits: string }[]; note?: string }
  | { type: 'binary-addition'; title: string; a: number; b: number; width: 8; explanation: string }
  | { type: 'logical-shift'; title: string; value: number; direction: 'left' | 'right'; places: number; width: 8; explanation: string }
  | { type: 'sampling-diagram'; title: string; duration: number; waveform: number[]; panels: { label: string; sampleRate: number; resolution: number }[] }
);

export interface Checklist {
  id: string;
  title: string;
  subtitle?: string;
  label: string;
  version: string;
  syllabus: string;
  sample?: boolean;
  pdfPageTitles?: string[];
  sections: {
    id: string;
    title: string;
    summary?: string;
    blocks: KnowledgeBlock[];
  }[];
  reviewTopics?: { id: string; label: string }[];
}
