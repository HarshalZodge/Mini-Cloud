import React from 'react';

export const GlassCard = ({
  children,
  className = '',
  variant = 'default', // 'subtle' | 'default' | 'strong'
  hover = false,
  highlight = true,
  onClick,
}) => {
  const variantClasses = {
    subtle: 'glass-subtle',
    default: 'glass',
    strong: 'glass-strong',
  };

  const hoverClass = hover
    ? 'transition-all duration-200 hover:-translate-y-0.5 hover:shadow-glass-hover'
    : '';

  const highlightClass = highlight ? 'glass-highlight' : '';

  return (
    <div
      onClick={onClick}
      className={`rounded-2xl ${variantClasses[variant] || 'glass'} ${hoverClass} ${highlightClass} ${className}`}
    >
      {children}
    </div>
  );
};
