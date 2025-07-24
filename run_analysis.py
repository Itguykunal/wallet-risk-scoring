import pandas as pd
import sys
import os
from datetime import datetime
from compound_risk_scorer import CompoundWalletRiskScorer

# ===== CONFIGURATION =====
# Set your Etherscan API key here (get free key from https://etherscan.io/apis)
ETHERSCAN_API_KEY = "YOUR_API_KEY"  # Replace with your actual API key

def main():
    """
    Main execution function to score all wallets and generate deliverables
    """
    print("=== Compound Wallet Risk Scoring System ===")
    print(f"Starting analysis at: {datetime.now()}")
    
    # Load wallet addresses from CSV file
    csv_filename = input("Enter your CSV filename (or press Enter for 'wallets.csv'): ").strip()
    if not csv_filename:
        csv_filename = "wallets.csv"
    
    print(f"Loading wallet addresses from: {csv_filename}")
    
    try:
        df = pd.read_csv(csv_filename)
        
        # Try different possible column names
        possible_columns = ['wallet_id', 'wallet_address', 'address', 'wallet']
        wallet_column = None
        
        for col in possible_columns:
            if col in df.columns:
                wallet_column = col
                break
        
        if wallet_column is None:
            wallet_column = df.columns[0]
            print(f"Using first column '{wallet_column}' as wallet addresses")
        
        wallet_addresses = df[wallet_column].astype(str).tolist()
        wallet_addresses = [addr.strip() for addr in wallet_addresses if addr.strip()]
        
        print(f"Successfully loaded {len(wallet_addresses)} wallet addresses")
        
    except FileNotFoundError:
        print(f"Error: Could not find {csv_filename} in the current directory")
        print("Please make sure your CSV file is in the same folder as this script")
        return None, None
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None, None
    
    # Use the API key from the configuration variable
    api_key = ETHERSCAN_API_KEY
    
    # Also check environment variable as backup
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        api_key = os.getenv('ETHERSCAN_API_KEY')
        
    if not api_key:
        print("No API key found. Please:")
        print("1. Set ETHERSCAN_API_KEY variable at the top of this script, OR")
        print("2. Set ETHERSCAN_API_KEY environment variable")
        api_key = input("Enter your Etherscan API key: ").strip()
        
    if not api_key:
        print("ERROR: No API key provided. Cannot proceed.")
        return None, None
    
    print(f"Using API key: {api_key[:8]}...")  # Show first 8 characters for confirmation
    
    # Initialize scorer
    scorer = CompoundWalletRiskScorer(api_key=api_key)
    
    print(f"Total wallets to analyze: {len(wallet_addresses)}")
    print("\n--- Starting Risk Analysis ---")
    
    # Score all wallets
    results_df = scorer.score_wallet_list(wallet_addresses)
    
    # Generate the required deliverable (wallet_id, score only)
    deliverable_df = results_df[['wallet_id', 'score']].copy()
    
    # Save main deliverable
    deliverable_file = 'wallet_risk_scores.csv'
    deliverable_df.to_csv(deliverable_file, index=False)
    
    # Save detailed analysis for internal use
    detailed_file = 'detailed_wallet_analysis.csv'
    results_df.to_csv(detailed_file, index=False)
    
    # Generate summary statistics
    print("\n=== ANALYSIS COMPLETE ===")
    print(f"Results saved to: {deliverable_file}")
    print(f"Detailed analysis saved to: {detailed_file}")
    
    print("\n--- Risk Score Statistics ---")
    print(f"Average Risk Score: {results_df['score'].mean():.1f}")
    print(f"Median Risk Score: {results_df['score'].median():.1f}")
    print(f"Minimum Risk Score: {results_df['score'].min()}")
    print(f"Maximum Risk Score: {results_df['score'].max()}")
    print(f"Standard Deviation: {results_df['score'].std():.1f}")
    
    # Risk distribution
    print("\n--- Risk Distribution ---")
    low_risk = (results_df['score'] <= 200).sum()
    med_low_risk = ((results_df['score'] > 200) & (results_df['score'] <= 400)).sum()
    medium_risk = ((results_df['score'] > 400) & (results_df['score'] <= 600)).sum()
    high_risk = ((results_df['score'] > 600) & (results_df['score'] <= 800)).sum()
    critical_risk = (results_df['score'] > 800).sum()
    
    print(f"Low Risk (0-200): {low_risk} wallets ({low_risk/len(results_df)*100:.1f}%)")
    print(f"Medium-Low Risk (201-400): {med_low_risk} wallets ({med_low_risk/len(results_df)*100:.1f}%)")
    print(f"Medium Risk (401-600): {medium_risk} wallets ({medium_risk/len(results_df)*100:.1f}%)")
    print(f"High Risk (601-800): {high_risk} wallets ({high_risk/len(results_df)*100:.1f}%)")
    print(f"Critical Risk (801-1000): {critical_risk} wallets ({critical_risk/len(results_df)*100:.1f}%)")
    
    # Top 10 riskiest wallets
    print("\n--- Top 10 Riskiest Wallets ---")
    top_risky = results_df.nlargest(10, 'score')[['wallet_id', 'score']]
    for idx, row in top_risky.iterrows():
        print(f"{row['wallet_id']}: {row['score']}")
    
    # Top 10 safest wallets  
    print("\n--- Top 10 Safest Wallets ---")
    top_safe = results_df.nsmallest(10, 'score')[['wallet_id', 'score']]
    for idx, row in top_safe.iterrows():
        print(f"{row['wallet_id']}: {row['score']}")
    
    # Component analysis
    print("\n--- Average Risk Component Scores ---")
    print(f"Liquidation Risk: {results_df['liquidation_risk'].mean():.1f}")
    print(f"Volatility Risk: {results_df['volatility_risk'].mean():.1f}")
    print(f"Concentration Risk: {results_df['concentration_risk'].mean():.1f}")
    print(f"Leverage Risk: {results_df['leverage_risk'].mean():.1f}")
    print(f"Behavioral Risk: {results_df['behavioral_risk'].mean():.1f}")
    
    # Transaction analysis
    print("\n--- Transaction Analysis ---")
    print(f"Average Compound Transactions per Wallet: {results_df['tx_count'].mean():.1f}")
    print(f"Average Token Transactions per Wallet: {results_df['token_tx_count'].mean():.1f}")
    active_wallets = (results_df['tx_count'] > 0).sum()
    print(f"Active Wallets (with Compound transactions): {active_wallets} ({active_wallets/len(results_df)*100:.1f}%)")
    
    return deliverable_df, results_df

def validate_deliverable(df):
    """
    Validate the deliverable meets requirements
    """
    print("\n--- Validating Deliverable ---")
    
    # Check required columns
    required_cols = ['wallet_id', 'score']
    if not all(col in df.columns for col in required_cols):
        print("ERROR: Missing required columns")
        return False
    
    # Check score range
    if not all((df['score'] >= 0) & (df['score'] <= 1000)):
        print("ERROR: Scores outside valid range (0-1000)")
        return False
    
    # Check for duplicates
    if df['wallet_id'].duplicated().any():
        print("ERROR: Duplicate wallet addresses found")
        return False
    
    # Check data types
    if not pd.api.types.is_numeric_dtype(df['score']):
        print("ERROR: Score column is not numeric")
        return False
    
    print("✅ Deliverable validation PASSED")
    return True

if __name__ == "__main__":
    """
    Main execution
    """
    print("Compound Wallet Risk Scoring System")
    print("====================================")
    
    # Check if CSV file exists
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if csv_files:
        print(f"Found CSV files: {', '.join(csv_files)}")
    
    # Run the actual analysis
    deliverable_df, results_df = main()
    
    # Validate the deliverable
    if deliverable_df is not None:
        validate_deliverable(deliverable_df)
        print("\n🎯 Your deliverable 'wallet_risk_scores.csv' is ready!")
    else:
        print("\n❌ Analysis failed. Please check your CSV file and API key.")