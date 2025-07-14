#!/usr/bin/env python3
"""
Test script to verify the improvements work correctly.
Tests LLM manager, monitoring system, and enhanced tools.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

load_dotenv()

def test_llm_manager():
    """Test the LLM manager functionality."""
    print("🧪 Testing LLM Manager...")
    
    try:
        from llm_manager import llm_manager
        
        # Test available providers
        providers = llm_manager.get_available_providers()
        print(f"✅ Available providers: {providers}")
        
        # Test getting LLM instance
        if providers:
            llm = llm_manager.get_llm()
            print(f"✅ Successfully got LLM instance: {type(llm).__name__}")
            
            # Test simple invocation
            test_prompt = "Hello, this is a test. Please respond with 'Test successful'."
            result = llm_manager.invoke_with_fallback(test_prompt)
            
            if result["success"]:
                print(f"✅ LLM invocation successful using {result['provider']}")
                print(f"   Response: {result['response']}")
            else:
                print(f"❌ LLM invocation failed: {result.get('error', 'Unknown error')}")
        else:
            print("⚠️  No LLM providers available. Make sure GOOGLE_API_KEY is set.")
            
    except Exception as e:
        print(f"❌ LLM Manager test failed: {e}")

def test_monitoring():
    """Test the monitoring system."""
    print("\n🧪 Testing Monitoring System...")
    
    try:
        from monitoring import monitoring
        
        # Test task monitoring
        task_id = monitoring.start_task("test_task", "Test task description")
        print(f"✅ Started task: {task_id}")
        
        # Test agent monitoring
        agent_id = monitoring.start_agent(task_id, "test_agent")
        print(f"✅ Started agent: {agent_id}")
        
        # Test ending agent
        monitoring.end_agent(agent_id, success=True, provider_used="gemini")
        print("✅ Ended agent successfully")
        
        # Test ending task
        monitoring.end_task(task_id, success=True)
        print("✅ Ended task successfully")
        
        # Test getting stats
        stats = monitoring.get_system_stats()
        print(f"✅ System stats: {stats}")
        
    except Exception as e:
        print(f"❌ Monitoring test failed: {e}")

def test_enhanced_scraper():
    """Test the enhanced web scraper."""
    print("\n🧪 Testing Enhanced Web Scraper...")
    
    try:
        from tools.enhanced_scraper import scrape_website_enhanced
        
        # Test with a simple website
        test_url = "https://httpbin.org/html"
        result = scrape_website_enhanced(test_url)
        
        if "error" not in result:
            print(f"✅ Enhanced scraper successful")
            print(f"   Content length: {result.get('content_length', 0)}")
            print(f"   Status: {result.get('status', 'unknown')}")
        else:
            print(f"❌ Enhanced scraper failed: {result['error']}")
            
    except Exception as e:
        print(f"❌ Enhanced scraper test failed: {e}")

def test_vector_store():
    """Test the vector store functionality."""
    print("\n🧪 Testing Vector Store...")
    
    try:
        from vector_store import VectorStore
        
        vector_store = VectorStore()
        print("✅ Vector store initialized")
        
        # Test adding documents
        test_docs = ["This is a test document about AI.", "Another test document about machine learning."]
        vector_store.add_documents("test_index", test_docs)
        print("✅ Documents added successfully")
        
        # Test search
        results = vector_store.search("test_index", "AI")
        print(f"✅ Search successful, found {len(results)} results")
        
    except Exception as e:
        print(f"❌ Vector store test failed: {e}")

async def main():
    """Run all tests."""
    print("🚀 Starting Improvement Tests...\n")
    
    # Test LLM Manager
    test_llm_manager()
    
    # Test Monitoring
    test_monitoring()
    
    # Test Enhanced Scraper
    test_enhanced_scraper()
    
    # Test Vector Store
    test_vector_store()
    
    print("\n✨ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 