"""
LangGraph-based data analysis agent for e-commerce insights.
"""

import logging
import pandas as pd
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from agent.state import AnalysisState, AnalysisType, determine_analysis_type
from agent.prompts import enhance_insight_with_llm
from config import create_bigquery_client, setup_gemini

logger = logging.getLogger(__name__)

class LangGraphAnalysisAgent:
    """LangGraph-based agent for e-commerce data analysis using graph workflows."""

    def __init__(self):
        """Initialize the analysis agent with LangGraph workflow."""
        self.bq_client = create_bigquery_client()
        self.llm_client = setup_gemini()
        self.enable_llm_insights = self.llm_client is not None

        # Test LLM client if available
        if self.enable_llm_insights and self.llm_client:
            try:
                # Quick test to see if API key is valid
                test_response = self.llm_client.invoke("Hello")
                if test_response:
                    logging.debug("LLM client test successful")
                else:
                    logging.warning("LLM client returned empty response, disabling LLM features")
                    self.enable_llm_insights = False
            except Exception as e:
                logging.warning(f"LLM client test failed: {e}. Disabling LLM features.")
                self.enable_llm_insights = False

        # Import here to avoid circular imports
        from tools.query_builder import QueryBuilder
        from tools.analyzers import CustomerAnalyzer, ProductAnalyzer, SalesAnalyzer, GeographicAnalyzer

        self.query_builder = QueryBuilder(self.bq_client)
        self.customer_analyzer = CustomerAnalyzer()
        self.product_analyzer = ProductAnalyzer()
        self.sales_analyzer = SalesAnalyzer()
        self.geographic_analyzer = GeographicAnalyzer()

        # Build the LangGraph workflow
        self.graph = self._create_analysis_graph()

    def analyze(self, user_input: str) -> AnalysisState:
        """Execute the LangGraph workflow for data analysis."""

        # Create initial state with LangGraph message
        import uuid
        initial_state = AnalysisState(
            messages=[HumanMessage(content=user_input)],
            session_id=str(uuid.uuid4()),
            current_analysis=None,
            analysis_context=None,
            current_query=None,
            query_history=[],
            insights=[],
            raw_dataframes={},
            errors=[],
            last_error=None,
            created_at=pd.Timestamp.now().isoformat(),
            max_insights=10,
            enable_llm_insights=self.enable_llm_insights
        )

        # Execute the LangGraph workflow
        try:
            final_state = self.graph.invoke(initial_state)
            return final_state
        except Exception as e:
            logger.error(f"LangGraph workflow failed: {e}")
            # Return state with error
            error_state = initial_state.copy()
            error_state["errors"] = [str(e)]
            error_state["last_error"] = str(e)
            return error_state

    def _create_analysis_graph(self) -> StateGraph:
        """Create the LangGraph workflow for data analysis."""

        # Create the workflow graph
        workflow = StateGraph(AnalysisState)

        # Add nodes for each step of the workflow
        workflow.add_node("classify_query", self._classify_query_node)
        workflow.add_node("build_query", self._build_query_node)
        workflow.add_node("execute_query", self._execute_query_node)
        workflow.add_node("analyze_data", self._analyze_data_node)
        workflow.add_node("enhance_insights", self._enhance_insights_node)

        # Define the workflow flow
        workflow.set_entry_point("classify_query")
        workflow.add_edge("classify_query", "build_query")
        workflow.add_edge("build_query", "execute_query")
        workflow.add_edge("execute_query", "analyze_data")
        workflow.add_edge("analyze_data", "enhance_insights")
        workflow.add_edge("enhance_insights", END)

        return workflow.compile()

    def _classify_query_node(self, state: AnalysisState) -> AnalysisState:
        """Node 1: Classify the user query to determine analysis type."""
        try:
            user_input = state["messages"][-1].content if state["messages"] else ""
            analysis_type = determine_analysis_type(user_input)

            # Update state with classification results
            new_state = state.copy()
            new_state["current_analysis"] = analysis_type
            new_state["messages"] = state["messages"] + [AIMessage(content=f"Analysis type determined: {analysis_type.value}")]

            logger.info(f"Query classified as: {analysis_type}")
            return new_state

        except Exception as e:
            logger.error(f"Query classification failed: {e}")
            error_state = state.copy()
            error_state["errors"] = state.get("errors", []) + [f"Classification error: {str(e)}"]
            error_state["last_error"] = str(e)
            return error_state

    def _build_query_node(self, state: AnalysisState) -> AnalysisState:
        """Node 2: Build the appropriate SQL query based on analysis type."""
        try:
            analysis_type = state["current_analysis"]
            if not analysis_type:
                raise ValueError("No analysis type determined")

            # Create analysis context
            from agent.state import AnalysisContext
            context = AnalysisContext(
                analysis_type=analysis_type,
                parameters={}
            )

            # Build query using existing query builder
            query = self.query_builder.build_query(analysis_type, context)

            # Update state with query information
            new_state = state.copy()
            new_state["current_query"] = type('QueryResult', (), {
                'query': query,
                'dataframe': None,
                'execution_time': 0,
                'row_count': 0
            })()
            new_state["messages"] = state["messages"] + [AIMessage(content=f"Query built for {analysis_type.value}")]

            logger.info(f"Query built for analysis type: {analysis_type}")
            return new_state

        except Exception as e:
            logger.error(f"Query building failed: {e}")
            error_state = state.copy()
            error_state["errors"] = state.get("errors", []) + [f"Query building error: {str(e)}"]
            error_state["last_error"] = str(e)
            return error_state

    def _execute_query_node(self, state: AnalysisState) -> AnalysisState:
        """Node 3: Execute the SQL query against BigQuery."""
        try:
            current_query = state.get("current_query")
            if not current_query or not current_query.query:
                raise ValueError("No query to execute")

            import time
            start_time = time.time()

            # Execute query using existing BigQuery client
            df = self.bq_client.execute_query(current_query.query)

            execution_time = time.time() - start_time

            # Update state with query results
            new_state = state.copy()
            new_state["current_query"] = type('QueryResult', (), {
                'query': current_query.query,
                'dataframe': df,
                'execution_time': execution_time,
                'row_count': len(df) if df is not None else 0
            })()
            new_state["query_history"] = state.get("query_history", []) + [new_state["current_query"]]

            if df is not None and not df.empty:
                new_state["raw_dataframes"] = {"query_result": df}

            new_state["messages"] = state["messages"] + [AIMessage(content=f"Query executed, returned {len(df) if df is not None else 0} rows")]

            logger.info(f"Query executed successfully, returned {len(df) if df is not None else 0} rows")
            return new_state

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            error_state = state.copy()
            error_state["errors"] = state.get("errors", []) + [f"Query execution error: {str(e)}"]
            error_state["last_error"] = str(e)
            return error_state

    def _analyze_data_node(self, state: AnalysisState) -> AnalysisState:
        """Node 4: Analyze the query results using appropriate analyzer."""
        try:
            analysis_type = state["current_analysis"]
            current_query = state.get("current_query")

            if not analysis_type:
                raise ValueError("No analysis type determined")

            if not current_query or current_query.dataframe is None or current_query.dataframe.empty:
                logger.warning("No data to analyze")
                new_state = state.copy()
                new_state["messages"] = state["messages"] + [AIMessage(content="No data available for analysis")]
                return new_state

            df = current_query.dataframe

            # Analyze results using existing analyzers
            if analysis_type == AnalysisType.CUSTOMER_SEGMENTATION:
                result = self.customer_analyzer.analyze_segmentation(df)
            elif analysis_type == AnalysisType.PRODUCT_PERFORMANCE:
                result = self.product_analyzer.analyze_performance(df)
            elif analysis_type == AnalysisType.SALES_TRENDS:
                result = self.sales_analyzer.analyze_trends(df)
            elif analysis_type == AnalysisType.GEOGRAPHIC_PATTERNS:
                result = self.geographic_analyzer.analyze_patterns(df)
            else:
                result = type('Result', (), {'insights': [], 'summary_stats': {}})()

            # Update state with analysis results
            new_state = state.copy()
            new_state["insights"] = result.insights
            new_state["messages"] = state["messages"] + [AIMessage(content=f"Generated {len(result.insights)} insights")]

            logger.info(f"Data analysis completed, generated {len(result.insights)} insights")
            return new_state

        except Exception as e:
            logger.error(f"Data analysis failed: {e}")
            error_state = state.copy()
            error_state["errors"] = state.get("errors", []) + [f"Analysis error: {str(e)}"]
            error_state["last_error"] = str(e)
            return error_state

    def _enhance_insights_node(self, state: AnalysisState) -> AnalysisState:
        """Node 5: Enhance insights with LLM if available."""
        try:
            insights = state.get("insights", [])
            analysis_type = state.get("current_analysis")

            if not insights or not analysis_type:
                logger.info("No insights to enhance or no analysis type")
                return state

            # Check if LLM is available
            if not self.enable_llm_insights or not self.llm_client:
                logger.info("LLM enhancement not available, returning original insights")
                return state

            # Enhance insights with LLM using async parallel processing
            logger.info(f"Starting async AI enhancement for {len(insights)} insights...")
            async def enhance_insights_async():
                async def enhance_single_insight(insight):
                    try:
                        # Run LLM enhancement in thread pool to avoid blocking
                        loop = asyncio.get_event_loop()
                        enhanced_content = await loop.run_in_executor(
                            None,
                            enhance_insight_with_llm,
                            self.llm_client,
                            insight.content,
                            analysis_type.value
                        )
                        return type('Insight', (), {
                            'content': enhanced_content,
                            'confidence': insight.confidence,
                            'data_source': insight.data_source,
                            'analysis_type': insight.analysis_type,
                            'supporting_data': insight.supporting_data
                        })()
                    except Exception as e:
                        logger.warning(f"LLM enhancement failed for insight: {e}")
                        return insight  # Keep original if enhancement fails

                # Create tasks for all insights
                tasks = [enhance_single_insight(insight) for insight in insights]

                # Run all enhancements concurrently
                enhanced_insights = await asyncio.gather(*tasks, return_exceptions=True)

                # Handle any exceptions that occurred
                final_insights = []
                for i, result in enumerate(enhanced_insights):
                    if isinstance(result, Exception):
                        logger.warning(f"LLM enhancement failed for insight {i}: {result}")
                        final_insights.append(insights[i])  # Keep original if enhancement failed
                    else:
                        final_insights.append(result)

                return final_insights

            # Run the async enhancement
            enhanced_insights = asyncio.run(enhance_insights_async())
            logger.info(f"Async AI enhancement completed for {len(enhanced_insights)} insights")

            # Update state with enhanced insights
            new_state = state.copy()
            new_state["insights"] = enhanced_insights
            new_state["messages"] = state["messages"] + [AIMessage(content=f"Enhanced {len(enhanced_insights)} insights with AI")]

            return new_state

        except Exception as e:
            logger.error(f"Insight enhancement failed: {e}")
            # Return original state if enhancement fails
            return state

    def get_insights_text(self, state: AnalysisState) -> str:
        """Get formatted insights text."""
        insights = state.get("insights", [])
        if not insights:
            return "No insights generated."

        return "\n\n".join([
            f"{i+1}. {insight.content}"
            for i, insight in enumerate(insights)
        ])

# Convenience function
def create_analysis_agent():
    """Create a new LangGraph-based analysis agent."""
    return LangGraphAnalysisAgent()