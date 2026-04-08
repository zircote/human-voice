#!/usr/bin/env node

/**
 * resolve-profile.js
 * Resolves which voice profile applies to a given file or directory.
 *
 * Resolution order (highest priority first):
 *   1. Frontmatter label: `voice-profile: <name>` in the target file
 *   2. Path glob match: routing rules in .claude/human-voice.local.md
 *   3. Config default: `profiles.default` in .claude/human-voice.local.md
 *   4. Plugin default: profiles/default.md
 *
 * Usage:
 *   node resolve-profile.js <file-or-dir> [--config=path] [--plugin-root=path]
 *   node resolve-profile.js docs/api.md
 *   node resolve-profile.js _posts/my-post.md --plugin-root=/path/to/human-voice
 *   node resolve-profile.js docs/ --config=.claude/human-voice.local.md
 *
 * Output:
 *   JSON object with resolved profile settings to stdout
 *
 * Exit codes:
 *   0 - Profile resolved successfully
 *   1 - Error (invalid arguments, file not found)
 */

const fs = require("fs");
const path = require("path");

// --- YAML frontmatter parser (simple, no dependencies) ---

/**
 * Extract YAML frontmatter from markdown content.
 * Returns an object with parsed key-value pairs, or null if no frontmatter.
 */
function parseFrontmatter(content) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return null;

  const yaml = match[1];
  return parseYaml(yaml);
}

/**
 * Simple YAML parser supporting:
 * - Key-value pairs (string, number, boolean)
 * - Nested objects (indentation-based)
 * - Arrays (- item syntax)
 * - Inline arrays ([item1, item2])
 */
function parseYaml(text) {
  const lines = text.split("\n");
  return parseYamlLines(lines, 0).result;
}

function parseYamlLines(lines, baseIndent) {
  const result = {};
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Skip empty lines and comments
    if (line.trim() === "" || line.trim().startsWith("#")) {
      i++;
      continue;
    }

    const indent = line.search(/\S/);
    if (indent < baseIndent) break;
    if (indent > baseIndent) {
      i++;
      continue;
    }

    const keyMatch = line.match(/^(\s*)([\w-]+)\s*:\s*(.*)/);
    if (!keyMatch) {
      i++;
      continue;
    }

    const key = keyMatch[2];
    const valueStr = keyMatch[3].trim();

    if (valueStr === "") {
      // Check if next lines are array items or nested object
      const nextNonEmpty = findNextNonEmpty(lines, i + 1);
      if (nextNonEmpty !== -1) {
        const nextIndent = lines[nextNonEmpty].search(/\S/);
        if (nextIndent > indent && lines[nextNonEmpty].trim().startsWith("- ")) {
          // Array
          const arr = [];
          let j = i + 1;
          while (j < lines.length) {
            const arrLine = lines[j];
            if (arrLine.trim() === "" || arrLine.trim().startsWith("#")) {
              j++;
              continue;
            }
            const arrIndent = arrLine.search(/\S/);
            if (arrIndent <= indent) break;

            const arrMatch = arrLine.match(/^\s*-\s+(.+)/);
            if (arrMatch) {
              // Check if this is a map item (- key: value)
              const mapMatch = arrMatch[1].match(/^([\w-]+)\s*:\s*(.*)/);
              if (mapMatch) {
                // Array of objects: collect all key-value pairs at this level
                const obj = {};
                obj[mapMatch[1]] = parseValue(mapMatch[2].trim());
                // Look for continuation lines at deeper indent
                let k = j + 1;
                while (k < lines.length) {
                  const contLine = lines[k];
                  if (contLine.trim() === "" || contLine.trim().startsWith("#")) {
                    k++;
                    continue;
                  }
                  const contIndent = contLine.search(/\S/);
                  if (contIndent <= arrIndent) break;
                  const contMatch = contLine.match(/^\s*([\w-]+)\s*:\s*(.*)/);
                  if (contMatch) {
                    obj[contMatch[1]] = parseValue(contMatch[2].trim());
                  }
                  k++;
                }
                arr.push(obj);
                j = k;
              } else {
                arr.push(parseValue(arrMatch[1]));
                j++;
              }
            } else {
              j++;
            }
          }
          result[key] = arr;
          i = j;
          continue;
        } else if (nextIndent > indent) {
          // Nested object
          const nested = parseYamlLines(lines.slice(i + 1), nextIndent);
          result[key] = nested.result;
          i = i + 1 + nested.consumed;
          continue;
        }
      }
      result[key] = null;
      i++;
    } else {
      result[key] = parseValue(valueStr);
      i++;
    }
  }

  return { result, consumed: i };
}

function findNextNonEmpty(lines, start) {
  for (let i = start; i < lines.length; i++) {
    if (lines[i].trim() !== "" && !lines[i].trim().startsWith("#")) {
      return i;
    }
  }
  return -1;
}

function parseValue(str) {
  if (str === "true") return true;
  if (str === "false") return false;
  if (str === "null" || str === "~") return null;
  if (/^-?\d+$/.test(str)) return parseInt(str, 10);
  if (/^-?\d+\.\d+$/.test(str)) return parseFloat(str);

  // Inline array: [item1, item2]
  if (str.startsWith("[") && str.endsWith("]")) {
    const inner = str.slice(1, -1).trim();
    if (inner === "") return [];
    return inner.split(",").map((s) => parseValue(s.trim()));
  }

  // Remove surrounding quotes
  if (
    (str.startsWith('"') && str.endsWith('"')) ||
    (str.startsWith("'") && str.endsWith("'"))
  ) {
    return str.slice(1, -1);
  }

  return str;
}

// --- Glob matching (simple, no dependencies) ---

/**
 * Match a file path against a simple glob pattern.
 * Supports:
 *   dir/**     - matches anything under dir/
 *   *.md       - matches files ending in .md
 *   exact.md   - exact match
 *   dir/*.md   - matches .md files directly in dir/
 */
function globMatch(pattern, filePath) {
  // Normalize paths
  const normPath = filePath.replace(/\\/g, "/");
  const normPattern = pattern.replace(/\\/g, "/");

  // dir/** -> matches anything under dir/
  if (normPattern.endsWith("/**")) {
    const prefix = normPattern.slice(0, -3);
    return normPath.startsWith(prefix + "/") || normPath === prefix;
  }

  // Exact match
  if (!normPattern.includes("*")) {
    return normPath === normPattern || normPath.endsWith("/" + normPattern);
  }

  // Convert glob to regex for remaining patterns
  const regexStr = normPattern
    .replace(/\./g, "\\.")
    .replace(/\*\*/g, "<<GLOBSTAR>>")
    .replace(/\*/g, "[^/]*")
    .replace(/<<GLOBSTAR>>/g, ".*");

  const regex = new RegExp("^" + regexStr + "$");
  return regex.test(normPath);
}

// --- Profile loading ---

/**
 * Load a profile by name from plugin presets or user overrides.
 * Search order: .claude/profiles/<name>.md, then <plugin-root>/profiles/<name>.md
 */
function loadProfile(name, pluginRoot) {
  const candidates = [
    path.join(".claude", "profiles", name + ".md"),
    path.join(pluginRoot, "profiles", name + ".md"),
  ];

  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      const content = fs.readFileSync(candidate, "utf8");
      const frontmatter = parseFrontmatter(content);
      if (frontmatter) {
        return frontmatter;
      }
    }
  }

  return null;
}

/**
 * Load routing config from .claude/human-voice.local.md
 */
function loadRoutingConfig(configPath) {
  if (!fs.existsSync(configPath)) return null;

  const content = fs.readFileSync(configPath, "utf8");
  const frontmatter = parseFrontmatter(content);
  if (!frontmatter || !frontmatter.profiles) return null;

  return frontmatter.profiles;
}

/**
 * Extract voice-profile from a target file's frontmatter.
 */
function extractFileProfile(filePath) {
  if (!fs.existsSync(filePath)) return null;

  const stat = fs.statSync(filePath);
  if (stat.isDirectory()) return null;

  const ext = path.extname(filePath).toLowerCase();
  if (![".md", ".mdx", ".markdown", ".txt"].includes(ext)) return null;

  const content = fs.readFileSync(filePath, "utf8");
  const frontmatter = parseFrontmatter(content);
  if (!frontmatter) return null;

  return frontmatter["voice-profile"] || null;
}

// --- Main ---

function main() {
  const args = process.argv.slice(2);

  // Parse arguments
  let target = null;
  let configPath = path.join(".claude", "human-voice.local.md");
  let pluginRoot = path.resolve(path.join(__dirname, "..", "..", ".."));

  for (const arg of args) {
    if (arg.startsWith("--config=")) {
      configPath = arg.substring(9);
    } else if (arg.startsWith("--plugin-root=")) {
      pluginRoot = arg.substring(14);
    } else if (!arg.startsWith("--")) {
      target = arg;
    }
  }

  if (!target) {
    console.error(
      "Usage: node resolve-profile.js <file-or-dir> [--config=path] [--plugin-root=path]",
    );
    console.error("");
    console.error("Resolution order (highest priority first):");
    console.error(
      "  1. voice-profile frontmatter label in the target file",
    );
    console.error(
      "  2. Path glob match from routing rules in config",
    );
    console.error("  3. Default profile from config");
    console.error("  4. Plugin default profile");
    process.exit(1);
  }

  if (!fs.existsSync(target)) {
    console.error(`Error: Target not found: ${target}`);
    process.exit(1);
  }

  // Step 1: Check file frontmatter for voice-profile label
  let profileName = extractFileProfile(target);
  let source = "frontmatter";

  // Step 2: Check routing config for path glob match
  if (!profileName) {
    const routing = loadRoutingConfig(configPath);
    if (routing && routing.routes) {
      for (const route of routing.routes) {
        if (route.match && route.profile && globMatch(route.match, target)) {
          profileName = route.profile;
          source = "route:" + route.match;
          break;
        }
      }
    }

    // Step 3: Use config default
    if (!profileName && routing && routing.default) {
      profileName = routing.default;
      source = "config-default";
    }
  }

  // Step 4: Fall back to plugin default
  if (!profileName) {
    profileName = "default";
    source = "plugin-default";
  }

  // Load the resolved profile
  const profile = loadProfile(profileName, pluginRoot);
  if (!profile) {
    // Profile not found, output minimal default
    const fallback = {
      name: profileName,
      source: source,
      error: `Profile "${profileName}" not found`,
      detection: {
        character_patterns: { enabled: true, ignore: [] },
        language_patterns: { enabled: true },
        structural_patterns: { enabled: true },
        voice_patterns: { enabled: true },
      },
      strictness: "normal",
    };
    console.log(JSON.stringify(fallback, null, 2));
    process.exit(0);
  }

  // Output resolved profile as JSON
  const output = {
    name: profile.name || profileName,
    source: source,
    description: profile.description || "",
    detection: profile.detection || {
      character_patterns: { enabled: true, ignore: [] },
      language_patterns: { enabled: true },
      structural_patterns: { enabled: true },
      voice_patterns: { enabled: true },
    },
    strictness: profile.strictness || "normal",
  };

  console.log(JSON.stringify(output, null, 2));
  process.exit(0);
}

main();
