# Utility functions for AOP workflow
import json
import os
import hashlib
import pickle
from typing import Any, Dict, List, Optional, Type
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

# Cache configuration
CACHE_ENABLED = os.environ.get("ENABLE_CACHE", "true").lower() == "true"
CACHE_DIR = os.environ.get("CACHE_DIR", "./cache")
os.makedirs(CACHE_DIR, exist_ok=True)

class WorkflowUtils:
    """Utility class for workflow operations"""
    
    @staticmethod
    def _get_cache_key(agent_name: str, prompt: str) -> str:
        """Generate a cache key from agent name and prompt"""
        combined = f"{agent_name}:{prompt}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    @staticmethod
    def _get_cache_path(cache_key: str) -> str:
        """Get the cache file path for a given cache key"""
        return os.path.join(CACHE_DIR, f"{cache_key}.pkl")
    
    @staticmethod
    def _load_from_cache(cache_key: str) -> Optional[Any]:
        """Load data from cache if available"""
        if not CACHE_ENABLED:
            return None
            
        cache_path = WorkflowUtils._get_cache_path(cache_key)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                return None
        return None
    
    @staticmethod
    def _save_to_cache(cache_key: str, data: Any) -> None:
        """Save data to cache"""
        if not CACHE_ENABLED:
            return
            
        cache_path = WorkflowUtils._get_cache_path(cache_key)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception:
            pass  # Silently fail on cache save errors
    
    @staticmethod
    def run_agent(agent_name: str, prompt: str, structured_output: Optional[Type[BaseModel]] = None) -> Any:
        """Alias for call_agent for backward compatibility"""
        return WorkflowUtils.call_agent(agent_name, prompt, structured_output)

    @staticmethod
    def invoke_agent(agent_name: str, prompt: str, structured_output: Optional[Type[BaseModel]] = None) -> Any:
        """Alias for call_agent for backward compatibility"""
        return WorkflowUtils.call_agent(agent_name, prompt, structured_output)
    
    @staticmethod
    def call_agent(agent_name: str, prompt: str, structured_output: Optional[Type[BaseModel]] = None) -> Any:
        """
        Call an agent directly using its instructions and the LLM.
        This function ensures all LLM calls go through agent instructions to prevent hallucination.
        """
        print(f"[AGENT CALL] Starting {agent_name} agent call...")
        print(f"[AGENT CALL] Prompt length: {len(prompt)} characters")
        
        # Check cache first
        cache_key = WorkflowUtils._get_cache_key(agent_name, prompt)
        cached_result = WorkflowUtils._load_from_cache(cache_key)
        if cached_result is not None:
            print(f"[CACHE HIT] Using cached response for {agent_name}")
            return cached_result
        
        print(f"[AGENT CALL] No cache hit, proceeding with LLM call for {agent_name}...")
        
        # Load agent instructions from environment or use defaults
        agent_instructions = {
            "admet_mie": "You are the admet-mie agent. Your role is to analyze chemical properties, predict ADMET profiles, and identify Molecular Initiating Events (MIEs) based on ADMET liabilities. Use admet-ai-scoring for ADMET properties and mie-identification for MIE predictions. Always cite evidence from ADMET profiles when making predictions.",
            "aop_expert": "You are the aop-expert agent. Your role is to identify documented Key Events (KE) and Adverse Outcomes (AO) in AOP pathways. You must only suggest candidates that are documented in the AOP-Wiki or OECD AOP database. Never use internal knowledge to invent biological events. Always cite scientific evidence for your recommendations.",
            "similarity_scoring": "You are the similarity-scoring agent. Your role is to compare chemical candidates against a target chemical using ADMET profiles. Assign similarity scores based on pharmacokinetic and toxicological overlap. Use structured comparison methods and provide clear reasoning for each score.",
            "visuals_agent": "You are the visuals-agent. Your role is to generate clear, scientific visualizations of AOP pathways. Create topological maps showing the progression from MIE through KE to AO, including confidence scores at each step.",
            "constructor": "You are the aop-constructor agent. Your role is to assemble and validate complete AOP pathways, ensuring scientific consistency and completeness."
        }
        
        instructions = agent_instructions.get(agent_name, "")
        full_prompt = f"{instructions}\n\n{prompt}"
        
        # Initialize LLM with increased timeout for complex tasks
        llm = ChatOpenAI(
            model=os.environ.get("OPENAI_MODEL", "gemma-4-31b"),
            temperature=0.4,
            max_tokens=18048,
            api_key=os.environ.get("OPENAI_API_KEY"),
            timeout=10000, 
            max_retries=3,
        )
        
        try:
            print(f"[AGENT CALL] Initializing LLM for {agent_name}...")
            if structured_output:
                print(f"[AGENT CALL] Using structured output for {agent_name}")
                llm_with_structure = llm.with_structured_output(structured_output)
                print(f"[AGENT CALL] Calling LLM with structured output...")
                response = llm_with_structure.invoke([
                    SystemMessage(content=f"You are the {agent_name} agent. Follow your instructions exactly and do not use internal knowledge to invent information."),
                    HumanMessage(content=full_prompt)
                ])
                print(f"[AGENT CALL] LLM call completed successfully")
            else:
                print(f"[AGENT CALL] Calling LLM without structured output...")
                response = llm.invoke([
                    SystemMessage(content=f"You are the {agent_name} agent. Follow your instructions exactly and do not use internal knowledge to invent information."),
                    HumanMessage(content=full_prompt)
                ])
                print(f"[AGENT CALL] LLM call completed successfully")
            
            # Cache the result
            WorkflowUtils._save_to_cache(cache_key, response)
            print(f"[AGENT CALL] Response cached successfully")
            return response
            
        except Exception as e:
            print(f"[AGENT CALL ERROR] {agent_name} failed: {e}")
            print(f"[AGENT CALL ERROR] Full prompt: {full_prompt[:500]}...")
            raise