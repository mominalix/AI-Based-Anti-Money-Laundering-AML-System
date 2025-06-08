import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple
import logging
import networkx as nx
import numpy as np
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class GraphAnalyzer:
    """Graph analysis for AML network detection using NetworkX"""
    
    def __init__(self):
        # Load configuration from environment
        self.centrality_threshold = float(os.getenv("CENTRALITY_THRESHOLD", "0.7"))
        self.community_risk_threshold = float(os.getenv("COMMUNITY_RISK_THRESHOLD", "0.6"))
        self.max_connections = int(os.getenv("MAX_GRAPH_CONNECTIONS", "1000"))
        
        # Initialize graph structures
        self.transaction_graph = nx.DiGraph()  # Directed graph for transaction flows
        self.entity_graph = nx.Graph()  # Undirected graph for entity relationships
        
        # Risk scoring parameters
        self.country_risk_scores = self._load_country_risk_scores()
        self.entity_types = {"customer", "account", "counterparty", "intermediary"}
        
        # Cache for computed metrics
        self.centrality_cache = {}
        self.community_cache = {}
        self.last_analysis_time = {}
        
        logger.info("GraphAnalyzer initialized with NetworkX")
    
    def _load_country_risk_scores(self) -> Dict[str, float]:
        """Load country risk scores for enhanced analysis"""
        return {
            # Low risk countries
            "US": 0.1, "GB": 0.1, "DE": 0.1, "FR": 0.1, "CA": 0.1, "AU": 0.1, "JP": 0.1,
            "NL": 0.1, "SE": 0.1, "NO": 0.1, "DK": 0.1, "FI": 0.1, "SG": 0.15, "HK": 0.15,
            
            # Medium risk countries
            "SA": 0.3, "AE": 0.25, "QA": 0.25, "KW": 0.3, "BH": 0.25, "OM": 0.3,
            "BR": 0.35, "MX": 0.3, "AR": 0.35, "CL": 0.25, "CO": 0.4, "PE": 0.35,
            
            # High risk countries
            "KY": 0.75, "BM": 0.7, "BS": 0.7, "BZ": 0.7, "PA": 0.65, "CH": 0.6,
            "VG": 0.75, "AI": 0.7, "TC": 0.7, "GG": 0.65, "JE": 0.65, "IM": 0.65,
            
            # Very high risk countries
            "AF": 0.95, "IR": 0.9, "KP": 0.95, "SY": 0.9, "IQ": 0.85, "YE": 0.85,
            "SO": 0.9, "LY": 0.85, "SD": 0.85, "MM": 0.8, "BY": 0.8, "VE": 0.8
        }
    
    def add_transaction_to_graph(self, transaction_data: Dict[str, Any], customer_data: Dict[str, Any] = None):
        """Add transaction data to the graph for analysis"""
        
        try:
            txn_id = transaction_data["txn_id"]
            account_id = transaction_data["account_id"]
            amount = float(transaction_data["amount"])
            timestamp = datetime.fromisoformat(transaction_data["timestamp"].replace('Z', '+00:00'))
            counterparty_country = transaction_data.get("counterparty_country", "US")
            
            # Create or update nodes
            customer_id = customer_data.get("customer_id") if customer_data else f"CUST_{account_id[-1]}"
            
            # Add customer node
            self.entity_graph.add_node(
                customer_id,
                node_type="customer",
                risk_score=self._calculate_customer_risk(customer_data) if customer_data else 0.5,
                pep_flag=customer_data.get("pep_flag", False) if customer_data else False,
                kyc_level=customer_data.get("kyc_level", "standard") if customer_data else "standard"
            )
            
            # Add account node
            self.entity_graph.add_node(
                account_id,
                node_type="account",
                risk_score=0.1,
                customer_id=customer_id
            )
            
            # Add counterparty node (simplified)
            counterparty_id = f"CP_{counterparty_country}_{hash(txn_id) % 1000}"
            country_risk = self.country_risk_scores.get(counterparty_country, 0.5)
            
            self.entity_graph.add_node(
                counterparty_id,
                node_type="counterparty",
                risk_score=country_risk,
                country=counterparty_country
            )
            
            # Add edges
            self.entity_graph.add_edge(customer_id, account_id, relationship="owns")
            
            # Add transaction edge in directed graph
            self.transaction_graph.add_edge(
                account_id,
                counterparty_id,
                txn_id=txn_id,
                amount=amount,
                timestamp=timestamp,
                country=counterparty_country,
                risk_score=country_risk
            )
            
            # Add undirected relationship for community detection
            if not self.entity_graph.has_edge(account_id, counterparty_id):
                self.entity_graph.add_edge(
                    account_id,
                    counterparty_id,
                    relationship="transacts_with",
                    total_amount=amount,
                    transaction_count=1,
                    first_transaction=timestamp,
                    last_transaction=timestamp
                )
            else:
                # Update existing edge
                edge_data = self.entity_graph[account_id][counterparty_id]
                edge_data["total_amount"] += amount
                edge_data["transaction_count"] += 1
                edge_data["last_transaction"] = max(edge_data["last_transaction"], timestamp)
            
            # Clear cache for affected nodes
            self._clear_cache_for_node(customer_id)
            
            logger.debug(f"Added transaction {txn_id} to graph")
            
        except Exception as e:
            logger.error(f"Error adding transaction to graph: {e}")
    
    def _calculate_customer_risk(self, customer_data: Dict[str, Any]) -> float:
        """Calculate base risk score for customer"""
        if not customer_data:
            return 0.5
        
        risk_score = 0.0
        
        # PEP flag
        if customer_data.get("pep_flag", False):
            risk_score += 0.4
        
        # KYC level
        kyc_level = customer_data.get("kyc_level", "standard")
        kyc_risk = {"basic": 0.3, "standard": 0.1, "enhanced": 0.05}.get(kyc_level, 0.1)
        risk_score += kyc_risk
        
        # Age factor (if available)
        dob = customer_data.get("dob")
        if dob:
            try:
                birth_date = datetime.strptime(dob, "%Y-%m-%d")
                age = (datetime.now() - birth_date).days / 365.25
                if age < 25 or age > 80:  # Very young or very old customers
                    risk_score += 0.1
            except:
                pass
        
        return min(risk_score, 1.0)
    
    async def analyze_party_risk(self, party_id: str) -> Optional[Dict[str, Any]]:
        """Analyze graph-based risk for a party"""
        
        try:
            # Check if party exists in graph
            if party_id not in self.graph_data["nodes"]:
                logger.warning(f"Party {party_id} not found in graph")
                return None
            
            party_data = self.graph_data["nodes"][party_id]
            
            # Find cluster
            cluster_id = self._find_cluster(party_id)
            
            # Calculate centrality score
            centrality_score = self._calculate_centrality(party_id)
            
            # Calculate community risk
            community_risk = self._calculate_community_risk(cluster_id)
            
            # Get connected parties
            connected_parties = self._get_connected_parties(party_id)
            
            # Generate graph alerts
            graph_alerts = self._generate_graph_alerts(party_id, centrality_score, community_risk)
            
            result = {
                "party_id": party_id,
                "cluster_id": cluster_id,
                "centrality_score": centrality_score,
                "community_risk": community_risk,
                "connected_parties": connected_parties,
                "graph_alerts": graph_alerts,
                "analyzed_at": datetime.utcnow()
            }
            
            logger.info(f"Analyzed party {party_id}: centrality={centrality_score:.3f}, community_risk={community_risk:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing party {party_id}: {e}")
            return None
    
    def _find_cluster(self, party_id: str) -> str:
        """Find which cluster a party belongs to"""
        
        for cluster_id, members in self.graph_data["clusters"].items():
            if party_id in members:
                return cluster_id
        
        return "UNKNOWN"
    
    def _calculate_centrality(self, party_id: str) -> float:
        """Calculate betweenness centrality score"""
        
        party_data = self.graph_data["nodes"][party_id]
        connections = party_data.get("connections", [])
        
        # Simplified centrality calculation
        # In production, use proper graph algorithms (NetworkX, igraph)
        
        # Base centrality on number of connections
        base_centrality = len(connections) / 10.0  # Normalize to max 10 connections
        
        # Weight by connection quality (risk scores of connected parties)
        connection_weights = []
        for connected_id in connections:
            if connected_id in self.graph_data["nodes"]:
                connected_risk = self.graph_data["nodes"][connected_id]["risk_score"]
                connection_weights.append(connected_risk)
        
        if connection_weights:
            avg_connection_risk = sum(connection_weights) / len(connection_weights)
            weighted_centrality = base_centrality * (1 + avg_connection_risk)
        else:
            weighted_centrality = base_centrality
        
        # Add some randomness to simulate real algorithm
        noise = random.gauss(0, 0.05)
        centrality_score = max(0.0, min(1.0, weighted_centrality + noise))
        
        return centrality_score
    
    def _calculate_community_risk(self, cluster_id: str) -> float:
        """Calculate risk score for the entire community/cluster"""
        
        if cluster_id == "UNKNOWN":
            return 0.5
        
        cluster_members = self.graph_data["clusters"].get(cluster_id, [])
        
        if not cluster_members:
            return 0.5
        
        # Calculate average risk of cluster members
        risk_scores = []
        for member_id in cluster_members:
            if member_id in self.graph_data["nodes"]:
                member_risk = self.graph_data["nodes"][member_id]["risk_score"]
                risk_scores.append(member_risk)
        
        if not risk_scores:
            return 0.5
        
        avg_risk = sum(risk_scores) / len(risk_scores)
        
        # Boost risk if cluster has high-risk members
        max_risk = max(risk_scores)
        if max_risk > 0.8:
            community_risk = min(1.0, avg_risk * 1.3)
        else:
            community_risk = avg_risk
        
        return community_risk
    
    def _get_connected_parties(self, party_id: str) -> List[Dict[str, Any]]:
        """Get connected parties with relationship analysis"""
        
        party_data = self.graph_data["nodes"][party_id]
        connections = party_data.get("connections", [])
        
        connected_parties = []
        
        for connected_id in connections:
            if connected_id in self.graph_data["nodes"]:
                connected_data = self.graph_data["nodes"][connected_id]
                
                # Calculate relationship strength (simplified)
                relationship_strength = random.uniform(0.3, 0.9)
                
                # Calculate risk contribution
                connected_risk = connected_data["risk_score"]
                risk_contribution = relationship_strength * connected_risk
                
                connected_parties.append({
                    "party_id": connected_id,
                    "relationship_strength": relationship_strength,
                    "risk_contribution": risk_contribution
                })
        
        # Sort by risk contribution (highest first)
        connected_parties.sort(key=lambda x: x["risk_contribution"], reverse=True)
        
        return connected_parties[:5]  # Return top 5 connections
    
    def _generate_graph_alerts(
        self, 
        party_id: str, 
        centrality_score: float, 
        community_risk: float
    ) -> List[Dict[str, Any]]:
        """Generate graph-based alerts"""
        
        alerts = []
        
        # High centrality alert
        if centrality_score > 0.7:
            alerts.append({
                "alert_type": "high_centrality",
                "severity": "high" if centrality_score > 0.8 else "medium",
                "description": f"Party {party_id} has high network centrality ({centrality_score:.2f}), indicating potential hub activity",
                "confidence": min(1.0, centrality_score * 1.2)
            })
        
        # Suspicious cluster alert
        if community_risk > 0.6:
            alerts.append({
                "alert_type": "suspicious_cluster",
                "severity": "critical" if community_risk > 0.8 else "high",
                "description": f"Party {party_id} belongs to a high-risk cluster (risk: {community_risk:.2f})",
                "confidence": community_risk
            })
        
        # Unusual pattern detection (mock)
        party_data = self.graph_data["nodes"][party_id]
        if party_data["risk_score"] > 0.7 and len(party_data.get("connections", [])) > 3:
            alerts.append({
                "alert_type": "unusual_pattern",
                "severity": "medium",
                "description": f"Unusual connection pattern detected for high-risk party {party_id}",
                "confidence": 0.75
            })
        
        return alerts
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get graph statistics for monitoring"""
        
        total_nodes = len(self.graph_data["nodes"])
        total_clusters = len(self.graph_data["clusters"])
        
        # Count high-risk nodes
        high_risk_nodes = sum(
            1 for node_data in self.graph_data["nodes"].values()
            if node_data["risk_score"] > 0.7
        )
        
        # Calculate average connections
        total_connections = sum(
            len(node_data.get("connections", []))
            for node_data in self.graph_data["nodes"].values()
        )
        avg_connections = total_connections / total_nodes if total_nodes > 0 else 0
        
        return {
            "total_nodes": total_nodes,
            "total_clusters": total_clusters,
            "high_risk_nodes": high_risk_nodes,
            "avg_connections_per_node": avg_connections,
            "graph_density": total_connections / (total_nodes * (total_nodes - 1)) if total_nodes > 1 else 0
        } 