"use client";

import { useState } from "react";

type Rule = { key: string; test: (value: string) => boolean; message: string };

// Keep in step with backend/app/auth/security.py.
const RULES: Rule[] = [
  { key: "length", test: (v) => v.length >= 8, message: "At least 8 characters are required." },
  { key: "upper", test: (v) => /[A-Z]/.test(v), message: "One capital letter is a minimum requirement." },
  { key: "digit", test: (v) => /[0-9]/.test(v), message: "One number is a minimum requirement." },
  { key: "symbol", test: (v) => /[^A-Za-z0-9]/.test(v), message: "One special character is a minimum requirement." },
];

const HINT = "Min 8 characters, one capital letter, one number, one special character.";

export function passwordProblems(value: string): Rule[] {
  return RULES.filter((rule) => !rule.test(value));
}

export default function PasswordField({
  id,
  label = "Password",
  value,
  onChange,
  submitted = false,
  autoComplete = "new-password",
}: {
  id: string;
  label?: string;
  value: string;
  onChange: (value: string) => void;
  submitted?: boolean;
  autoComplete?: string;
}) {
  const [touched, setTouched] = useState(false);
  const problems = passwordProblems(value);
  const showProblems = (touched || submitted) && problems.length > 0;
  const showHint = value.length === 0 && !showProblems;

  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        type="password"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onBlur={() => setTouched(true)}
        required
        maxLength={128}
        autoComplete={autoComplete}
        aria-invalid={showProblems || undefined}
        aria-describedby={`${id}-rules`}
        className="input"
      />
      <div id={`${id}-rules`} aria-live="polite" style={{ minHeight: 18 }}>
        {showHint && <p className="hint faint">{HINT}</p>}
        {showProblems &&
          problems.map((problem) => (
            <p key={problem.key} className="hint hint--problem">
              {problem.message}
            </p>
          ))}
      </div>
      <style>{`
        @keyframes fl-rule-in {
          from { opacity: 0; transform: translateY(-3px); }
          to { opacity: 1; transform: none; }
        }
        @media (prefers-reduced-motion: reduce) {
          @keyframes fl-rule-in { from { opacity: 1; } to { opacity: 1; } }
        }
      `}</style>
    </div>
  );
}
