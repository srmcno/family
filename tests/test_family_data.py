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
