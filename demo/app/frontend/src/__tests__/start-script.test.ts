import { describe, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import { resolve } from 'path';

describe('Root package.json', () => {
  const rootPkg = JSON.parse(
    readFileSync(resolve(import.meta.dirname, '../../../package.json'), 'utf-8'),
  );

  it('contains demo:start script', () => {
    expect(rootPkg.scripts).toHaveProperty('demo:start');
  });

  it('lists concurrently as devDependency', () => {
    expect(rootPkg.devDependencies).toHaveProperty('concurrently');
  });
});
