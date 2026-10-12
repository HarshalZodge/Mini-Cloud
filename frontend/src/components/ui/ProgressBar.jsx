import React from 'react';

export const ProgressBar = ({
  percentage = 0,
  label,
  valueText,
  size = 'md', // 'sm' | 'md'
  variant = 'primary', // 'primary' | 'warning' | 'danger'
  className = '',
}) => {
  const clamped = Math.min(100, Math.max(0, percentage));

  const sizeClasses = {
    sm: 'h-1.5',
    md: 'h-2.5',
  };

  const gradientClasses = {
    primary: 'bg-gradient-to-r from-indigo-500 to-violet-500',
    warning: 'bg-gradient-to-r from-amber-500 to-orange-500',
    danger: 'bg-gradient-to-r from-rose-500 to-red-600',
  };

  const activeGradient =
    variant !== 'primary'
      ? gradientClasses[variant]
      : clamped > 90
      ? gradientClasses.danger
      : clamped > 75
      ? gradientClasses.warning
      : gradientClasses.primary;

  return (
    <div className={`w-full ${className}`}>
      {(label || valueText) && (
        <div className="flex justify-between items-center text-xs font-medium text-slate-600 dark:text-slate-400 mb-1.5">
          {label && <span>{label}</span>}
          {valueText && <span className="font-semibold text-slate-700 dark:text-slate-300">{valueText}</span>}
        </div>
      )}
      <div className={`w-full bg-slate-200/60 dark:bg-slate-700/60 rounded-full overflow-hidden ${sizeClasses[size]}`}>
        <div
          className={`${sizeClasses[size]} ${activeGradient} rounded-full transition-all duration-300 ease-out`}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
};
