import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class CompoundWalletRiskScorer:
    """
    Comprehensive wallet risk scoring system for Compound V2/V3 protocol users.
    Analyzes transaction history and assigns risk scores from 0-1000.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the risk scorer with API configuration
        """
        self.api_key = api_key
        # Compound V2 Contract Addresses (Ethereum Mainnet)
        self.compound_contracts = {
            'comptroller': '0x3d9819210a31b4691b2a2d1e8c07b6b9b6e4b2c9',
            'ceth': '0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5',
            'cusdc': '0x39aa39c021dfbae8fac545936693ac917d5e7563',
            'cdai': '0x5d3a536e4d6dbd6114cc1ead35777bab948e3643',
            'cusdt': '0xf650c3d88d12db855b8bf7d11be6c55a4e07dcc9',
            'cwbtc': '0xc11b1268c1a384e55c48c2391d8d480264a3a7f4',
            'cuni': '0x35a18000230da775cac24873d00ff85bccded550',
            'ccomp': '0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4'
        }
        
        # Risk scoring weights
        self.risk_weights = {
            'liquidation_risk': 0.30,      # Health factor and utilization
            'volatility_risk': 0.25,       # Transaction frequency and amounts
            'concentration_risk': 0.20,    # Asset diversification
            'leverage_risk': 0.15,         # Borrowing behavior
            'behavioral_risk': 0.10        # Unusual patterns
        }
        
    def get_wallet_transactions(self, wallet_address: str) -> List[Dict]:
        """
        Fetch transaction history for a wallet from Etherscan API
        Focus on Compound protocol interactions
        """
        base_url = "https://api.etherscan.io/api"
        
        # Get normal transactions
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': wallet_address,
            'startblock': 0,
            'endblock': 99999999,
            'page': 1,
            'offset': 1000,
            'sort': 'desc'
        }
        
        if self.api_key:
            params['apikey'] = self.api_key
            
        try:
            response = requests.get(base_url, params=params, timeout=15)
            data = response.json()
            
            if data['status'] == '1' and 'result' in data:
                # Filter for Compound-related transactions
                compound_txs = []
                for tx in data['result'][:500]:  # Limit to recent 500 transactions
                    to_address = tx.get('to', '').lower()
                    if any(contract.lower() in to_address 
                          for contract in self.compound_contracts.values()):
                        compound_txs.append(tx)
                
                return compound_txs
            else:
                # Handle API errors gracefully
                if data.get('message') == 'NOTOK':
                    print(f"API Error for {wallet_address}: {data.get('result', 'Unknown error')}")
                return []
                
        except requests.exceptions.Timeout:
            print(f"Timeout fetching transactions for {wallet_address}")
            return []
        except Exception as e:
            print(f"Error fetching transactions for {wallet_address}: {e}")
            return []
    
    def get_wallet_token_transactions(self, wallet_address: str) -> List[Dict]:
        """
        Fetch ERC-20 token transactions (cToken interactions)
        """
        base_url = "https://api.etherscan.io/api"
        
        params = {
            'module': 'account',
            'action': 'tokentx',
            'address': wallet_address,
            'startblock': 0,
            'endblock': 99999999,
            'page': 1,
            'offset': 1000,
            'sort': 'desc'
        }
        
        if self.api_key:
            params['apikey'] = self.api_key
            
        try:
            response = requests.get(base_url, params=params, timeout=15)
            data = response.json()
            
            if data['status'] == '1' and 'result' in data:
                # Filter for cToken transactions
                ctoken_txs = []
                for tx in data['result'][:500]:
                    contract_addr = tx.get('contractAddress', '').lower()
                    if any(ctoken.lower() in contract_addr 
                          for ctoken in self.compound_contracts.values()):
                        ctoken_txs.append(tx)
                
                return ctoken_txs
            else:
                # Handle API errors gracefully
                if data.get('message') == 'NOTOK':
                    print(f"Token API Error for {wallet_address}: {data.get('result', 'Unknown error')}")
                return []
                
        except requests.exceptions.Timeout:
            print(f"Timeout fetching token transactions for {wallet_address}")
            return []
        except Exception as e:
            print(f"Error fetching token transactions for {wallet_address}: {e}")
            return []
    
    def calculate_liquidation_risk(self, transactions: List[Dict], 
                                 token_transactions: List[Dict]) -> float:
        """
        Calculate liquidation risk based on borrowing patterns and health factors
        """
        if not transactions and not token_transactions:
            return 500  # Medium risk for inactive wallets
        
        all_txs = transactions + token_transactions
        
        # Analyze supply vs borrow patterns
        supply_count = 0
        borrow_count = 0
        total_value = 0
        
        for tx in all_txs[-50:]:  # Recent 50 transactions
            try:
                value = float(tx.get('value', 0)) / 1e18
                total_value += value
                
                # Heuristic: identify supply vs borrow based on transaction patterns
                func_name = tx.get('functionName', '').lower()
                if 'mint' in func_name or 'supply' in func_name:
                    supply_count += 1
                elif 'borrow' in func_name:
                    borrow_count += 1
            except (ValueError, TypeError):
                continue
        
        # Calculate risk factors
        if supply_count + borrow_count == 0:
            utilization_ratio = 0.5  # Neutral for inactive
        else:
            utilization_ratio = borrow_count / (supply_count + borrow_count + 1)
        
        # High utilization = higher risk
        utilization_score = min(utilization_ratio * 1000, 1000)
        
        # Factor in transaction frequency (too frequent = risky)
        if len(all_txs) > 100:
            frequency_penalty = min((len(all_txs) - 100) * 2, 200)
        else:
            frequency_penalty = 0
            
        liquidation_risk = min(utilization_score + frequency_penalty, 1000)
        return liquidation_risk
    
    def calculate_volatility_risk(self, transactions: List[Dict]) -> float:
        """
        Calculate volatility risk based on transaction patterns and amounts
        """
        if not transactions:
            return 300  # Medium-low risk for inactive wallets
        
        # Analyze transaction amounts and timing
        amounts = []
        timestamps = []
        
        for tx in transactions:
            try:
                value = float(tx.get('value', 0)) / 1e18
                timestamp = int(tx.get('timeStamp', 0))
                
                if value > 0:
                    amounts.append(value)
                    timestamps.append(timestamp)
            except (ValueError, TypeError):
                continue
        
        if len(amounts) < 2:
            return 400
        
        # Calculate coefficient of variation for amounts
        amounts_array = np.array(amounts)
        if np.mean(amounts_array) > 0:
            cv_amounts = np.std(amounts_array) / np.mean(amounts_array)
        else:
            cv_amounts = 1
        
        # Calculate transaction frequency volatility
        if len(timestamps) > 1:
            time_diffs = np.diff(sorted(timestamps))
            if np.mean(time_diffs) > 0:
                cv_timing = np.std(time_diffs) / np.mean(time_diffs)
            else:
                cv_timing = 0
        else:
            cv_timing = 0
        
        # Combine volatility measures
        volatility_score = min((cv_amounts * 300) + (cv_timing * 0.01), 1000)
        return volatility_score
    
    def calculate_concentration_risk(self, token_transactions: List[Dict]) -> float:
        """
        Calculate concentration risk based on asset diversification
        """
        if not token_transactions:
            return 600  # High risk for no diversification
        
        # Count unique tokens/assets
        unique_tokens = set()
        token_values = {}
        
        for tx in token_transactions:
            token_addr = tx.get('contractAddress', '').lower()
            token_symbol = tx.get('tokenSymbol', 'UNKNOWN')
            
            unique_tokens.add(token_addr)
            
            # Track value by token
            try:
                decimals = int(tx.get('tokenDecimal', 18))
                value = float(tx.get('value', 0)) / (10 ** decimals)
                if token_symbol not in token_values:
                    token_values[token_symbol] = 0
                token_values[token_symbol] += value
            except (ValueError, TypeError):
                continue
        
        # Calculate concentration score
        num_tokens = len(unique_tokens)
        
        if num_tokens == 0:
            return 800
        elif num_tokens == 1:
            return 700  # Single asset concentration
        elif num_tokens <= 3:
            return 400  # Moderate diversification
        else:
            return 200  # Good diversification
    
    def calculate_leverage_risk(self, transactions: List[Dict]) -> float:
        """
        Calculate leverage risk based on borrowing behavior
        """
        if not transactions:
            return 300
        
        # Analyze function calls to identify leverage patterns
        leverage_indicators = 0
        total_functions = 0
        
        for tx in transactions:
            func_name = tx.get('functionName', '').lower()
            if func_name:  # Only count transactions with identifiable functions
                total_functions += 1
                
                # Count risky function calls
                if any(risky in func_name for risky in 
                      ['borrow', 'repay', 'liquidate', 'redeem']):
                    leverage_indicators += 1
        
        if total_functions == 0:
            return 400
        
        leverage_ratio = leverage_indicators / total_functions
        leverage_score = min(leverage_ratio * 800, 1000)
        
        return leverage_score
    
    def calculate_behavioral_risk(self, transactions: List[Dict], 
                                token_transactions: List[Dict]) -> float:
        """
        Calculate behavioral risk based on unusual patterns
        """
        all_txs = transactions + token_transactions
        
        if not all_txs:
            return 400
        
        risk_flags = 0
        
        # Check for rapid-fire transactions (MEV bot behavior)
        timestamps = []
        for tx in all_txs:
            try:
                timestamp = int(tx.get('timeStamp', 0))
                if timestamp > 0:
                    timestamps.append(timestamp)
            except (ValueError, TypeError):
                continue
        
        timestamps.sort()
        
        rapid_tx_count = 0
        for i in range(1, len(timestamps)):
            if timestamps[i] - timestamps[i-1] < 60:  # Within 1 minute
                rapid_tx_count += 1
        
        if rapid_tx_count > 10:
            risk_flags += 1
        
        # Check for failed transactions (indicator of risky behavior)
        failed_count = sum(1 for tx in transactions 
                          if tx.get('isError', '0') == '1')
        
        if len(transactions) > 0 and failed_count > len(transactions) * 0.1:  # More than 10% failed
            risk_flags += 1
        
        # Check for very large transactions (whale behavior)
        large_tx_count = 0
        for tx in transactions:
            try:
                value = float(tx.get('value', 0)) / 1e18
                if value > 1000:  # Transactions > 1000 ETH
                    large_tx_count += 1
            except (ValueError, TypeError):
                continue
        
        if large_tx_count > 5:
            risk_flags += 1
        
        behavioral_score = min(risk_flags * 200, 1000)
        return behavioral_score
    
    def calculate_wallet_risk_score(self, wallet_address: str) -> Tuple[float, Dict]:
        """
        Calculate comprehensive risk score for a wallet
        """
        print(f"Analyzing wallet: {wallet_address}")
        
        # Fetch transaction data
        transactions = self.get_wallet_transactions(wallet_address)
        token_transactions = self.get_wallet_token_transactions(wallet_address)
        
        # Add small delay to avoid rate limiting
        time.sleep(0.3)  # Slightly longer delay for better rate limiting
        
        # Calculate individual risk components
        liquidation_risk = self.calculate_liquidation_risk(transactions, token_transactions)
        volatility_risk = self.calculate_volatility_risk(transactions)
        concentration_risk = self.calculate_concentration_risk(token_transactions)
        leverage_risk = self.calculate_leverage_risk(transactions)
        behavioral_risk = self.calculate_behavioral_risk(transactions, token_transactions)
        
        # Calculate weighted final score
        final_score = (
            liquidation_risk * self.risk_weights['liquidation_risk'] +
            volatility_risk * self.risk_weights['volatility_risk'] +
            concentration_risk * self.risk_weights['concentration_risk'] +
            leverage_risk * self.risk_weights['leverage_risk'] +
            behavioral_risk * self.risk_weights['behavioral_risk']
        )
        
        # Ensure score is within 0-1000 range
        final_score = max(0, min(1000, round(final_score)))
        
        # Return detailed breakdown
        breakdown = {
            'liquidation_risk': round(liquidation_risk, 1),
            'volatility_risk': round(volatility_risk, 1),
            'concentration_risk': round(concentration_risk, 1),
            'leverage_risk': round(leverage_risk, 1),
            'behavioral_risk': round(behavioral_risk, 1),
            'final_score': final_score,
            'tx_count': len(transactions),
            'token_tx_count': len(token_transactions)
        }
        
        return final_score, breakdown
    
    def score_wallet_list(self, wallet_addresses: List[str]) -> pd.DataFrame:
        """
        Score a list of wallets and return results as DataFrame
        """
        results = []
        total_wallets = len(wallet_addresses)
        
        print(f"Starting analysis of {total_wallets} wallets...")
        start_time = time.time()
        
        for i, wallet in enumerate(wallet_addresses):
            try:
                score, breakdown = self.calculate_wallet_risk_score(wallet)
                
                result = {
                    'wallet_id': wallet,
                    'score': score,
                    'liquidation_risk': breakdown['liquidation_risk'],
                    'volatility_risk': breakdown['volatility_risk'],
                    'concentration_risk': breakdown['concentration_risk'],
                    'leverage_risk': breakdown['leverage_risk'],
                    'behavioral_risk': breakdown['behavioral_risk'],
                    'tx_count': breakdown['tx_count'],
                    'token_tx_count': breakdown['token_tx_count']
                }
                
                results.append(result)
                
                # Progress update
                elapsed = time.time() - start_time
                if i > 0:
                    avg_time_per_wallet = elapsed / (i + 1)
                    remaining_time = avg_time_per_wallet * (total_wallets - i - 1)
                    print(f"Completed {i+1}/{total_wallets}: {wallet} -> Score: {score} "
                          f"(Est. remaining: {remaining_time/60:.1f}m)")
                else:
                    print(f"Completed {i+1}/{total_wallets}: {wallet} -> Score: {score}")
                
            except Exception as e:
                print(f"Error processing {wallet}: {e}")
                # Add default score for failed wallets
                results.append({
                    'wallet_id': wallet,
                    'score': 500,  # Medium risk default
                    'liquidation_risk': 500,
                    'volatility_risk': 500,
                    'concentration_risk': 500,
                    'leverage_risk': 500,
                    'behavioral_risk': 500,
                    'tx_count': 0,
                    'token_tx_count': 0
                })
        
        total_time = time.time() - start_time
        print(f"\nAnalysis completed in {total_time/60:.1f} minutes")
        
        return pd.DataFrame(results)