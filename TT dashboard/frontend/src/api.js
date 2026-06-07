import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

// Strategies API
export const fetchStrategies = (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.wallet) params.append('wallet', filters.wallet);
  if (filters.status) params.append('status', filters.status);
  if (filters.execution_type) params.append('execution_type', filters.execution_type);
  if (filters.date_from) params.append('date_from', filters.date_from);
  if (filters.date_to) params.append('date_to', filters.date_to);
  
  return apiClient.get('/strategies', { params });
};

export const fetchStrategyDetail = (strategyId) => {
  return apiClient.get(`/strategies/${strategyId}`);
};

export const fetchStrategyTrades = (strategyId, filters = {}) => {
  const params = new URLSearchParams();
  if (filters.counter) params.append('counter', filters.counter);
  if (filters.date_from) params.append('date_from', filters.date_from);
  if (filters.date_to) params.append('date_to', filters.date_to);
  
  return apiClient.get(`/strategies/${strategyId}/trades`, { params });
};

// Dashboard API
export const fetchDashboardSummary = () => {
  return apiClient.get('/dashboard/summary');
};

export const fetchPnlChartData = (strategyId = null, groupBy = 'date') => {
  const params = new URLSearchParams();
  if (strategyId) params.append('strategy_id', strategyId);
  params.append('group_by', groupBy);
  
  return apiClient.get('/dashboard/pnl-chart-data', { params });
};

export const fetchHeatmapData = () => {
  return apiClient.get('/dashboard/heatmap-data');
};

// Refresh API
export const triggerRefresh = () => {
  return apiClient.post('/refresh');
};

// Health check
export const checkHealth = () => {
  return apiClient.get('/health');
};
