# Moffitt & Thompson Roots

A family-history site for the Moffitt, Thompson, Hulsey and Smith lines: stories, records, restored photographs and a timeline.
The site is static (`index.html` plus `data.json`) and is published with GitHub Pages. It asks search engines not to index it.

Serve the checkout with `python3 -m http.server 8767`. Run the data checks with
`python3 -m unittest discover -s tests -v` and the adapter checks with
`node --test tests/test_family_adapter.mjs`. Merged stories keep their former
URLs through `STORY_ALIASES` in `data.json`.
