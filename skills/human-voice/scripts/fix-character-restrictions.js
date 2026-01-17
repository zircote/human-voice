#!/usr/bin/env node

/**
 * fix-character-restrictions.js
 * Auto-fixes AI-telltale characters in content files
 *
 * Usage:
 *   node fix-character-restrictions.js [--dry-run] <directory> [directory...]
 *   node fix-character-restrictions.js --dry-run _posts
 *   node fix-character-restrictions.js _posts content _docs
 *
 * Options:
 *   --dry-run  Show what would be changed without modifying files
 *
 * Exit codes:
 *   0 - Success (files fixed or no changes needed)
 *   1 - Error
 */

const fs = require('fs');
const path = require('path');

// Replacement rules
const REPLACEMENTS = [
  // Em dash: context-dependent, default to period for sentence break
  { pattern: /\u2014/g, replacement: '. ', name: 'Em Dash' },
  // En dash: simple hyphen
  { pattern: /\u2013/g, replacement: '-', name: 'En Dash' },
  // Smart double quotes
  { pattern: /[\u201C\u201D]/g, replacement: '"', name: 'Smart Double Quotes' },
  // Smart single quotes / apostrophes
  { pattern: /[\u2018\u2019]/g, replacement: "'", name: 'Smart Single Quotes' },
  // Horizontal ellipsis
  { pattern: /\u2026/g, replacement: '...', name: 'Horizontal Ellipsis' },
  // Bullet character
  { pattern: /\u2022/g, replacement: '-', name: 'Bullet Character' },
  // Common emojis (remove entirely)
  {
    pattern: /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu,
    replacement: '',
    name: 'Emoji'
  },
  // Arrow characters
  { pattern: /\u2192/g, replacement: '->', name: 'Right Arrow' },
  { pattern: /\u2190/g, replacement: '<-', name: 'Left Arrow' },
  { pattern: /\u2194/g, replacement: '<->', name: 'Bidirectional Arrow' },
  { pattern: /[\u2191\u2193]/g, replacement: '', name: 'Vertical Arrow' }
];

// File extensions to process
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

function fixContent(content) {
  let fixed = content;
  const changes = [];

  for (const rule of REPLACEMENTS) {
    const matches = fixed.match(rule.pattern);
    if (matches) {
      changes.push({
        name: rule.name,
        count: matches.length
      });
      fixed = fixed.replace(rule.pattern, rule.replacement);
    }
  }

  // Clean up double spaces that might result from replacements
  fixed = fixed.replace(/  +/g, ' ');

  // Clean up ". ." patterns from em dash replacement
  fixed = fixed.replace(/\. \./g, '.');

  // Clean up space before punctuation
  fixed = fixed.replace(/ ([.,;:!?])/g, '$1');

  return { fixed, changes };
}

function processFile(filePath, dryRun) {
  const original = fs.readFileSync(filePath, 'utf8');
  const { fixed, changes } = fixContent(original);

  if (changes.length === 0) {
    return { modified: false, changes: [] };
  }

  if (!dryRun) {
    fs.writeFileSync(filePath, fixed, 'utf8');
  }

  return { modified: true, changes };
}

function main() {
  const args = process.argv.slice(2);

  // Parse options
  const dryRun = args.includes('--dry-run');
  const directories = args.filter(arg => !arg.startsWith('--'));

  if (directories.length === 0) {
    console.error('Usage: node fix-character-restrictions.js [--dry-run] <directory> [directory...]');
    console.error('Example: node fix-character-restrictions.js --dry-run _posts content _docs');
    process.exit(1);
  }

  // Validate directories
  const invalidDirs = directories.filter(dir => !fs.existsSync(dir));
  if (invalidDirs.length > 0) {
    console.error(`Error: Directory not found: ${invalidDirs.join(', ')}`);
    process.exit(1);
  }

  const modeLabel = dryRun ? '(DRY RUN)' : '';
  console.log(colorize(`\n=== Character Restriction Fix ${modeLabel} ===\n`, 'bold'));

  let totalFiles = 0;
  let modifiedFiles = 0;
  let totalChanges = 0;
  const summary = {};

  for (const dir of directories) {
    const files = getFilesRecursively(dir);
    totalFiles += files.length;

    for (const file of files) {
      const result = processFile(file, dryRun);

      if (result.modified) {
        modifiedFiles++;
        console.log(colorize(`${dryRun ? 'Would fix' : 'Fixed'}: ${file}`, 'cyan'));

        for (const change of result.changes) {
          console.log(`  - ${change.name}: ${change.count} occurrence(s)`);
          totalChanges += change.count;

          if (!summary[change.name]) {
            summary[change.name] = 0;
          }
          summary[change.name] += change.count;
        }
        console.log();
      }
    }
  }

  // Print summary
  console.log(colorize('=== Summary ===', 'bold'));
  console.log(`  Mode: ${dryRun ? 'Dry run (no files modified)' : 'Applied fixes'}`);
  console.log(`  Files checked: ${totalFiles}`);
  console.log(`  Files ${dryRun ? 'needing fixes' : 'modified'}: ${modifiedFiles}`);
  console.log(`  Total replacements: ${totalChanges}`);

  if (Object.keys(summary).length > 0) {
    console.log('\n  By type:');
    for (const [name, count] of Object.entries(summary)) {
      console.log(`    ${name}: ${count}`);
    }
  }

  if (dryRun && modifiedFiles > 0) {
    console.log(colorize('\nRun without --dry-run to apply fixes.', 'yellow'));
  } else if (modifiedFiles === 0) {
    console.log(colorize('\nNo character restrictions found. Content is clean.', 'green'));
  } else {
    console.log(colorize('\nAll fixes applied.', 'green'));
  }

  process.exit(0);
}

main();
