"""Validate the archive data that drives both the story links and photo viewer."""
import json
import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
D = json.loads((ROOT / 'data.json').read_text())
TREE = json.loads((ROOT / 'tree.json').read_text())
ENTRIES = D['P'] + D['EXTRA']
BY_ID = {entry['id']: entry for entry in ENTRIES}
ALIASES = D.get('STORY_ALIASES', {})


class ArchiveDataTests(unittest.TestCase):
    def test_tree_parent_links_resolve_without_ancestry_cycles(self):
        people = TREE['people']
        for root in TREE['roots'].values():
            self.assertIn(root, people)
        for person_id, person in people.items():
            for parent in (person.get('f'), person.get('m')):
                if parent:
                    self.assertIn(parent, people, person_id)
                    self.assertNotEqual(parent, person_id)

        complete = set()

        def visit(person_id, ancestors):
            self.assertNotIn(person_id, ancestors, f'ancestry cycle at {person_id}')
            if person_id in complete:
                return
            person = people[person_id]
            for parent in (person.get('f'), person.get('m')):
                if parent:
                    visit(parent, ancestors | {person_id})
            complete.add(person_id)

        for person_id in people:
            visit(person_id, set())

    def test_provisional_hulsey_household_does_not_invent_maternal_links(self):
        people = TREE['people']
        father = 'A:benjamin-hulsey:father'
        for person_id in ('A:margaret-m-hulsey:1880', 'A:charles-f-hulsey:1880'):
            self.assertEqual(people[person_id]['f'], father)
            self.assertIsNone(people[person_id]['m'])
            self.assertEqual(people[person_id]['ev'], 'probable')
            self.assertTrue(people[person_id]['source_urls'])
        # The separately researched Benjamin biography must not silently become this father.
        self.assertEqual(people[father]['a'], 'bf-hulsey-1880')

    def test_hulsey_1850_original_corrects_ages_without_merging_candidates(self):
        household = BY_ID['m3-salathiel-1850']
        self.assertIn('Benjamin, 3', household['body'][0])
        self.assertIn('Lillean, 6', household['body'][0])
        self.assertIn('no relationship column', household['body'][1])
        self.assertIn('4191561_00433', household['src'])
        self.assertIn('img/rec/hulsey-1850-union-household-original.jpg',
                      [image['s'] for image in household['imgs']])
        self.assertEqual(BY_ID['benjaminh']['ev'], 'lead')
        self.assertNotEqual(TREE['people']['A:benjamin-hulsey:father']['a'], 'benjaminh')

    def test_arkansas_robert_remains_a_candidate_after_original_review(self):
        candidate = BY_ID['robertrhulsey']
        self.assertEqual(candidate['ev'], 'lead')
        self.assertNotIn('Robert R.', candidate['name'])
        self.assertIn('4211301_00318', candidate['src'])
        self.assertIn('Selatha G.', candidate['body'][1])
        self.assertIn('handwritten spelling is uncertain', candidate['body'][1])
        self.assertIn('Benjamin is not listed in this household', candidate['body'][1])

    def test_story_aliases_preserve_usable_canonical_stories(self):
        self.assertEqual(len(BY_ID), len(ENTRIES), 'story IDs must be unique')
        for old, canonical in ALIASES.items():
            self.assertIn(old, BY_ID)
            self.assertIn(canonical, BY_ID)
            self.assertNotEqual(old, canonical)
            self.assertNotIn(canonical, ALIASES, 'aliases must resolve in one step')
            self.assertTrue(BY_ID[canonical].get('title'))
            self.assertTrue(BY_ID[canonical].get('body'))
            self.assertTrue(BY_ID[canonical].get('src'))
        for event in D['TIMELINE']:
            if event.get('p'):
                self.assertIn(event['p'], BY_ID)
        for person in TREE['people'].values():
            if person.get('a'):
                self.assertIn(person['a'], BY_ID)

    def test_melvina_conflicting_originals_do_not_invent_a_resolved_mother(self):
        story = BY_ID['melvina']
        text = ' '.join(story['body'])
        self.assertIn('78 years, 2 months, 6 days', text)
        self.assertIn('10 November 1851', text)
        self.assertIn('indexed as Vina', text)
        self.assertIn('identification of Vina with Melvina remains open', text)
        self.assertIn('KYVR_7017537-2275', story['src'])
        mother = TREE['people']['I352820878334']
        self.assertEqual(mother['ev'], 'probable')
        self.assertIn('have not been reconciled', mother['note'])
        self.assertNotIn('Elms', mother['n'])
        # A combined name incorrectly turns two unresolved surnames into one person.
        for entry in ENTRIES:
            self.assertNotIn('Mary Dunn "Polly" Elms', str(entry))
            self.assertNotIn('Mary Dunn "Polly" (Elms)', str(entry))

    def test_photograph_editions_and_story_images_exist(self):
        source_digests = {}
        for key, image in D['PH'].items():
            for edition in ('o', 'r', 'c'):
                if image.get(edition):
                    self.assertTrue((ROOT / image[edition]).is_file(), (key, edition, image[edition]))
            digest = hashlib.sha256((ROOT / image['o']).read_bytes()).hexdigest()
            self.assertNotIn(digest, source_digests, f"duplicate original photograph: {key} and {source_digests.get(digest)}")
            source_digests[digest] = key
        for story in ENTRIES:
            images = [image['s'] for image in story.get('imgs', [])]
            self.assertEqual(len(images), len(set(images)), story['id'])
            for image in images:
                self.assertTrue((ROOT / image).is_file(), (story['id'], image))


if __name__ == '__main__':
    unittest.main()
