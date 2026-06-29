#!/usr/bin/env node
/**
 * Validate a definePluginEntry plugin — checks export structure and tool registration.
 * Usage: node scripts/validate-plugin.mjs
 */
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const entry = require("../dist/index.js").default;

const errors = [];

if (!entry || typeof entry !== "object") {
  errors.push("export.default is not an object");
} else {
  if (!entry.id) errors.push("missing id");
  if (!entry.name) errors.push("missing name");
  if (!entry.description) errors.push("missing description");
  if (typeof entry.register !== "function") errors.push("register is not a function");

  if (entry.register) {
    const registered = [];
    const mockApi = {
      registerTool: (def) => { registered.push(def.name); },
      on: () => {},
    };
    try {
      entry.register(mockApi);
    } catch (e) {
      errors.push(`register() threw: ${String(e)}`);
    }
    if (registered.length === 0) {
      errors.push("register() registered no tools");
    } else {
      console.log(`Tools registered: ${registered.join(", ")}`);
    }
  }
}

if (errors.length > 0) {
  console.error("Validation FAILED:");
  errors.forEach((e) => console.error(`  - ${e}`));
  process.exit(1);
}

console.log(`Plugin "${entry.id}" validated OK`);
