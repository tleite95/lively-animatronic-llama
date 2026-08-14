from __future__ import annotations

from state import QSARState, make_initial_state

from langgraph.graph import StateGraph, START, END

import nodes
import routers

def build_graph():
    builder = StateGraph(QSARState)
    builder.add_node("init", nodes.init)
    builder.add_node("retrieve-evidence", nodes.init)
    builder.add_node("harmonize-evidence", nodes.init)
    builder.add_node("search-endpoints", nodes.init)
    builder.add_node("generate-descriptors", nodes.init)
    builder.add_node("qsar-predict", nodes.init)
    builder.add_node("search-analogs", nodes.init)
    builder.add_node("analyze-analogs", nodes.init)
    builder.add_node("quality-assessment", nodes.init)
    builder.add_node("woe-synthesis", nodes.init)

   
    builder.add_edge(START, "init")
    builder.add_edge("woe-table", END)

    return builder.compile()

if __name__ == "__main__":
    app = build_graph()
    final_report = app.invoke(make_initial_state("./config.yaml"))["final-report"]
    print(final_report)
