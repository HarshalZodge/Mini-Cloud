import React from 'react';

export const Skeleton = ({
  className = '',
  variant = 'rounded', // 'rounded' | 'circular' | 'text'
}) => {
  const variantClasses = {
    rounded: 'rounded-xl',
    circular: 'rounded-full',
    text: 'rounded-md h-4',
  };

  return (
    <div
      className={`animate-pulse bg-slate-300/40 dark:bg-slate-700/40 backdrop-blur-sm ${variantClasses[variant]} ${className}`}
    />
  );
};
