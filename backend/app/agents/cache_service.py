import json
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime
from backend.app.db.base import get_redis
import logging
from zoneinfo import ZoneInfo 
import time
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

class SemanticCacheService:
    def __init__(self):
        self.redis_client = get_redis()
        self.embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2", 
        model_kwargs={"device": "cpu"}, 
        encode_kwargs={"normalize_embeddings": True}
        )
    
    async def search_similar(self, query: str, course_category: Optional[str], course_name: Optional[str], threshold: float = 0.65) -> Optional[Dict[str, Any]]:
        """Search for semantically similar queries in cache, filtering by course."""
        try:
            print(f"CACHE SEARCH: query='{query[:50]}...', course='{course_category}/{course_name}'")
            
            retries = 3
            backoff_time = 1
            for i in range(retries):
                try:
                    query_embedding = await self.embeddings.aembed_query(query)
                    query_vector = np.array(query_embedding)
                    break
                except Exception as e:
                    if "504" in str(e) and i < retries - 1:
                        print(f"Embedding failed: {e}. Retrying in {backoff_time} seconds...")
                        time.sleep(backoff_time)
                        backoff_time *= 2  # Exponential backoff
                    else:
                        print(f"Embedding failed after {i + 1} attempts: {e}")
                        raise # Re-raise the exception if all retries fail
            
            print(f"Generated embedding vector of length: {len(query_vector)}")
            
            # Get all cached queries
            cached_keys = self.redis_client.keys("cache:*")
            print(f"Found {len(cached_keys)} cached entries to check")
            
            best_match = None
            best_similarity = 0.0
            
            for key in cached_keys:
                try:
                    cached_data_str = self.redis_client.get(key)
                    if not cached_data_str:
                        continue
                        
                    cached_data = json.loads(cached_data_str)
                    
                    # --- START: Course Filtering Logic ---
                    cached_meta = cached_data.get("metadata", {})
                    cached_course_cat = cached_meta.get("course_category")
                    cached_course_names = cached_meta.get("course_names", [])

                    # A cache entry is valid if:
                    # 1. The cache item has NO course info (it's a general query)
                    # 2. The cache item's course category matches the user's AND the user's course name is in the list
                    is_course_match = (
                        not cached_course_cat or
                        (cached_course_cat == course_category and course_name in cached_course_names)
                    )

                    if not is_course_match:
                        # print(f"Skipping cache item {key} due to course mismatch.")
                        continue
                    
                    cached_embedding = np.array(cached_data["embedding"])
                    
                    # Calculate cosine similarity
                    similarity = np.dot(query_vector, cached_embedding) / (
                        np.linalg.norm(query_vector) * np.linalg.norm(cached_embedding)
                    )
                    
                    print(f"Similarity with cached query '{cached_data.get('query', '')[:30]}...': {similarity:.3f}")
                    
                    if similarity > best_similarity and similarity >= threshold:
                        best_similarity = similarity
                        best_match = cached_data
                        print(f"New best match found with similarity: {similarity:.3f}")
                        
                except Exception as e:
                    print(f"Error processing cached item {key}: {str(e)}")
                    continue
            
            if best_match:
                print(f"CACHE HIT: Found cached response with similarity: {best_similarity:.3f}")
                return {
                    "response": best_match["response"],
                    "confidence": best_match.get("confidence", 0.9),
                    "similarity": best_similarity,
                    "original_query": best_match["query"]
                }
            else:
                print(f"CACHE MISS: No similar queries found above threshold {threshold}")
            
            return None
            
        except Exception as e:
            print(f"Semantic cache search error", e)
            return None
    
    async def store_response(
        self, 
        query: str, 
        response: str, 
        confidence: float,
        category: str,
        metadata: Dict[str, Any] = None
    ):
        """Store a query-response pair in semantic cache"""
        try:
            print(f"STORING IN CACHE: query='{query[:50]}...', confidence={confidence}")
            
            # Generate embedding for the query
            query_embedding = await self.embeddings.aembed_query(query)
            IST = ZoneInfo('Asia/Kolkata')
            # Create cache entry
            cache_data = {
                "query": query,
                "response": response,
                "confidence": confidence,
                "category": category,
                "embedding": query_embedding,
                "metadata": metadata or {},
                "timestamp": datetime.now(IST)
            }
            
            # Store in Redis with expiration (7 days)
            cache_key = f"cache:{hash(query)}"
            self.redis_client.set(
                cache_key,
                json.dumps(cache_data, default=str),
                {"ex": 604800} 
            )
            
            print(f"CACHED SUCCESSFULLY: key={cache_key}")
            
        except Exception as e:
            print(f"Error storing in cache",e)
    
    async def invalidate_category(self, category: str):
        """Invalidate cache entries for a specific category (useful when knowledge base is updated)"""
        try:
            print(f" INVALIDATING CACHE for category: {category}")
            cached_keys = self.redis_client.keys("cache:*")
            invalidated_count = 0
            
            for key in cached_keys:
                try:
                    cached_data_str = self.redis_client.get(key)
                    if not cached_data_str:
                        continue
                        
                    cached_data = json.loads(cached_data_str)
                    if cached_data.get("category") == category:
                        self.redis_client.delete(key)
                        invalidated_count += 1
                        
                except Exception as e:
                    print(f"Error invalidating cache item {key}: {str(e)}")
            
            print(f"INVALIDATED {invalidated_count} cache entries for category {category}")
                    
        except Exception as e:
            print(f"Error invalidating category cache: {str(e)}")
    
    def clear_all(self):
        """Clear all cache entries"""
        try:
            cached_keys = self.redis_client.keys("cache:*")
            if cached_keys:
                self.redis_client.delete(*cached_keys)
                print(f"CLEARED {len(cached_keys)} cache entries")
            else:
                print("No cache entries to clear")
        except Exception as e:
            print(f"Error clearing cache: {str(e)}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring"""
        try:
            cached_keys = self.redis_client.keys("cache:*")
            stats = {
                "total_entries": len(cached_keys),
                "categories": {},
                "oldest_entry": None,
                "newest_entry": None
            }
            
            timestamps = []
            for key in cached_keys:
                try:
                    cached_data_str = self.redis_client.get(key)
                    if not cached_data_str:
                        continue
                    
                    cached_data = json.loads(cached_data_str)
                    category = cached_data.get("category", "unknown")
                    timestamp = cached_data.get("timestamp", 0)
                    
                    stats["categories"][category] = stats["categories"].get(category, 0) + 1
                    timestamps.append(timestamp)
                    
                except Exception as e:
                    print(f"ror processing cache stats for {key}: {e}")
                    continue
            
            if timestamps:
                stats["oldest_entry"] = min(timestamps)
                stats["newest_entry"] = max(timestamps)
            
            return stats
            
        except Exception as e:
            print(f"ror getting cache stats: {e}")
            return {"error": str(e)}