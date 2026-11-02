"""Validate the archive data that drives both the story links and photo viewer."""
import json
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

    def test_photograph_editions_and_story_images_exist(self):
        for key, image in D['PH'].items():
            for edition in ('o', 'r', 'c'):
                if image.get(edition):
                    self.assertTrue((ROOT / image[edition]).is_file(), (key, edition, image[edition]))
        for story in ENTRIES:
            images = [image['s'] for image in story.get('imgs', [])]
            self.assertEqual(len(images), len(set(images)), story['id'])
            for image in images:
                self.assertTrue((ROOT / image).is_file(), (story['id'], image))


if __name__ == '__main__':
    unittest.main()
