export const levels = ['not-yet', 'developing', 'confident'];
export const storageKey = (id) => `igcse0478-checklist:v1:${id}`;

export function readProgress(storage, id, itemIds) {
  const raw = JSON.parse(storage.getItem(storageKey(id)) || '{}');
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return {};
  return Object.fromEntries(itemIds.filter((itemId) => levels.includes(raw[itemId])).map((itemId) => [itemId, raw[itemId]]));
}

export function saveProgress(storage, id, state) {
  storage.setItem(storageKey(id), JSON.stringify(state));
}
