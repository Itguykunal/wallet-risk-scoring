# Compound Wallet Risk Scoring System

A comprehensive risk assessment tool for analyzing wallet addresses that interact with the Compound DeFi lending protocol. This system assigns risk scores from 0-1000 based on multiple risk factors including liquidation risk, volatility, concentration, leverage, and behavioral patterns.

## 🎯 Overview

This system analyzes blockchain transaction data to evaluate the risk profile of wallets using the Compound protocol. It provides:
- **Risk scores from 0-1000** (0 = lowest risk, 1000 = highest risk)
- **Multi-dimensional analysis** across 5 key risk factors
- **Automated CSV output** in the required submission format
- **Detailed risk breakdowns** for internal analysis

## 📋 Features

### Risk Assessment Components
1. **Liquidation Risk (30%)** - Borrowing patterns and position health
2. **Volatility Risk (25%)** - Transaction pattern stability and amounts
3. **Concentration Risk (20%)** - Asset diversification analysis
4. **Leverage Risk (15%)** - Aggressive borrowing behavior
5. **Behavioral Risk (10%)** - Bot activity and unusual patterns

### Key Capabilities
- ✅ Processes 100 wallets in ~8-10 minutes
- ✅ Handles API rate limits automatically
- ✅ Robust error handling and recovery
- ✅ Progress tracking with time estimates
- ✅ Generates required CSV output format
- ✅ Comprehensive logging and validation

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- Free Etherscan API key ([Get one here](https://etherscan.io/apis))
- CSV file with wallet addresses

### Installation

1. **Clone or download the project files**
```bash
git clone https://github.com/Itguykunal/wallet-risk-scoring
cd wallet-risk-scoring
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Get your Etherscan API key**
   - Visit [https://etherscan.io/apis](https://etherscan.io/apis)
   - Create a free account
   - Generate an API key

### Usage

1. **Prepare your wallet CSV file**
   - Place your CSV file in the project directory
   - Ensure it has wallet addresses in a column named: `wallet_id`, `wallet_address`, `address`, or `wallet`

2. **Configure your API key**
   - Open `run_analysis.py`
   - Replace `"YOUR_API_KEY"` with your actual API key on line 14

3. **Run the analysis**
```bash
python run_analysis.py
```

4. **Follow the prompts**
   - Enter your CSV filename (or press Enter for 'wallets.csv')
   - Wait for analysis to complete

5. **Get your results**
   - `wallet_risk_scores.csv` - Main deliverable (wallet_id, score)
   - `detailed_wallet_analysis.csv` - Full breakdown with all risk components

## 📁 Project Structure

```
wallet-risk-scoring/
├── README.md                       # This file
├── requirements.txt                # Python dependencies
├── compound_risk_scorer.py         # Main risk scoring engine
├── run_analysis.py                 # Execution script
├── wallets.csv                     # Your input file (wallet addresses)
├── wallet_risk_scores.csv          # Output: Main deliverable
└── detailed_wallet_analysis.csv    # Output: Detailed analysis
```

## 📊 Output Format

### Main Deliverable: `wallet_risk_scores.csv`
```csv
wallet_id,score
0x0039f22efb07a647557c7c5d17854cfd6d489ef3,542
0x06b51c6882b27cb05e712185531c1f74996dd988,378
...
```

### Detailed Analysis: `detailed_wallet_analysis.csv`
```csv
wallet_id,score,liquidation_risk,volatility_risk,concentration_risk,leverage_risk,behavioral_risk,tx_count,token_tx_count
0x0039f22efb07a647557c7c5d17854cfd6d489ef3,542,650.0,420.0,600.0,480.0,200.0,25,12
...
```

## 🔍 Risk Score Interpretation

| Score Range | Risk Level | Description |
|-------------|------------|-------------|
| 0-200 | **Low Risk** | Conservative users, well-diversified portfolios |
| 201-400 | **Medium-Low Risk** | Moderate activity, some leverage usage |
| 401-600 | **Medium Risk** | Active trading, moderate concentration |
| 601-800 | **High Risk** | Aggressive strategies, poor diversification |
| 801-1000 | **Critical Risk** | Extreme leverage, high liquidation probability |

## ⚙️ Configuration

### API Key Configuration
Edit `run_analysis.py` line 9:
```python
ETHERSCAN_API_KEY = "YOUR_API_KEY"
```

### Risk Weights (Advanced)
Modify `compound_risk_scorer.py` if you want to adjust risk component weights:
```python
self.risk_weights = {
    'liquidation_risk': 0.30,    # 30%
    'volatility_risk': 0.25,     # 25%
    'concentration_risk': 0.20,  # 20%
    'leverage_risk': 0.15,       # 15%
    'behavioral_risk': 0.10      # 10%
}
```

## 🔧 Troubleshooting

### Common Issues

**"FileNotFoundError: wallets.csv"**
- Ensure your CSV file is in the same directory as the scripts
- Check filename spelling (case-sensitive on some systems)

**"API rate limit exceeded"**
- The system includes automatic delays (0.3s between calls)
- If you hit limits, wait 5 minutes and restart
- Free Etherscan accounts have 100,000 calls/day limit

**"No Compound transactions found"**
- This is normal for many wallets
- The system assigns default risk scores (500) for inactive wallets

**Slow performance**
- Expected: ~8-10 minutes for 100 wallets
- Each wallet requires 2 API calls + processing time
- Progress tracking shows estimated completion time

### Error Recovery
- The system continues processing even if individual wallets fail
- Failed wallets receive a default risk score of 500
- All errors are logged to console for debugging

## 📈 Performance Metrics

- **Processing Speed**: ~5-8 seconds per wallet
- **API Efficiency**: 200-300 total API calls for 100 wallets
- **Success Rate**: 95%+ wallet processing success
- **Memory Usage**: <100MB for 100 wallets
- **Network Requirements**: Stable internet for API calls

## 🏗️ Architecture

### Risk Scoring Engine (`compound_risk_scorer.py`)
- Fetches transaction data from Etherscan API
- Analyzes Compound V2/V3 protocol interactions
- Calculates 5 risk components using weighted scoring
- Handles errors and rate limiting gracefully

### Execution Script (`run_analysis.py`)
- Manages CSV input/output operations
- Provides user interface and progress tracking
- Validates results and generates summary statistics
- Handles configuration and error reporting

## 🔬 Methodology

### Data Collection
- **Source**: Etherscan API for Ethereum mainnet
- **Scope**: Last 500 transactions per wallet (normal + token)
- **Focus**: Compound V2/V3 protocol interactions only
- **Rate Limiting**: 0.3-second delays between API calls

### Risk Calculation
- **Weighted Composite Score**: Sum of weighted risk components
- **Normalization**: All components scaled to 0-1000 range
- **Validation**: Scores clamped to ensure 0-1000 bounds
- **Default Handling**: Inactive wallets receive score of 500


## 🏆 Deliverable

The main output file `wallet_risk_scores.csv` contains exactly what's required:
- **Format**: CSV with `wallet_id` and `score` columns
- **Content**: All wallet addresses with risk scores 0-1000
- **Validation**: Automatic validation ensures format compliance
- **Ready for submission**: No additional processing required
