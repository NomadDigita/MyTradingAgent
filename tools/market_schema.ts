export type MarketType = "spot" | "future" | "swap" | "cfd" | "stock";

export type TradePlan = {
  approvalId: string;
  symbol: string;
  side: "buy" | "sell";
  amount: number;
  leverage: number;
  entryPrice: number;
  stopLoss?: number;
  takeProfit?: number;
  marketType: MarketType;
  rationale: string[];
};

export function validateTradePlan(plan: TradePlan): string[] {
  const errors: string[] = [];
  if (!plan.symbol) errors.push("symbol is required");
  if (plan.amount <= 0) errors.push("amount must be positive");
  if (plan.entryPrice <= 0) errors.push("entryPrice must be positive");
  if (plan.leverage < 1 || plan.leverage > 20) errors.push("leverage must be between 1 and 20");
  return errors;
}
