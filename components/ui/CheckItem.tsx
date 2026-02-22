import { CheckCircle2 } from "lucide-react";

interface CheckItemProps {
  children: React.ReactNode;
}

export default function CheckItem({ children }: CheckItemProps) {
  return (
    <li className="flex items-start gap-3">
      <CheckCircle2
        size={20}
        className="text-brand-red shrink-0 mt-0.5"
        aria-hidden="true"
      />
      <span className="text-brand-text text-sm">{children}</span>
    </li>
  );
}
