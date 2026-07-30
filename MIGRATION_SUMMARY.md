# AppsFlyer-STG Content Migration — Summary

## Original goal

Set up a bi-directional sync between the ReadMe staging environment (`appsflyer-staging-group`) and a GitHub repo, then use that sync to copy `devhub`'s (the production dev hub source) content into the `AppsFlyer-STG` ReadMe project, so its structure matches the live production sidebar.

## What we set up

- Researched ReadMe's Bi-Directional Sync feature (Settings > Git Connection), which requires connecting to a completely empty GitHub repo and pushes an initial commit from the ReadMe side.
- Created the GitHub repo `staging-full-clone-STG` (owner: `dori-af`) and installed the ReadMe Sync GitHub App, scoped to that repo.
- Connected the `AppsFlyer-STG` ReadMe project to `staging-full-clone-STG` via Git Connection. The connected branch is `v1.0`.
- Confirmed the mechanics of the sync: it's genuinely two-way, edits in the ReadMe editor push to git automatically and vice versa, once the connection is live. New pages created directly in the ReadMe UI also sync out to git on save.
- Confirmed there's no per-page flag to exclude a page from syncing once a project is connected, sync is all-or-nothing per project/version.

## The actual copy job

Rather than a live merge, the goal became: fully replace `AppsFlyer-STG`'s content with content sourced from `devhub` (the repo backing the real production dev hub), matching production's current sidebar hierarchy exactly.

Key discovery: `devhub` uses ReadMe's **old** classic frontmatter schema (`title`, `slug`, `category.uri`, `parent.uri`, `content.excerpt`, `privacy.view`, `position`, `hidden`, `metadata`), while `AppsFlyer-STG`'s Bi-Directional Sync repo uses the **new** ReadMe Refactored schema (`title`, `excerpt`, `hidden`, `metadata`, category expressed as folder location, order expressed via `_order.yaml`). A straight file copy would not have worked.

### The hierarchy source

Parsed the actual production sidebar HTML (11 top-level categories, deeply nested subpages) to build the authoritative target structure, rather than trusting devhub's own folder layout or frontmatter alone. Excluded 3 sidebar entries with no real backing content (two external GitHub links, one duplicate cross-link to an already-covered category).

### `transform.py`

Wrote a Python script (now living in this repo) that:

- Indexes every markdown file in `devhub/docs/guides` and `devhub/docs/apis` by slug, skipping OpenAPI YAML/JSON specs and stray HTML files (flagged separately, 49 files, not handled by this script).
- Walks the production-sidebar-derived tree and, for each page: pulls content from the matching devhub file if one exists, or falls back to a live call against ReadMe's v2 API (`GET https://api.readme.com/v2/branches/stable/guides/{slug}`, Bearer auth) if devhub has no match, or writes a placeholder if neither source has it.
- Determines `hidden` by combining three signals: the sidebar's own hidden/visible state, devhub's own `hidden` field, and `privacy.view: anyone_with_link` (treated as hidden rather than silently made public).
- Carries over `metadata` (SEO fields) when present.
- Copies only real image assets from same-named sibling folders in devhub (not markdown, after finding and fixing a bug where non-image sibling content was being copied wholesale).
- Builds `_order.yaml` at every folder level to match the production page order, and `index.md` for any page that has its own subpages.
- Writes a `transform_report.txt` after each run summarizing what happened.

### Bugs found and fixed along the way

1. **Wrong API version/auth**: initial version used the deprecated v1 API with Basic auth; the project actually uses v2 with Bearer auth (`api.readme.com/v2/branches/{branch}/guides/{slug}`).
2. **Cloudflare block**: the API host was rejecting Python's default User-Agent; fixed by sending a normal browser-style User-Agent header.
3. **Asset-copy bug**: some devhub files have a same-named sibling folder that isn't an image folder but actual old-format subpages; the script was blindly copying that raw, polluting the new structure with old-format content under a stray `index/` folder. Fixed to only copy actual image files.
4. **API content collision**: 3 slugs (`temp-1`, `temp-2`, `deep-linking`) got back a different, unrelated page's full content (including its own frontmatter) from the live API, likely a slug-collision/cache quirk. Added a safety check that discards any API response whose body itself contains an embedded frontmatter block, falling back to a placeholder instead.

### Final verified state (before push)

- 137 real files sourced from devhub, 68 pages filled in via the live API, 11 pages correctly marked hidden due to `anyone_with_link`, only 3 genuine placeholders remaining (`temp-1`, `temp-2`, `deep-linking`, all originally obscure/legacy stub pages), 49 files (OpenAPI specs + 2 stray HTML pages) explicitly flagged as out of scope for this script.
- Verified no old-format frontmatter leaking anywhere, no duplicate content across any of the 199 pages, no corrupted files remaining.
- Noted (not fixed, flagged for later): 61 files still contain ReadMe's old `[block:...]` legacy JSON block syntax rather than plain Markdown, pre-existing in devhub, not introduced by this process.

## Where things stand now

- Committed and pushed to `staging-full-clone-STG` on branch `v1.0` (commit `3f6853c`).
- Still to confirm: that the push actually synced correctly into the live `AppsFlyer-STG` ReadMe project (pending visual check in the ReadMe dashboard).

## Known follow-ups

- Fill in real content for `temp-1`, `temp-2`, and `deep-linking` (currently placeholders), either manually in the ReadMe editor or once the API collision issue is understood.
- Decide what to do with the 49 flagged OpenAPI specs and 2 HTML files, these need a different ingestion path (ReadMe's OpenAPI upload, not markdown sync).
- Consider cleaning up the 61 files with legacy `[block:...]` syntax so they render properly under the new system.
- A backup branch (`backup-before-devhub-replace`) was pushed earlier and still exists if a rollback is ever needed.
