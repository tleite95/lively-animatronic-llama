import * as fs from "fs"
import * as path from "path"

const REF_PATHS: Record<string, string> = {
    REF: "reference-md/",
    DAT: "data/",
    CFG: "config/",
    OUT: "artifacts/",
    ROOT: "",
}

const _REF_RE =
    /(?<![\w/])@(?:\{(?<key>[A-Za-z0-9_-]+)\}:(?<keyed>[^\s\]\)\}\>,;]+)|(?<plain>[^\s\]\)\}\>,;]+))/g

type _RefGroups = { key?: string; keyed?: string; plain?: string }

export type RefTransformInput = {
    content: string
    absolutePath: string | undefined
    name: string
    config: Record<string, unknown> | undefined
}

function _rawRef(groups: _RefGroups): string {
    return groups.keyed || groups.plain || ""
}

function _relativeRef(filename: string): string {
    return filename.replace(/^[/\\]+/, "")
}

function _splitSection(raw: string): { filename: string; section?: string } {
    const hashIndex = raw.indexOf("#")
    if (hashIndex === -1) return { filename: raw }
    return { filename: raw.slice(0, hashIndex), section: raw.slice(hashIndex + 1) }
}

function _isFile(p: string): boolean {
    try {
        return fs.statSync(p).isFile()
    } catch {
        return false
    }
}

function _walkDirs(dir: string): string[] {
    const dirs = [dir]
    let entries: fs.Dirent[]
    try {
        entries = fs.readdirSync(dir, { withFileTypes: true })
    } catch {
        return dirs
    }
    for (const entry of entries) {
        if (entry.isDirectory()) {
            dirs.push(..._walkDirs(path.join(dir, entry.name)))
        }
    }
    return dirs
}

function _findFile(baseDir: string, filename: string): string | null {
    baseDir = path.resolve(baseDir)
    filename = _relativeRef(filename)

    const direct = path.resolve(path.join(baseDir, filename))
    if (_isFile(direct)) {
        return direct
    }

    const matches = _walkDirs(baseDir)
        .map((dir) => path.resolve(path.join(dir, filename)))
        .filter((p) => _isFile(p))
        .sort()
    return matches.length > 0 ? matches[0] : null
}

function _resolveRef(filename: string, key: string | undefined, currentFile: string, root: string): string | null {
    if (key) {
        const refPath = REF_PATHS[key]
        if (refPath === undefined) return null
        return _findFile(path.join(root, refPath), filename)
    }

    return _findFile(path.dirname(currentFile), filename) ?? _findFile(root, filename)
}

function _requireRoot(config: unknown): string {
    const root = (config as Record<string, unknown> | undefined)?.root
    if (typeof root !== "string" || root.length === 0) {
        throw new Error(
            'ref-transform: rule "config.root" is required, e.g. { "config": { "root": "RAG" } } in opencode.json',
        )
    }
    return path.isAbsolute(root) ? root : path.resolve(process.cwd(), root)
}

const _AGENT_DIR_CANDIDATES = ["agents", "agent"] as const

function _findAgentFile(root: string, name: string): string | null {
    for (const dir of _AGENT_DIR_CANDIDATES) {
        const candidate = path.join(root, ".opencode", dir, `${name}.md`)
        if (_isFile(candidate)) return candidate
    }
    return null
}

function _resolveCurrentFile(input: RefTransformInput): { currentFile: string; root: string } | null {
    const root = _requireRoot(input.config)

    if (input.absolutePath) {
        return { currentFile: path.resolve(input.absolutePath), root }
    }

    const found = _findAgentFile(root, input.name)
    return found ? { currentFile: found, root } : null
}

function _dedent(text: string): string {
    const lines = text.split("\n")
    let minIndent = Infinity
    for (const line of lines) {
        if (line.trim().length === 0) continue
        const indent = line.match(/^[ \t]*/)?.[0].length ?? 0
        minIndent = Math.min(minIndent, indent)
    }
    if (!isFinite(minIndent) || minIndent === 0) return text
    return lines.map((line) => line.slice(Math.min(minIndent, line.length))).join("\n")
}

function _sliceAndDedent(text: string, start: number, end: number): string {
    const lineStart = text.lastIndexOf("\n", start - 1) + 1
    const prefix = text.slice(lineStart, start)
    if (prefix.trim().length === 0) {
        return _dedent(prefix + text.slice(start, end))
    }
    return _dedent(text.slice(start, end))
}

const _ATX_HEADING_RE = /^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$/gm

function _slugify(heading: string): string {
    return heading
        .trim()
        .toLowerCase()
        .replace(/[^\w\s-]/g, "")
        .replace(/\s+/g, "-")
        .replace(/-+/g, "-")
        .replace(/^-|-$/g, "")
}

function _extractMarkdownSection(text: string, sectionId: string): string | null {
    const headings = [...text.matchAll(_ATX_HEADING_RE)].map((match) => ({
        level: match[1].length,
        start: match.index ?? 0,
        slug: _slugify(match[2]),
    }))

    const targetIndex = headings.findIndex((h) => h.slug === sectionId)
    if (targetIndex === -1) return null
    const target = headings[targetIndex]

    const nextSibling = headings.slice(targetIndex + 1).find((h) => h.level <= target.level)
    const end = nextSibling ? nextSibling.start : text.length

    return _sliceAndDedent(text, target.start, end)
}

type _MarkupToken = { kind: "open" | "close" | "selfclose"; name: string; attrs: string; start: number }

const _TAG_RE = /<!--[\s\S]*?-->|<([a-zA-Z][\w:-]*)((?:"[^"]*"|'[^']*'|[^>])*?)(\/?)>|<\/([a-zA-Z][\w:-]*)\s*>/g

const _VOID_HTML_TAGS = new Set([
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
])

function _tokenizeMarkup(text: string): _MarkupToken[] {
    const tokens: _MarkupToken[] = []
    for (const match of text.matchAll(_TAG_RE)) {
        const [full, openName, attrs, selfSlash, closeName] = match
        if (full.startsWith("<!--")) continue
        const start = match.index ?? 0

        if (closeName) {
            tokens.push({ kind: "close", name: closeName, attrs: "", start })
        } else if (openName) {
            const isSelfClose = selfSlash === "/" || _VOID_HTML_TAGS.has(openName.toLowerCase())
            tokens.push({ kind: isSelfClose ? "selfclose" : "open", name: openName, attrs: attrs ?? "", start })
        }
    }
    return tokens
}

function _idAttr(attrs: string): string | null {
    const match = attrs.match(/\bid\s*=\s*(?:"([^"]*)"|'([^']*)')/)
    return match ? (match[1] ?? match[2] ?? null) : null
}

function _extractMarkupSection(text: string, sectionId: string): string | null {
    const tokens = _tokenizeMarkup(text)

    let depth = 0
    let targetIndex = -1
    let targetDepth = -1
    for (let i = 0; i < tokens.length; i++) {
        const token = tokens[i]
        if ((token.kind === "open" || token.kind === "selfclose") && _idAttr(token.attrs) === sectionId) {
            targetIndex = i
            targetDepth = depth
            break
        }
        if (token.kind === "open") depth++
        else if (token.kind === "close") depth = Math.max(0, depth - 1)
    }
    if (targetIndex === -1) return null
    const target = tokens[targetIndex]

    let cursor = targetIndex + 1
    let subtreeDepth = targetDepth
    if (target.kind === "open") {
        subtreeDepth++
        while (cursor < tokens.length && subtreeDepth > targetDepth) {
            if (tokens[cursor].kind === "open") subtreeDepth++
            else if (tokens[cursor].kind === "close") subtreeDepth--
            cursor++
        }
    }

    const boundary = cursor < tokens.length ? tokens[cursor].start : text.length
    return _sliceAndDedent(text, target.start, boundary)
}

function _extractSection(fileContent: string, filePath: string, sectionId: string): string {
    try {
        switch (path.extname(filePath).toLowerCase()) {
            case ".md":
                return _extractMarkdownSection(fileContent, sectionId) ?? fileContent
            case ".html":
            case ".htm":
            case ".xml":
                return _extractMarkupSection(fileContent, sectionId) ?? fileContent
            default:
                return fileContent
        }
    } catch {
        return fileContent
    }
}

/**
 * Replaces each "@{KEY}:filename" and "@filename" directive with the absolute path of the referenced file
 * Leavesthe raw directive text in place wherever a reference can't be resolved
 * If no source file can be resolved for "input" at all, returns `input.content` unchanged (no error thrown)
 */
export function hydrateRefs(input: RefTransformInput): string {
    const resolved = _resolveCurrentFile(input)
    if (!resolved) {
        _warnNoSourceFile("hydrateRefs", input.name)
        return input.content
    }
    const { currentFile, root } = resolved

    return input.content.replace(_REF_RE, (_match: string, ...args: unknown[]) => {
        const groups = args[args.length - 1] as _RefGroups
        const raw = _relativeRef(_rawRef(groups))
        const { filename, section } = _splitSection(raw)

        const target = _resolveRef(filename, groups.key, currentFile, root)
        if (target === null) {
            console.log("Could not resolve file reference; leaving raw filename.")
            return raw
        }
        return section ? `@${target}#${section}` : `@${target}`
    })
}

/**
 * Replaces each "@{KEY}:filename" / "@filename" directive with the contents of the referenced file
 *   Recursively expands directives found inside it
 * A `#section` fragment restricts the expansion to just that section for markdown files
 * Any other extension (or a failed section search) falls back to the whole file
 * Same no-source-file fallback as hydrateRefs()
 */
export function expandRefs(input: RefTransformInput): string {
    const resolved = _resolveCurrentFile(input)
    if (!resolved) {
        _warnNoSourceFile("expandRefs", input.name)
        return input.content
    }
    const { currentFile, root } = resolved
    return _expandRefs(input.content, currentFile, root, new Set())
}

function _warnNoSourceFile(fnName: string, name: string): void {
    const checked = _AGENT_DIR_CANDIDATES.map((dir) => `.opencode/${dir}/${name}.md`).join(", ")
    console.warn(
        `ref-transform: ${fnName} found no source file for "${name}" (checked ${checked}); leaving content unchanged`,
    )
}

function _expandRefs(text: string, currentFile: string, root: string, seen: Set<string>): string {
    currentFile = path.resolve(currentFile)

    return text.replace(_REF_RE, (_match: string, ...args: unknown[]) => {
        const groups = args[args.length - 1] as _RefGroups
        const raw = _relativeRef(_rawRef(groups))
        const { filename, section } = _splitSection(raw)

        try {
            const target = _resolveRef(filename, groups.key, currentFile, root)
            if (target === null || seen.has(target)) {
                throw new Error()
            }

            const included = fs.readFileSync(target, "utf-8")
            const scoped = section ? _extractSection(included, target, section) : included
            return _expandRefs(scoped, target, root, new Set([...seen, currentFile, target]))
        } catch {
            console.log("Could not expand file reference; leaving raw filename.")
            return raw
        }
    })
}