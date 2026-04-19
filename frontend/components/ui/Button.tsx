"use client";

import { ButtonHTMLAttributes, forwardRef } from "react";

type Variant = "primary" | "secondary" | "ghost" | "brand";
type Size = "sm" | "md" | "lg";

interface Props extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "size"> {
  variant?: Variant;
  size?: Size;
}

const variantClass: Record<Variant, string> = {
  primary: "btn btn-primary",
  secondary: "btn btn-secondary",
  ghost: "btn btn-ghost",
  brand: "btn btn-brand",
};

const sizeClass: Record<Size, string> = {
  sm: "btn-sm",
  md: "",
  lg: "btn-lg",
};

export const Button = forwardRef<HTMLButtonElement, Props>(function Button(
  { variant = "primary", size = "md", className = "", children, ...rest }, ref
) {
  return (
    <button ref={ref}
      className={`${variantClass[variant]} ${sizeClass[size]} ${className}`}
      {...rest}>
      {children}
    </button>
  );
});
