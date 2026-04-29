import { describe, it, expect } from 'vitest';
import es from '../../../frontend/src/locales/es.json';
import en from '../../../frontend/src/locales/en.json';

describe('Translations', () => {
  function getKeys(obj, prefix = '') {
    let keys = [];
    for (const key in obj) {
      const fullKey = prefix ? `${prefix}.${key}` : key;
      if (typeof obj[key] === 'object' && obj[key] !== null) {
        keys = keys.concat(getKeys(obj[key], fullKey));
      } else {
        keys.push(fullKey);
      }
    }
    return keys;
  }

  it('should have same keys in both language files', () => {
    const esKeys = new Set(getKeys(es));
    const enKeys = new Set(getKeys(en));

    const missingInEn = [...esKeys].filter(k => !enKeys.has(k));
    const missingInEs = [...enKeys].filter(k => !esKeys.has(k));

    expect(missingInEn).toHaveLength(0, `Keys in ES but not EN: ${missingInEn.join(', ')}`);
    expect(missingInEs).toHaveLength(0, `Keys in EN but not ES: ${missingInEs.join(', ')}`);
  });

  it('should not have empty translation values', () => {
    const esKeys = getKeys(es);
    const enKeys = getKeys(en);

    esKeys.forEach(key => {
      const value = key.split('.').reduce((obj, k) => obj[k], es);
      expect(value).toBeTruthy(`ES translation empty for key: ${key}`);
    });

    enKeys.forEach(key => {
      const value = key.split('.').reduce((obj, k) => obj[k], en);
      expect(value).toBeTruthy(`EN translation empty for key: ${key}`);
    });
  });
});
