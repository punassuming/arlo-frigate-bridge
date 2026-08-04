# Contribution and publishing standards

## Commit messages

Use Conventional Commits for every commit that can reach `main`:

```text
type(optional-scope): imperative summary
```

Allowed types are `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `build`,
`ci`, and `chore`.

- Use `feat` for a user-visible capability; it produces a minor release.
- Use `fix` or `perf` for a user-visible correction; it produces a patch release.
- Add `!` after the type/scope or a `BREAKING CHANGE:` footer for breaking
  changes; it produces a major release.
- Keep the first line concise, imperative, and free of a trailing period.
- PR titles are validated in CI and must use the same format. Squash merge PRs
  so that title becomes the merge commit and release-note source of truth.

Examples:

```text
feat(deployment): generate a verified deployment manifest
fix(mqtt): wait for Frigate state confirmation
docs: explain private inventory generation
```

## Publishing workflow

1. Work on an `agent/<description>` branch.
2. Run the relevant local checks and inspect the staged diff before committing.
3. Commit only the scoped changes with a Conventional Commit message.
4. Push the branch and open a draft PR unless the requester explicitly asks for
   ready-for-review status.
5. Resolve required CI checks before requesting merge.
6. Do not manually edit `CHANGELOG.md`, create release tags, or bump
   `custom_components/arlo_cam_api/manifest.json` for ordinary releases.
   Release Please owns those files after a Conventional Commit reaches `main`.

## Deployment versions

Private deployment inventories and generated output must never be committed.
Pin deployment images to a tag or digest, never `latest`. For PR deployments,
use the version emitted by the **PR deployment version** workflow.
