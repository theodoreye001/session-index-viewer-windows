# Release process

Current release candidate: **v0.1.0**.

See `docs/release-checklist.md` for the release gate and `docs/release-v0.1.0.md` for the prepared notes.

The supported release flow is:

1. Finish changes on a release branch.
2. Require the full GitHub Actions matrix to pass.
3. Merge the release PR into `master`.
4. Create tag `v0.1.0` on the merge commit.
5. Publish the GitHub release using the prepared release notes.

Do not tag the migration branch directly. The tag should identify the exact commit shipped from `master`.
