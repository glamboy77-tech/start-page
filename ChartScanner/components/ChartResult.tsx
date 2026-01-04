import React from 'react';
import { ChartEntry } from '../types';

interface ChartResultProps {
  data: ChartEntry[] | null;
}

export const ChartResult: React.FC<ChartResultProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <p className="text-gray-500 text-center py-4">No chart data to display.</p>
    );
  }

  return (
    <pre className="whitespace-pre-wrap break-all bg-gray-800 text-gray-200 p-4 rounded-md text-sm leading-relaxed overflow-x-auto">
      <code>{JSON.stringify(data, null, 2)}</code>
    </pre>
  );
};
