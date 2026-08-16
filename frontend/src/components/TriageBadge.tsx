import React from 'react';

interface TriageBadgeProps {
  tier: string;
}

export const TriageBadge: React.FC<TriageBadgeProps> = ({ tier }) => {
  let badgeColor = '';
  switch (tier) {
    case 'Red':
      badgeColor = 'bg-red-100 text-red-800 border-red-200';
      break;
    case 'Orange':
      badgeColor = 'bg-orange-100 text-orange-800 border-orange-200';
      break;
    case 'Yellow':
      badgeColor = 'bg-yellow-100 text-yellow-800 border-yellow-200';
      break;
    case 'Green':
    default:
      badgeColor = 'bg-green-100 text-green-800 border-green-200';
      break;
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${badgeColor}`}>
      {tier}
    </span>
  );
};
