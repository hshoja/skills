#!/usr/bin/env node
// Agent docs (AGENTS.md, CLAUDE.md, skills, subagents, rules) go stale on every refactor, and agents then follow dead paths.
// Fails when a doc names a file that is gone from the repo.
// With --changed <base-ref>, also warns when a PR edits a file a doc names but not the doc.
//
// Usage: node check-agent-docs.mjs [--changed <base-ref>]
// Ignore list: optional .agent-docs-ignore at the repo root, one path per line (# for comments).
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'

// Docs to check: AGENTS.md / CLAUDE.md anywhere, plus every .md / .mdc under these folders.
const DOC_DIRS = ['.claude', '.agents', '.cursor', '.github/instructions']
// A ref is a backticked relative path with at least one folder and one of these extensions.
const EXTENSIONS =
  'c|cc|cpp|cs|css|go|h|java|js|jsx|json|kt|md|mjs|cjs|php|py|rb|rs|scala|scss|sh|sql|swift|toml|ts|tsx|vue|ya?ml|conf'

const root = execFileSync('git', ['rev-parse', '--show-toplevel'], { encoding: 'utf8' }).trim()
const git = (...args) =>
  execFileSync('git', args, { cwd: root, encoding: 'utf8', maxBuffer: 1 << 28 })
    .split('\n')
    .filter(Boolean)

const ignoreFile = path.join(root, '.agent-docs-ignore')
const IGNORED = new Set(
  fs.existsSync(ignoreFile)
    ? fs
        .readFileSync(ignoreFile, 'utf8')
        .split('\n')
        .map(l => l.trim())
        .filter(l => l && !l.startsWith('#'))
    : [],
)

const PATH_REF = new RegExp(
  `\`((?:\\.{1,2}/)*[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+\\.(?:${EXTENSIONS}))\``,
  'g',
)

const escape = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
// Refs are often relative to a module, and `src/.../Foo.ts` skips any depth, so match a path suffix.
const pathMatcher = ref =>
  new RegExp(
    `(^|/)${ref
      .replace(/^(\.{1,2}\/)+/, '')
      .split('/...')
      .map(escape)
      .join('(?:/.+)?')}$`,
  )

const tracked = git('ls-files')
const dirRe = new RegExp(`^(${DOC_DIRS.map(escape).join('|')})/.*\\.mdc?$`)
// AGENTS.md is often a symlink to CLAUDE.md; use the real file so a PR that edits it counts as a doc update.
const docs = [
  ...new Set(
    tracked
      .filter(f => /(^|\/)(AGENTS|CLAUDE)\.md$/.test(f) || dirRe.test(f))
      .filter(f => fs.existsSync(path.join(root, f)))
      .map(f => path.relative(root, fs.realpathSync(path.join(root, f)))),
  ),
]

const refs = docs.map(doc => ({
  doc,
  paths: [...new Set([...fs.readFileSync(path.join(root, doc), 'utf8').matchAll(PATH_REF)].map(m => m[1]))].filter(
    p => !IGNORED.has(p),
  ),
}))

const trackedSet = new Set(tracked)
// A ref next to the doc (e.g. a skill's `references/x.md`) is that file; otherwise match by suffix.
const resolve = (doc, p) => {
  const local = path.join(path.dirname(doc), p)
  if (trackedSet.has(local)) return [local]
  const re = pathMatcher(p)
  return tracked.filter(f => re.test(f))
}
const resolved = new Map(refs.map(r => [r.doc, new Map(r.paths.map(p => [p, resolve(r.doc, p)]))]))

const changedIdx = process.argv.indexOf('--changed')
if (changedIdx !== -1) {
  const changed = new Set(git('diff', '--name-only', `${process.argv[changedIdx + 1]}...HEAD`))
  for (const { doc, paths } of refs) {
    if (changed.has(doc)) continue
    // A ref matching several files is a convention (e.g. `src/router.ts` in each service), not one file to watch.
    const owned = paths.map(p => resolved.get(doc).get(p)).filter(files => files.length === 1)
    const touched = new Set(owned.flat().filter(f => changed.has(f)))
    for (const f of touched)
      console.log(`::warning file=${doc}::${f} changed in this PR; check that ${doc} is still correct`)
  }
}

const dead = refs.flatMap(r =>
  r.paths.filter(p => resolved.get(r.doc).get(p).length === 0).map(p => `${r.doc}: \`${p}\``),
)
const total = refs.reduce((n, r) => n + r.paths.length, 0)
console.log(`check-agent-docs: ${docs.length} docs, ${total} file references, ${dead.length} dead`)
if (dead.length) {
  for (const d of dead) console.error(`  ${d}`)
  console.error(
    '\nThe file was moved or deleted. Point the doc at the new file, or update the text around it.' +
      '\nA path that exists only at run time (not in git) goes in .agent-docs-ignore.',
  )
  process.exit(1)
}
