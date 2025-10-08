"""
StateGraph construction for the multi-agent itinerary planner.
Defines the flow between nodes and conditional routing logic.
"""

import logging
from typing import Literal
from langgraph.graph import StateGraph, END

from core.state import GraphState
from core.router import router_node
from core.destination_planner import preplanner_agent_node
from agents.planner import planner_node
from agents.planner_execution import planner_execution_node
from agents.reasoning import reasoning_node
from agents.flight_agent import flight_agent_node
from agents.hotel_agent import hotel_agent_node
from agents.activity_agent import activity_agent_node
from agents.itinerary_agent import itinerary_agent_node

logger = logging.getLogger(__name__)


def route_after_router(state: GraphState) -> Literal["destination_planner", "planner", "flight", "hotel", "activity", "itinerary", "reasoning", "end"]:
    """
    Conditional routing based on router's decision.
    
    Args:
        state: Current graph state
    
    Returns:
        Next node name
    """
    next_agent = state.get("next_agent", "").upper()
    
    route_map = {
        "DESTINATION_PLANNER": "destination_planner",
        "PLANNER": "planner",
        "FLIGHT": "flight",
        "HOTEL": "hotel",
        "ACTIVITY": "activity",
        "ITINERARY": "itinerary",
        "REASONING": "reasoning",
        "END": "end"
    }
    
    route = route_map.get(next_agent, "end")
    logger.info(f"Router decision: {next_agent} -> routing to '{route}'")
    return route


def route_after_destination_planner(state: GraphState) -> Literal["router", "end"]:
    """
    After destination planner provides recommendations, route based on selection.
    
    Args:
        state: Current graph state
    
    Returns:
        Next node name
    """
    metadata = state.get("metadata", {})
    
    # If destination has been selected, continue to router (which will route to planner)
    if metadata.get("destination_selected", False):
        logger.info("Destination selected, routing to router")
        return "router"
    else:
        # Wait for user to select from recommendations
        logger.info("Waiting for destination selection, ending graph")
        return "end"


def route_after_planner(state: GraphState) -> Literal["planner_execution", "reasoning"]:
    """
    After planner generates a plan, route to execution or reasoning.
    
    Args:
        state: Current graph state
    
    Returns:
        Next node name
    """
    # Check if plan exists and needs execution
    plan = state.get("plan")
    if plan and plan.get("steps"):
        logger.info("Plan generated, routing to execution")
        return "planner_execution"
    else:
        logger.info("No executable plan, routing to reasoning")
        return "reasoning"


def route_after_execution(state: GraphState) -> Literal["reasoning", "end"]:
    """
    After execution, route to reasoning for validation.
    
    Args:
        state: Current graph state
    
    Returns:
        Next node name
    """
    logger.info("Execution complete, routing to reasoning for validation")
    return "reasoning"


def route_after_specialized_agent(state: GraphState) -> Literal["reasoning", "end"]:
    """
    After a specialized agent runs, route to reasoning.
    
    Args:
        state: Current graph state
    
    Returns:
        Next node name
    """
    logger.info("Specialized agent complete, routing to reasoning")
    return "reasoning"


def route_after_reasoning(state: GraphState) -> Literal["router", "end"]:
    """
    After reasoning, decide if more processing needed or end.
    
    Args:
        state: Current graph state
    
    Returns:
        Next node name
    """
    # Check if reasoning suggests more actions
    next_agent = state.get("next_agent", "").upper()
    
    if next_agent and next_agent != "END":
        logger.info(f"Reasoning suggests more work: {next_agent}, routing to router")
        return "router"
    else:
        logger.info("Reasoning complete, ending graph")
        return "end"


def build_graph():
    """
    Build and compile the state graph for the itinerary planner.
    
    Returns:
        Compiled StateGraph ready for invocation
    """
    logger.info("Building state graph...")
    
    # Initialize graph
    graph = StateGraph(GraphState)
    
    # Add nodes
    graph.add_node("router", router_node)
    graph.add_node("destination_planner", preplanner_agent_node)
    graph.add_node("planner", planner_node)
    graph.add_node("planner_execution", planner_execution_node)
    graph.add_node("reasoning", reasoning_node)
    graph.add_node("flight", flight_agent_node)
    graph.add_node("hotel", hotel_agent_node)
    graph.add_node("activity", activity_agent_node)
    graph.add_node("itinerary", itinerary_agent_node)
    
    # Set entry point
    graph.set_entry_point("router")
    
    # Add conditional edges from router
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {
            "destination_planner": "destination_planner",
            "planner": "planner",
            "flight": "flight",
            "hotel": "hotel",
            "activity": "activity",
            "itinerary": "itinerary",
            "reasoning": "reasoning",
            "end": END
        }
    )
    
    # Add conditional edges from destination_planner
    graph.add_conditional_edges(
        "destination_planner",
        route_after_destination_planner,
        {
            "router": "router",
            "end": END
        }
    )
    
    # Add conditional edges from planner
    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "planner_execution": "planner_execution",
            "reasoning": "reasoning"
        }
    )
    
    # Add conditional edges from planner execution
    graph.add_conditional_edges(
        "planner_execution",
        route_after_execution,
        {
            "reasoning": "reasoning",
            "end": END
        }
    )
    
    # Add conditional edges from specialized agents
    for agent in ["flight", "hotel", "activity", "itinerary"]:
        graph.add_conditional_edges(
            agent,
            route_after_specialized_agent,
            {
                "reasoning": "reasoning",
                "end": END
            }
        )
    
    # Add conditional edges from reasoning
    graph.add_conditional_edges(
        "reasoning",
        route_after_reasoning,
        {
            "router": "router",
            "end": END
        }
    )
    
    # Compile graph
    compiled_graph = graph.compile()
    
    logger.info("State graph built and compiled successfully")
    return compiled_graph