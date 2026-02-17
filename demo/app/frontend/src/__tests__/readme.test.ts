import { describe, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import { resolve } from 'path';

describe('Root README.md', () => {
  const readme = readFileSync(
    resolve(import.meta.dirname, '../../../../README.md'),
    'utf-8',
  );

  it('contains Prerequisites section', () => {
    expect(readme).toMatch(/#+\s*Prerequisites/i);
  });

  it('contains Setup section', () => {
    expect(readme).toMatch(/#+\s*Setup/i);
  });

  it('contains Environment Variables section', () => {
    expect(readme).toMatch(/#+\s*Environment\s*[Vv]ariables/i);
  });

  it('contains Architecture section', () => {
    expect(readme).toMatch(/#+\s*Architecture/i);
  });

  it('contains SDT Compression section', () => {
    expect(readme).toMatch(/#+\s*SDT\s*[Cc]ompression/i);
  });

  it('contains Troubleshooting section', () => {
    expect(readme).toMatch(/#+\s*Troubleshooting/i);
  });
});
