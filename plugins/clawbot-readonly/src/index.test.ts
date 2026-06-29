import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import entry from "./index.js";

describe("clawbot-readonly", () => {
  it("exports a plugin entry with expected id", () => {
    expect(entry).toBeDefined();
    expect(entry.id).toBe("clawbot-readonly");
  });

  it("has a register function", () => {
    expect(entry.register).toBeDefined();
    expect(typeof entry.register).toBe("function");
  });

  it("keeps the read-only status tool description", () => {
    expect(entry.description).toContain("Read-only status");
  });

  it("does not hardcode private local paths or private persona labels", () => {
    const source = readFileSync(new URL("./index.ts", import.meta.url), "utf8");
    expect(source).not.toContain("/home/" + "rainw");
    expect(source).not.toContain("仝" + "希禾");
  });
});
