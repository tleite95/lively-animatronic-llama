import { define } from "@opencode-ai/plugin/v2/promise"
import type { AgentV2Info, SkillV2Source } from "@opencode-ai/sdk/v2/types"
import { isAbsolute, relative, resolve } from "node:path"
import { fileURLToPath, pathToFileURL } from "node:url"
import { z } from "zod"

type ContentKind = "skill" | "agent"

/**
 * Shape of input to a transformer function
 * absolutePath: item's backing file when one exists (always present in the API return for skills, never for agents)
 *   Transforms that need a file for agents must find it themselves (maybe move this up the stack to this plugin?)
 */
type ContentTransformInput = {
    content: string
    absolutePath: string | undefined
    name: string
    config: Record<string, unknown> | undefined
}

type ContentTransform = (input: ContentTransformInput) => string | Promise<string>

const TransformRuleSchema = z
    .object({
        transformModule: z.string().min(1),
        exportName: z.string().min(1).default("default"),
        skills: z.array(z.string().min(1)).default([]),
        agents: z.array(z.string().min(1)).default([]),
        config: z.record(z.string(), z.unknown()).optional(),
    })
    .refine((rule) => rule.skills.length > 0 || rule.agents.length > 0, {
        message: 'targets nothing; set "skills", "agents", or ["*"]',
    })

const OptionsSchema = z.object({
    transformsDir: z.string().min(1).default(".opencode/plugins/scripts"),
    transforms: z.array(TransformRuleSchema).min(1),
})

type TransformRule = z.infer<typeof TransformRuleSchema>
type Options = z.infer<typeof OptionsSchema>
type RuntimeRule = TransformRule & { transformContent: ContentTransform }

function parseOptions(raw: unknown): Options {
    const result = OptionsSchema.safeParse(raw)
    if (!result.success) {
        throw new Error(`content-transform: invalid options - ${result.error.message}`)
    }
    return result.data
}

// Some defense against code injection
function assertWithinAllowedDir(absolutePath: string, allowedDir: string): void {
    const rel = relative(allowedDir, absolutePath)
    if (rel.startsWith("..") || isAbsolute(rel)) {
        throw new Error(
            `content-transform: transformModule must resolve inside ${allowedDir} (got ${absolutePath})`,
        )
    }
}

function toModuleUrl(specifier: string, allowedDir: string): string {
    const absolutePath = specifier.startsWith("file://")
        ? fileURLToPath(specifier)
        : isAbsolute(specifier)
            ? specifier
            : resolve(allowedDir, specifier)

    assertWithinAllowedDir(absolutePath, allowedDir)
    return pathToFileURL(absolutePath).href
}

async function loadTransform(rule: TransformRule, allowedDir: string): Promise<ContentTransform> {
    const mod = (await import(toModuleUrl(rule.transformModule, allowedDir))) as Record<string, unknown>
    const fn = mod[rule.exportName]

    if (typeof fn !== "function") {
        throw new Error(
            `content-transform: ${rule.transformModule} does not export a function named "${rule.exportName}"`,
        )
    }

    return async (input) => {
        const result = await fn(input)
        if (typeof result !== "string") {
            throw new Error(
                `content-transform: ${rule.transformModule}#${rule.exportName} must return a string (or Promise<string>)`,
            )
        }
        return result
    }
}

const loadRules = (rules: TransformRule[], allowedDir: string): Promise<RuntimeRule[]> =>
    Promise.all(rules.map(async (rule) => ({ ...rule, transformContent: await loadTransform(rule, allowedDir) })))

async function invokeTransform(rule: RuntimeRule, input: ContentTransformInput): Promise<string> {
    try {
        return await rule.transformContent(input)
    } catch (error) {
        console.warn(`content-transform: transform "${rule.transformModule}#${rule.exportName}" failed`, error)
        throw error
    }
}

function globToRegExp(pattern: string): RegExp {
    const escaped = pattern
        .replace(/[.+^${}()|[\]\\]/g, "\\$&")
        .replace(/\*/g, ".*")
        .replace(/\?/g, ".")
    return new RegExp(`^${escaped}$`)
}

const matchesName = (name: string, patterns: string[]): boolean =>
    patterns.some((pattern) => globToRegExp(pattern).test(name))

function matchingRule(name: string, kind: ContentKind, rules: RuntimeRule[]): RuntimeRule | undefined {
    const matched = rules.filter((rule) => matchesName(name, kind === "skill" ? rule.skills : rule.agents))

    if (matched.length > 1) {
        throw new Error(
            `content-transform: multiple rules target ${kind} "${name}" (${matched
                .map((rule) => rule.transformModule)
                .join(", ")}); narrow the "skills"/"agents" patterns so only one rule matches`,
        )
    }

    return matched[0]
}

const resolveSkillPath = (location: string, worktree: string): string =>
    isAbsolute(location) ? location : resolve(worktree, location)

export default define({
    id: "lal.content-transform",
    setup: async (ctx: any) => {
        const projectRoot = process.cwd()
        const options = parseOptions(ctx.options)
        const allowedDir = resolve(projectRoot, options.transformsDir)
        const rules = await loadRules(options.transforms, allowedDir)

        console.log(`content-transform: setting up with ROOT=${projectRoot}`)

        await ctx.skill.transform(async (draft: any) => {
            for (const source of draft.list()) {
                if (source.type !== "embedded") {
                    console.warn(
                        `content-transform: skipping "${source.type}" skill source; only "embedded" sources expose inline content to transform`,
                    )
                    continue
                }

                const rule = matchingRule(source.skill.name, "skill", rules)
                if (!rule) continue

                const absolutePath = resolveSkillPath(source.skill.location, projectRoot)
                const content = await invokeTransform(rule, {
                    content: source.skill.content,
                    absolutePath,
                    name: source.skill.name,
                    config: rule.config,
                })
                const updated: SkillV2Source = { ...source, skill: { ...source.skill, content } }
                draft.source(updated)
            }
        })

        await ctx.agent.transform(async (draft: any) => {
            for (const info of draft.list()) {
                const rule = matchingRule(info.id, "agent", rules)
                if (!rule) continue

                const content = await invokeTransform(rule, {
                    content: info.system ?? "",
                    absolutePath: undefined,
                    name: info.id,
                    config: rule.config,
                })
                draft.update(info.id, (agent: AgentV2Info) => {
                    agent.system = content
                })
            }
        })
    },
})
