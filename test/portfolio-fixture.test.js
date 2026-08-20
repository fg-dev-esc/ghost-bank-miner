const assert = require('node:assert/strict');
const { access, readFile } = require('node:fs/promises');
const path = require('node:path');
const test = require('node:test');

const root = path.join(__dirname, '..');

test('portfolio files and synthetic operation fixtures are valid', async () => {
  await access(path.join(root, 'ARCHITECTURE.md'));
  await access(path.join(root, 'legacy', 'README.md'));

  const fixture = JSON.parse(
    await readFile(path.join(__dirname, 'fixtures', 'synthetic', 'operation-cases.json'), 'utf8')
  );
  const patterns = [/op[\s.\-:]*(\d+)[\s.\-:]*ref/i, /Concepto[\s:]*.*?OP\s+(\d+)/i];

  assert.equal(fixture.synthetic, true);
  fixture.cases.forEach((item) => {
    const match = patterns.map((pattern) => item.text.match(pattern)).find(Boolean);
    assert.equal(match?.[1], item.operationId);
    assert.equal(item.outputName, `${item.operationId}.pdf`);
  });
});
