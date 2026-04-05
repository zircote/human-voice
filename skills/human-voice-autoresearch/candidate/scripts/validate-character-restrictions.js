#!/usr/bin/env node

/**
 * validate-character-restrictions.js
 * Detects AI-telltale characters in content files
 *
 * Usage:
 *   node validate-character-restrictions.js [--ignore=categories] <directory> [directory...]
 *   node validate-character-restrictions.js _posts content _docs
 *   node validate-character-restrictions.js --ignore=emojis,em-dash _posts
 *
 * Options:
 *   --ignore=categories  Comma-separated list of categories to ignore:
 *                        emojis, em-dash, en-dash, smart-quotes, ellipsis, bullet, arrow
 *
 * Exit codes:
 *   0 - No violations found
 *   1 - Violations found
 *   2 - Error (invalid arguments, directory not found)
 */

const fs = require("fs");
const path = require("path");

// Character restrictions with metadata
const RESTRICTIONS = [
  {
    name: "Em Dash",
    pattern: /\u2014/g,
    unicode: "U+2014",
    replacement: "colon (:), comma (,), semicolon (;), or period (.)",
    severity: "error",
  },
  {
    name: "En Dash",
    pattern: /\u2013/g,
    unicode: "U+2013",
    replacement: "hyphen (-)",
    severity: "error",
  },
  {
    name: "Left Double Quote",
    pattern: /\u201C/g,
    unicode: "U+201C",
    replacement: 'straight quote (")',
    severity: "error",
  },
  {
    name: "Right Double Quote",
    pattern: /\u201D/g,
    unicode: "U+201D",
    replacement: 'straight quote (")',
    severity: "error",
  },
  {
    name: "Left Single Quote",
    pattern: /\u2018/g,
    unicode: "U+2018",
    replacement: "straight apostrophe (')",
    severity: "error",
  },
  {
    name: "Right Single Quote",
    pattern: /\u2019/g,
    unicode: "U+2019",
    replacement: "straight apostrophe (')",
    severity: "error",
  },
  {
    name: "Horizontal Ellipsis",
    pattern: /\u2026/g,
    unicode: "U+2026",
    replacement: "three periods (...)",
    severity: "error",
  },
  {
    name: "Bullet Character",
    pattern: /\u2022/g,
    unicode: "U+2022",
    replacement: "markdown list (-)",
    severity: "error",
  },
  {
    name: "Emoji",
    pattern:
      /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu,
    unicode: "Various",
    replacement: "remove entirely",
    severity: "error",
  },
  {
    name: "Arrow Character",
    pattern: /[\u2190-\u21FF]/g,
    unicode: "U+2190-21FF",
    replacement: "ASCII arrow (->)",
    severity: "warning",
  },
];

// File extensions to check
const EXTENSIONS = [".md", ".mdx", ".markdown", ".txt"];

// Category name mapping for --ignore flag
// Maps user-facing category names to internal restriction names
const CATEGORY_MAP = {
  emojis: ["Emoji"],
  "em-dash": ["Em Dash"],
  "en-dash": ["En Dash"],
  "smart-quotes": [
    "Left Double Quote",
    "Right Double Quote",
    "Left Single Quote",
    "Right Single Quote",
  ],
  ellipsis: ["Horizontal Ellipsis"],
  bullet: ["Bullet Character"],
  arrow: ["Arrow Character"],
};

// Valid category names for help text
const VALID_CATEGORIES = Object.keys(CATEGORY_MAP).join(", ");

// Parse --ignore flag and return set of restriction names to skip
function parseIgnoreCategories(args) {
  const ignoreArg = args.find((arg) => arg.startsWith("--ignore="));
  if (!ignoreArg) return new Set();

  const categories = ignoreArg
    .substring(9)
    .split(",")
    .map((c) => c.trim().toLowerCase());
  const ignoredNames = new Set();

  categories.forEach((cat) => {
    if (CATEGORY_MAP[cat]) {
      CATEGORY_MAP[cat].forEach((name) => ignoredNames.add(name));
    } else if (cat) {
      console.warn(
        colorize(
          `Warning: Unknown category "${cat}". Valid: ${VALID_CATEGORIES}`,
          "yellow",
        ),
      );
    }
  });

  return ignoredNames;
}

// Colors for terminal output
const colors = {
  red: "\x1b[31m",
  yellow: "\x1b[33m",
  green: "\x1b[32m",
  cyan: "\x1b[36m",
  reset: "\x1b[0m",
  bold: "\x1b[1m",
};

function colorize(text, color) {
  return `${colors[color]}${text}${colors.reset}`;
}

function getFilesRecursively(dir, files = []) {
  if (!fs.existsSync(dir)) {
    return files;
  }

  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      // Skip hidden directories and node_modules
      if (!entry.name.startsWith(".") && entry.name !== "node_modules") {
        getFilesRecursively(fullPath, files);
      }
    } else if (entry.isFile()) {
      const ext = path.extname(entry.name).toLowerCase();
      if (EXTENSIONS.includes(ext)) {
        files.push(fullPath);
      }
    }
  }

  return files;
}

function validateFile(filePath, ignoredNames) {
  const content = fs.readFileSync(filePath, "utf8");
  const lines = content.split("\n");
  const violations = [];

  lines.forEach((line, lineIndex) => {
    RESTRICTIONS.forEach((restriction) => {
      if (ignoredNames.has(restriction.name)) return;

      let match;
      const regex = new RegExp(
        restriction.pattern.source,
        restriction.pattern.flags,
      );

      while ((match = regex.exec(line)) !== null) {
        violations.push({
          file: filePath,
          line: lineIndex + 1,
          column: match.index + 1,
          character: match[0],
          name: restriction.name,
          unicode: restriction.unicode,
          replacement: restriction.replacement,
          severity: restriction.severity,
          context: line
            .substring(Math.max(0, match.index - 20), match.index + 20)
            .trim(),
        });
      }
    });
  });

  return violations;
}

function printViolation(v) {
  const severityColor = v.severity === "error" ? "red" : "yellow";
  const severityLabel = v.severity === "error" ? "ERROR" : "WARN";

  console.log(
    `  ${colorize(severityLabel, severityColor)} ` +
      `${colorize(v.file, "cyan")}:${v.line}:${v.column}`,
  );
  console.log(
    `    ${colorize(v.name, "bold")} (${v.unicode}) found: "${v.character}"`,
  );
  console.log(`    Replace with: ${v.replacement}`);
  console.log(`    Context: ...${v.context}...`);
  console.log();
}

function main() {
  const args = process.argv.slice(2);

  // Parse --ignore flag
  const ignoredNames = parseIgnoreCategories(args);

  // Filter out flag arguments to get directories
  const directories = args.filter((arg) => !arg.startsWith("--"));

  if (directories.length === 0) {
    console.error(
      "Usage: node validate-character-restrictions.js [--ignore=categories] <directory> [directory...]",
    );
    console.error(
      "Example: node validate-character-restrictions.js _posts content _docs",
    );
    console.error(
      "Example: node validate-character-restrictions.js --ignore=emojis,em-dash _posts",
    );
    console.error(
      "Categories: emojis, em-dash, en-dash, smart-quotes, ellipsis, bullet, arrow",
    );
    process.exit(2);
  }

  // Validate directories exist
  const invalidDirs = directories.filter((dir) => !fs.existsSync(dir));
  if (invalidDirs.length > 0) {
    console.error(`Error: Directory not found: ${invalidDirs.join(", ")}`);
    process.exit(2);
  }

  console.log(colorize("\n=== Character Restriction Validation ===\n", "bold"));

  if (ignoredNames.size > 0) {
    console.log(
      colorize(
        "Ignoring categories: " + Array.from(ignoredNames).join(", "),
        "yellow",
      ),
    );
    console.log();
  }

  let allViolations = [];
  let totalFiles = 0;

  for (const dir of directories) {
    const files = getFilesRecursively(dir);
    totalFiles += files.length;

    for (const file of files) {
      const violations = validateFile(file, ignoredNames);
      allViolations = allViolations.concat(violations);
    }
  }

  // Group violations by file
  const byFile = {};
  for (const v of allViolations) {
    if (!byFile[v.file]) {
      byFile[v.file] = [];
    }
    byFile[v.file].push(v);
  }

  // Print results
  if (allViolations.length === 0) {
    console.log(
      colorize("No character restriction violations found.", "green"),
    );
    console.log(`  Checked ${totalFiles} files in: ${directories.join(", ")}`);
    process.exit(0);
  }

  const errors = allViolations.filter((v) => v.severity === "error").length;
  const warnings = allViolations.filter((v) => v.severity === "warning").length;

  console.log(
    colorize(`Found ${allViolations.length} violations `, "bold") +
      `(${colorize(errors + " errors", "red")}, ${colorize(warnings + " warnings", "yellow")})\n`,
  );

  for (const [file, violations] of Object.entries(byFile)) {
    console.log(colorize(`${file} (${violations.length} violations):`, "bold"));
    for (const v of violations) {
      printViolation(v);
    }
  }

  // Summary
  console.log(colorize("=== Summary ===", "bold"));
  console.log(`  Files checked: ${totalFiles}`);
  console.log(`  Files with violations: ${Object.keys(byFile).length}`);
  console.log(`  Total violations: ${allViolations.length}`);
  console.log(`  Errors: ${errors}`);
  console.log(`  Warnings: ${warnings}`);
  console.log();
  const ignoreFlag =
    ignoredNames.size > 0
      ? ` --ignore=${Object.keys(CATEGORY_MAP)
          .filter((cat) =>
            CATEGORY_MAP[cat].some((name) => ignoredNames.has(name)),
          )
          .join(",")}`
      : "";
  console.log(
    `Run fix script to auto-correct: node fix-character-restrictions.js${ignoreFlag} ${directories.join(" ")}`,
  );

  process.exit(errors > 0 ? 1 : 0);
}

main();
