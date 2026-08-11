import type { ButtonHTMLAttributes, ReactNode } from "react";

import styles from "./Shared.module.css";

type ButtonVariant = "primary" | "secondary" | "quiet" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: ButtonVariant;
  icon?: ReactNode;
}

export function Button({ children, variant = "primary", icon, className = "", ...props }: ButtonProps) {
  return (
    <button className={`${styles.button} ${styles[variant]} ${className}`} {...props}>
      <span>{children}</span>
      {icon ? <span className={styles.buttonIcon}>{icon}</span> : null}
    </button>
  );
}
