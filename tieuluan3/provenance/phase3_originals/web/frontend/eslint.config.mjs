import tseslint from "typescript-eslint";
export default [
  { ignores: ["dist/**", "node_modules/**"] },
  ...tseslint.configs.recommended.map((config) => ({
    ...config,
    files: ["src/v3/**/*.{ts,tsx}"],
  })),
  {
    files: ["src/v3/**/*.{ts,tsx}"],
    rules: {
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_" },
      ],
    },
  },
  {
    files: ["src/v3/**/*.{ts,tsx}"],
    ignores: ["**/*.test.ts", "**/*.test.tsx"],
    rules: {
      "no-console": "error",
      "no-restricted-syntax": [
        "error",
        {
          selector: "JSXAttribute[name.name='dangerouslySetInnerHTML']",
          message: "Render escaped React content, never raw HTML.",
        },
        {
          selector: "CallExpression[callee.name='eval']",
          message: "No eval in public UI.",
        },
        {
          selector: "MemberExpression[property.name='localStorage']",
          message:
            "Private capability stays in sessionStorage, not localStorage.",
        },
      ],
    },
  },
];
