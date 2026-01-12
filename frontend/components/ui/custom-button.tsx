import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes, ReactNode } from "react";

interface CustomButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  className?: string;
}

export default function CustomButton({
  children,
  className,
  ...props
}: CustomButtonProps) {
  return (
    <Button
      {...props}
      className={cn(
        "flex h-10 w-10 items-center justify-center rounded-full bg-white text-gray-700 ring-1 ring-gray-300 transition-all hover:bg-gray-50",
        className
      )}
    >
      {children}
    </Button>
  );
}
