"""Resource Recommender Agent - Parallel execution with Google Search integration.

This agent runs in parallel to discover and recommend relevant learning resources
from the web using Google Search API integration.
"""

import logging
from typing import Dict, List, Any
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResourceRecommenderAgent:
    """Agent for discovering and recommending learning resources.
    
    Demonstrates:
    - Parallel agent execution pattern
    - External tool integration (Google Search)
    - Resource discovery and curation
    - Content relevance ranking
    """
    
    def __init__(self):
        """Initialize Resource Recommender agent."""
        self.name = "Resource Recommender"
        self.agent_type = "PARALLEL"
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        logger.info(f"Initialized {self.name} Agent (Type: {self.agent_type})")
    
    async def recommend_resources(self, session_id: str, topic: str, 
                                 learning_level: str = "beginner",
                                 resource_types: List[str] = None) -> Dict[str, Any]:
        """Discover and recommend learning resources for a topic.
        
        Args:
            session_id: Active session identifier
            topic: Learning topic or subject
            learning_level: Student's proficiency level (beginner/intermediate/advanced)
            resource_types: Preferred resource types (videos, articles, practice, etc.)
            
        Returns:
            Curated list of recommended resources with metadata
        """
        try:
            logger.info(f"[{session_id}] Finding resources for topic: {topic} (level: {learning_level})")
            
            if resource_types is None:
                resource_types = ["video", "article", "practice"]
            
            # Build search queries for different resource types
            search_queries = self._build_search_queries(topic, learning_level, resource_types)
            
            # Execute searches (would use Google Custom Search API in production)
            search_results = await self._execute_searches(search_queries)
            
            # Curate and rank resources
            curated_resources = self._curate_resources(search_results, resource_types)
            
            # Generate resource recommendations
            recommendations = {
                "session_id": session_id,
                "topic": topic,
                "learning_level": learning_level,
                "resources": curated_resources,
                "total_found": len(curated_resources),
                "agent": self.name
            }
            
            logger.info(f"[{session_id}] Found {len(curated_resources)} resources for {topic}")
            return recommendations
            
        except Exception as e:
            logger.error(f"[{session_id}] Resource recommendation failed: {e}")
            return {
                "session_id": session_id,
                "topic": topic,
                "error": str(e),
                "resources": [],
                "agent": self.name
            }
    
    def _build_search_queries(self, topic: str, level: str, resource_types: List[str]) -> Dict[str, str]:
        """Build optimized search queries for different resource types.
        
        Args:
            topic: Learning topic
            level: Student proficiency level
            resource_types: Types of resources to search for
            
        Returns:
            Dictionary mapping resource type to search query
        """
        queries = {}
        
        # Level-specific query modifiers
        level_modifiers = {
            "beginner": "introduction basics tutorial explained simply",
            "intermediate": "concepts guide examples",
            "advanced": "advanced in-depth comprehensive"
        }
        
        modifier = level_modifiers.get(level, "tutorial")
        
        # Build queries for each resource type
        if "video" in resource_types:
            queries["video"] = f"{topic} {modifier} video tutorial youtube khan academy"
        
        if "article" in resource_types:
            queries["article"] = f"{topic} {modifier} article guide explanation"
        
        if "practice" in resource_types:
            queries["practice"] = f"{topic} practice problems exercises worksheets"
        
        if "interactive" in resource_types:
            queries["interactive"] = f"{topic} interactive simulation experiment online"
        
        return queries
    
    async def _execute_searches(self, queries: Dict[str, str]) -> Dict[str, List[Dict]]:
        """Execute searches using Google Custom Search API.
        
        Args:
            queries: Dictionary of resource type to search query
            
        Returns:
            Dictionary of resource type to search results
        """
        results = {}
        
        # In production, would call Google Custom Search API
        # For now, return mock data demonstrating structure
        
        for resource_type, query in queries.items():
            logger.info(f"Searching for {resource_type}: {query}")
            
            # Mock search results (would be replaced with actual API calls)
            mock_results = self._generate_mock_results(resource_type, query)
            results[resource_type] = mock_results
        
        return results
    
    def _generate_mock_results(self, resource_type: str, query: str) -> List[Dict[str, Any]]:
        """Generate mock search results for demonstration.
        
        Args:
            resource_type: Type of resource
            query: Search query
            
        Returns:
            List of mock search results
        """
        # Mock data structure matching Google Custom Search API response
        topic_keywords = query.split()[0]  # Extract main topic
        
        if resource_type == "video":
            return [
                {
                    "title": f"{topic_keywords} - Complete Tutorial for Beginners",
                    "url": f"https://youtube.com/watch?v=example1",
                    "description": f"Comprehensive video tutorial covering {topic_keywords} fundamentals",
                    "source": "YouTube",
                    "duration": "15:32"
                },
                {
                    "title": f"Khan Academy: {topic_keywords} Explained",
                    "url": f"https://khanacademy.org/{topic_keywords.lower()}",
                    "description": f"Interactive lessons on {topic_keywords} with practice exercises",
                    "source": "Khan Academy",
                    "duration": "10:45"
                }
            ]
        
        elif resource_type == "article":
            return [
                {
                    "title": f"Understanding {topic_keywords}: A Complete Guide",
                    "url": f"https://example.com/guide/{topic_keywords.lower()}",
                    "description": f"Detailed article explaining {topic_keywords} concepts with examples",
                    "source": "Educational Site",
                    "read_time": "8 min"
                },
                {
                    "title": f"{topic_keywords} - Step by Step Explanation",
                    "url": f"https://sciencebuddy.org/{topic_keywords.lower()}",
                    "description": f"Learn {topic_keywords} through clear, visual explanations",
                    "source": "Science Buddy",
                    "read_time": "6 min"
                }
            ]
        
        elif resource_type == "practice":
            return [
                {
                    "title": f"{topic_keywords} Practice Problems with Solutions",
                    "url": f"https://practice.com/{topic_keywords.lower()}",
                    "description": f"50+ practice problems on {topic_keywords} with detailed solutions",
                    "source": "Practice Hub",
                    "problems": "50+"
                },
                {
                    "title": f"Interactive {topic_keywords} Exercises",
                    "url": f"https://brilliant.org/{topic_keywords.lower()}",
                    "description": f"Engaging exercises to master {topic_keywords}",
                    "source": "Brilliant.org",
                    "problems": "30+"
                }
            ]
        
        return []
    
    def _curate_resources(self, search_results: Dict[str, List[Dict]], 
                         resource_types: List[str]) -> List[Dict[str, Any]]:
        """Curate and rank resources from search results.
        
        Args:
            search_results: Raw search results by resource type
            resource_types: Requested resource types
            
        Returns:
            Curated and ranked list of resources
        """
        curated = []
        
        # Prioritize resource types based on learning effectiveness
        priority_order = ["video", "interactive", "article", "practice"]
        
        for resource_type in priority_order:
            if resource_type in search_results:
                results = search_results[resource_type]
                
                for idx, result in enumerate(results[:3]):  # Top 3 per type
                    curated.append({
                        "type": resource_type,
                        "title": result.get("title"),
                        "url": result.get("url"),
                        "description": result.get("description"),
                        "source": result.get("source"),
                        "metadata": {
                            k: v for k, v in result.items() 
                            if k not in ["title", "url", "description", "source"]
                        },
                        "relevance_score": 1.0 - (idx * 0.1)  # Simple ranking
                    })
        
        # Sort by relevance score
        curated.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return curated


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_resource_recommender():
        agent = ResourceRecommenderAgent()
        
        # Test recommendation for Physics topic
        result = await agent.recommend_resources(
            session_id="test-session-002",
            topic="Newton's Laws of Motion",
            learning_level="beginner",
            resource_types=["video", "article", "practice"]
        )
        
        print("\n=== Resource Recommendations ===")
        print(f"Topic: {result['topic']}")
        print(f"Level: {result['learning_level']}")
        print(f"Total Resources Found: {result['total_found']}\n")
        
        for resource in result['resources'][:5]:  # Show top 5
            print(f"[{resource['type'].upper()}] {resource['title']}")
            print(f"  Source: {resource['source']}")
            print(f"  URL: {resource['url']}")
            print(f"  Score: {resource['relevance_score']:.2f}\n")
    
    asyncio.run(test_resource_recommender())
