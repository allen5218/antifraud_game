const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const [action, state, group] = process.argv.slice(2);
if (!['check', 'record'].includes(action) || !state) throw Error('Expected check|record and local state directory');
if (group && group !== 'tests') throw Error('Unknown build group');
const metadata = JSON.parse(fs.readFileSync(path.join(state, 'environment.json'), 'utf8'));
const filename = path.join(state, group === 'tests' ? 'test-build-state.json' : 'build-state.json');
function imageIds() {
  return (group === 'tests' ? ['frontend-tests', 'playwright'] : ['backend', 'frontend']).map(service => {
    const name = `${metadata.project}-${service}:gameplay-v1.1`;
    const id = cp.execFileSync('docker', ['image', 'inspect', name, '--format', '{{.Id}}'], {encoding:'utf8',stdio:['ignore','pipe','pipe']}).trim();
    return {name, id};
  });
}
try {
  const images = imageIds();
  if (action === 'record') {
    if (!metadata.sourceFingerprint) throw Error('Missing source fingerprint');
    fs.writeFileSync(filename, JSON.stringify({sourceFingerprint:metadata.sourceFingerprint, images, recordedAt:new Date().toISOString()}, null, 2));
    console.log('Local image IDs and source fingerprint recorded.');
  } else {
    const saved = JSON.parse(fs.readFileSync(filename, 'utf8'));
    if (!metadata.sourceFingerprint || saved.sourceFingerprint !== metadata.sourceFingerprint || JSON.stringify(saved.images) !== JSON.stringify(images)) process.exit(2);
    console.log('Local source and image IDs match; reuse the existing build.');
  }
} catch (error) {
  if (action === 'check') process.exit(2);
  throw error;
}
