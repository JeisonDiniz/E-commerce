import { useId, useState, type InputHTMLAttributes, type KeyboardEvent } from "react";
import { IconAlertTriangle, IconEye, IconEyeOff } from "./icons";

interface PasswordInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label?: string;
}

/**
 * Campo de senha com dois cuidados de usabilidade que evitam o erro mais
 * comum de login: alternar visibilidade (evita digitar errado sem perceber)
 * e aviso de Caps Lock ativado (detectado via KeyboardEvent.getModifierState,
 * suportado nos principais navegadores).
 */
export function PasswordInput({ label, className = "", id, ...props }: PasswordInputProps) {
  const [visible, setVisible] = useState(false);
  const [capsLockOn, setCapsLockOn] = useState(false);
  const generatedId = useId();
  const inputId = id ?? generatedId;

  function checkCapsLock(e: KeyboardEvent<HTMLInputElement>) {
    if (typeof e.getModifierState === "function") {
      setCapsLockOn(e.getModifierState("CapsLock"));
    }
  }

  return (
    <div>
      {label && (
        <label htmlFor={inputId} className="mb-1 block text-xs font-medium text-[var(--text-secondary)]">
          {label}
        </label>
      )}
      <div className="relative">
        <input
          id={inputId}
          type={visible ? "text" : "password"}
          onKeyDown={checkCapsLock}
          onKeyUp={checkCapsLock}
          className={`w-full pr-10 ${className}`}
          {...props}
        />
        <button
          type="button"
          tabIndex={-1}
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? "Ocultar senha" : "Mostrar senha"}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--ink)]"
        >
          {visible ? <IconEyeOff width={16} height={16} /> : <IconEye width={16} height={16} />}
        </button>
      </div>
      {capsLockOn && (
        <p className="mt-1 flex items-center gap-1.5 text-xs text-amber-700">
          <IconAlertTriangle width={13} height={13} />
          Caps Lock está ativado
        </p>
      )}
    </div>
  );
}