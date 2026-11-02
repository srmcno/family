import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { adaptFamily } from '../adapter.js';
import { createRelationships } from '../relationships.js';

globalThis.window = { SITE: { rootName: 'Root' } };

test('merged stories preserve old references, both portraits, and photograph metadata', () => {
  const data = {
    P: [{ id: 'old', name: 'Person', title: 'Old story', branch: 'thompson', body: ['Old'] }],
    EXTRA: [{ id: 'new', name: 'Person', title: 'Combined', branch: 'thompson', body: ['Combined'],
      ph: 'first', photo_sets: ['second'], imgs: [
        { s: 'img/places/insurance.jpg', cap: 'Sanborn insurance map' },
        { s: 'img/p/school.jpg', cap: 'Person, school portrait' },
        { s: 'img/docs/letter.jpg', cap: 'Family letter', kind: 'record' }
      ] }],
    STORY_ALIASES: { old: 'new', missing: 'new', ghost: 'unknown' },
    ORDER: ['old'], PHOTO_ORDER: [], TIMELINE: [{ y: '1900', t: 'A date', p: 'old', b: 'thompson' }],
    PH: {
      first: { o: 'img/p/rebecca_graves_orig.jpg', c: 'img/p/enhanced.jpg', labels: { c: 'Enhanced' }, edit_note: 'A camera enhancement.', source: 'https://example.com/photo' },
      second: { o: 'img/p/second.jpg', c: 'img/p/second-color.jpg', cap: 'Second portrait' }
    }
  };
  const tree = { people: { person: { n: 'Person', x: 'F', a: 'old', f: null, m: null } }, roots: {} };
  const { T, C } = adaptFamily(data, tree);
  assert.deepEqual(C.storyAliases, { old: 'new' });
  assert.equal(C.stories.length, 1);
  assert.equal(C.stories[0].id, 'new');
  assert.deepEqual(C.stories[0].people, ['person']);
  assert.equal(C.stories[0].rank, 0);
  assert.deepEqual(C.stories[0].imgs.slice(0, 2).map(x => x.s), ['img/p/rebecca_graves_orig.jpg', 'img/p/second.jpg']);
  assert.equal(C.stories[0].imgs.at(-1).kind, 'record');
  assert.equal(C.timeline[0].story, 'new');
  assert.equal(C.restorations['img/p/rebecca_graves_orig.jpg'].labels.c, 'Enhanced');
  assert.equal(C.restorations['img/p/rebecca_graves_orig.jpg'].edit_note, 'A camera enhancement.');
  assert.equal(C.photoSources['img/p/rebecca_graves_orig.jpg'].url, 'https://example.com/photo');
  assert.equal(C.archivePhotos.length, 0, 'a school portrait and a map are not historic-place photos');
  assert.equal(T.people.person.n, 'Person');
  assert.equal(T.people.person.img, 'img/p/rebecca_graves_orig.jpg', 'the surname Graves is not a grave record');
});

test('Andrews family connection resolves through the recorded Stevenson parents', () => {
  const data = JSON.parse(readFileSync(new URL('../data.json', import.meta.url)));
  const tree = JSON.parse(readFileSync(new URL('../tree.json', import.meta.url)));
  const { T, C } = adaptFamily(data, tree);
  const relation = createRelationships(T.people, T.root).describe('A:frank-maxwell-andrews');
  assert.equal(relation.label, '3rd cousin, twice removed');
  assert.equal(relation.commonAncestor, 'I352820878523');
  const story = C.stories.find(s => s.id === 'frank-maxwell-andrews');
  assert.ok(story.people.includes('A:frank-maxwell-andrews'));
  assert.ok(story.imgs.some(img => img.s === 'img/p/frank_maxwell_andrews_orig.jpg'));
  assert.ok(C.restorations['img/p/frank_maxwell_andrews_orig.jpg'].colorized);
});
