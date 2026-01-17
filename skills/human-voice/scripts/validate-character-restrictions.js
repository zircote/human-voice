#!/usr/bin/env node

/**
 * validate-character-restrictions.js
 * Detects AI-telltale characters in content files
 *
 * Usage:
 *   node validate-character-restrictions.js <directory> [directory...]
 *   node validate-character-restrictions.js _posts content _docs
 *
 * Exit codes:
 *   0 - No violations found
 *   1 - Violations found
 *   2 - Error (invalid arguments, directory not found)
 */

const fs = require('fs');
const path = require('path');

// Character restrictions with metadata
const RESTRICTIONS = [
  {
    name: 'Em Dash',
    pattern: /\u2014/g,
    unicode: 'U+2014',
    replacement: 'colon (:), comma (,), semicolon (;), or period (.)',
    severity: 'error'
  },
  {
    name: 'En Dash',
    pattern: /\u2013/g,
    unicode: 'U+2013',
    replacement: 'hyphen (-)',
    severity: 'error'
  },
  {
    name: 'Left Double Quote',
    pattern: /\u201C/g,
    unicode: 'U+201C',
    replacement: 'straight quote (")',
    severity: 'error'
  },
  {
    name: 'Right Double Quote',
    pattern: /\u201D/g,
    unicode: 'U+201D',
    replacement: 'straight quote (")',
    severity: 'error'
  },
  {
    name: 'Left Single Quote',
    pattern: /\u2018/g,
    unicode: 'U+2018',
    replacement: "straight apostrophe (')",
    severity: 'error'
  },
  {
    name: 'Right Single Quote',
    pattern: /\u2019/g,
    unicode: 'U+2019',
    replacement: "straight apostrophe (')",
    severity: 'error'
  },
  {
    name: 'Horizontal Ellipsis',
    pattern: /\u2026/g,
    unicode: 'U+2026',
    replacement: 'three periods (...)',
    severity: 'error'
  },
  {
    name: 'Bullet Character',
    pattern: /\u2022/g,
    unicode: 'U+2022',
    replacement: 'markdown list (-)',
    severity: 'error'
  },
  {
    name: 'Emoji',
    pattern: /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu,
    unicode: 'Various',
    replacement: 'remove entirely',
    severity: 'error'
  },
  {
    name: 'Arrow Character',
    pattern: /[\u2190-\u21FF]/g,
    unicode: 'U+2190-21FF',
    replacement: 'ASCII arrow (->)',
    severity: 'warning'
  }
];

// File extensions to check
const EXTENSIONS = ['.md', '.mdx', '.markdown', '.txt'];

// Colors for terminal output
const colors = {
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  green: '\x1b[32m',
  cyan: '\x1b[36m',
  reset: '\x1b[0m',
  bold: '\x1b[1m'
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
      if (!entry.name.startsWith('.') && entry.name !== 'node_modules') {
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

function validateFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  const violations = [];

  lines.forEach((line, lineIndex) => {
    RESTRICTIONS.forEach((restriction) => {
      let match;
      const regex = new RegExp(restriction.pattern.source, restriction.pattern.flags);

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
          context: line.substring(Math.max(0, match.index - 20), match.index + 20).trim()
        });
      }
    });
  });

  return violations;
}

function printViolation(v) {
  const severityColor = v.severity === 'error' ? 'red' : 'yellow';
  const severityLabel = v.severity === 'error' ? 'ERROR' : 'WARN';

  console.log(
    `  ${colorize(severityLabel, severityColor)} ` +
    `${colorize(v.file, 'cyan')}:${v.line}:${v.column}`
  );
  console.log(
    `    ${colorize(v.name, 'bold')} (${v.unicode}) found: "${v.character}"`
  );
  console.log(`    Replace with: ${v.replacement}`);
  console.log(`    Context: ...${v.context}...`);
  console.log();
}

function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.error('Usage: node validate-character-restrictions.js <directory> [directory...]');
    console.error('Example: node validate-character-restrictions.js _posts content _docs');
    process.exit(2);
  }

  // Validate directories exist
  const invalidDirs = args.filter(dir => !fs.existsSync(dir));
  if (invalidDirs.length > 0) {
    console.error(`Error: Directory not found: ${invalidDirs.join(', ')}`);
    process.exit(2);
  }

  console.log(colorize('\n=== Character Restriction Validation ===\n', 'bold'));

  let allViolations = [];
  let totalFiles = 0;

  for (const dir of args) {
    const files = getFilesRecursively(dir);
    totalFiles += files.length;

    for (const file of files) {
      const violations = validateFile(file);
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
    console.log(colorize('No character restriction violations found.', 'green'));
    console.log(`  Checked ${totalFiles} files in: ${args.join(', ')}`);
    process.exit(0);
  }

  const errors = allViolations.filter(v => v.severity === 'error').length;
  const warnings = allViolations.filter(v => v.severity === 'warning').length;

  console.log(
    colorize(`Found ${allViolations.length} violations `, 'bold') +
    `(${colorize(errors + ' errors', 'red')}, ${colorize(warnings + ' warnings', 'yellow')})\n`
  );

  for (const [file, violations] of Object.entries(byFile)) {
    console.log(colorize(`${file} (${violations.length} violations):`, 'bold'));
    for (const v of violations) {
      printViolation(v);
    }
  }

  // Summary
  console.log(colorize('=== Summary ===', 'bold'));
  console.log(`  Files checked: ${totalFiles}`);
  console.log(`  Files with violations: ${Object.keys(byFile).length}`);
  console.log(`  Total violations: ${allViolations.length}`);
  console.log(`  Errors: ${errors}`);
  console.log(`  Warnings: ${warnings}`);
  console.log();
  console.log(`Run fix script to auto-correct: node fix-character-restrictions.js ${args.join(' ')}`);

  process.exit(errors > 0 ? 1 : 0);
}

main();
