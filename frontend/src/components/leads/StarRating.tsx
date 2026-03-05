import { useState } from "react";
import { Star } from "lucide-react";

interface StarRatingProps {
  onRate: (rating: number) => void;
  size?: number;
}

export function StarRating({ onRate, size = 20 }: StarRatingProps) {
  const [hovered, setHovered] = useState(0);

  return (
    <div
      className="inline-flex gap-0.5"
      onMouseLeave={() => setHovered(0)}
    >
      {[1, 2, 3, 4, 5].map((i) => (
        <button
          key={i}
          onClick={() => onRate(i)}
          onMouseEnter={() => setHovered(i)}
          className="bg-transparent border-none p-0 cursor-pointer leading-none"
          style={{ color: i <= hovered ? "var(--star-color)" : "var(--border)" }}
        >
          <Star size={size} fill={i <= hovered ? "currentColor" : "none"} strokeWidth={1.5} />
        </button>
      ))}
    </div>
  );
}
