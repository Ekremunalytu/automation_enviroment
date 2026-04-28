import { useState, type CSSProperties, type InputHTMLAttributes } from "react";

import { Eyebrow } from "./Typography";
import { FONT_DISPLAY, FONT_MONO, V3 } from "./tokens";

type FieldProps = {
  label?: string;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  mono?: boolean;
  style?: CSSProperties;
  inputStyle?: CSSProperties;
  inputProps?: Omit<InputHTMLAttributes<HTMLInputElement>, "value" | "onChange" | "placeholder" | "style">;
};

export function Field({ label, placeholder, value, onChange, mono, style, inputStyle, inputProps }: FieldProps) {
  const [focused, setFocused] = useState(false);
  const [hover, setHover] = useState(false);
  const borderColor = focused ? V3.coral : hover ? V3.rule2 : V3.rule;

  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 6, ...style }}>
      {label ? <Eyebrow>{label}</Eyebrow> : null}
      <input
        {...inputProps}
        placeholder={placeholder}
        value={value ?? ""}
        onChange={(event) => onChange?.(event.target.value)}
        onFocus={(event) => {
          setFocused(true);
          inputProps?.onFocus?.(event);
        }}
        onBlur={(event) => {
          setFocused(false);
          inputProps?.onBlur?.(event);
        }}
        onMouseEnter={(event) => {
          setHover(true);
          inputProps?.onMouseEnter?.(event);
        }}
        onMouseLeave={(event) => {
          setHover(false);
          inputProps?.onMouseLeave?.(event);
        }}
        style={{
          width: "100%",
          background: V3.paper2,
          color: V3.ink,
          border: `1px solid ${borderColor}`,
          borderRadius: 0,
          padding: "12px 14px",
          fontSize: 14,
          outline: "none",
          fontFamily: mono ? FONT_MONO : FONT_DISPLAY,
          transition: "border-color 140ms",
          ...inputStyle,
        }}
      />
    </label>
  );
}
