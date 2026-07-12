use std::env;

fn ema(values: &[f64], period: usize) -> Vec<f64> {
    if values.is_empty() || period == 0 {
        return vec![];
    }
    let alpha = 2.0 / (period as f64 + 1.0);
    let mut out = vec![values[0]];
    for value in &values[1..] {
        let previous = *out.last().unwrap();
        out.push((value * alpha) + (previous * (1.0 - alpha)));
    }
    out
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 3 {
        println!("usage: indicators-rust <period> <comma-separated-prices>");
        return;
    }
    let period: usize = args[1].parse().unwrap_or(12);
    let prices: Vec<f64> = args[2]
        .split(',')
        .filter_map(|item| item.trim().parse::<f64>().ok())
        .collect();
    let values = ema(&prices, period);
    if let Some(last) = values.last() {
        println!("{last:.8}");
    }
}
