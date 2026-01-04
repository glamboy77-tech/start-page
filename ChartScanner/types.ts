export interface ChartEntry {
  rank: number;
  title: string;
  artist: string;
}

export interface ApiError {
  message: string;
  statusCode?: number;
}
