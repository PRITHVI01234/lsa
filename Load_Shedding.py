import streamlit as st
from pyvis.network import Network
from itertools import combinations
import os
import time
import numpy as np
import random
from datetime import datetime

# Define the Node class
class Node:
    def __init__(self, real_power, priority):
        self.real_power = real_power
        self.priority = priority
        self.selected = False

# Function to generate all combinations of nodes and check if they meet the target power
def generate_combinations(nodes, target_real, tolerance):
    """
    Generates all combinations of nodes and checks if they meet the target real power within the tolerance.
    """
    best_combination = None
    best_power = None
    
    # Try all combinations of nodes (starting from one node, to two nodes, and so on)
    for r in range(1, len(nodes) + 1):
        for comb in combinations(nodes, r):
            total_power = sum(node.real_power for node in comb)
            if target_real - tolerance <= total_power <= target_real + tolerance:
                if best_power is None or abs(total_power - target_real) < abs(best_power - target_real):
                    best_combination = comb
                    best_power = total_power
    
    return best_combination, best_power

# Log function to log a single concise message with timestamp
def log_to_file(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {message}\n"
    
    with open("load_shedding_log.txt", "a") as log_file:
        log_file.write(log_entry)

# Main function to find the combination of nodes that meet the target real power
def find_combination(nodes_by_priority, target_real, tolerance):
    selected_nodes = set()
    found_valid_combination = False

    # Start from the lowest priority level (priority 5) and progressively combine nodes from higher levels
    for r in range(5, 0, -1):  # r = 5 -> check priority 5, r = 4 -> check priority 5 + 4, etc.
        # Collect nodes from the first r priority levels
        nodes_to_check = []
        for priority in range(5, 6 - r, -1):  # Collect nodes from priority 5 to priority r
            nodes_to_check.extend(nodes_by_priority[priority])

        # Step 1: Try all combinations of nodes from these priority levels
        best_combination, best_power = generate_combinations(nodes_to_check, target_real, tolerance)
        
        if best_combination:
            # If a valid combination is found, select those nodes and stop the search
            selected_nodes.update(best_combination)
            found_valid_combination = True
            break

    # Return the selected nodes and total power
    return selected_nodes, best_power, found_valid_combination

# Streamlit setup
st.set_page_config(page_title="Load Shedding Suggestions", page_icon="🔌", layout="wide")
st.title("Load Shedding Suggestions 🔋")
st.subheader("Find the optimal combination of loads to shed")

def clear_log():
    if os.path.exists("load_shedding_log.txt"):
        open("load_shedding_log.txt", "w").close()  # This clears the file content
        st.success("Log file cleared successfully! 🧹")
    else:
        st.warning("No log file found to clear. 🗑️")

# Sidebar for Log File Display
with st.sidebar:
    st.header("Load Shedding Log 📝:")
    st.divider()

    # Check if log file exists and display its contents with proper formatting
    if os.path.exists("load_shedding_log.txt"):
        with open("load_shedding_log.txt", "r") as log_file:
            log_contents = log_file.read()
        st.markdown("### Log File Contents:")
        # Render each timestamp (row) in a success or warning block based on the outcome
        for line in log_contents.strip().split("\n"):
          if " - " in line:  
            timestamp, message = line.split(" - ", 1)
            if "shed successfully" in message:
                st.success(f"{timestamp} - {message}",icon="✅")
            else:
                st.warning(f"{timestamp} - {message}",icon="❌")
    else:
        st.write("No log file found.")

    if st.button("Clear Logs 🗑️"):
        clear_log()  # Clear the log when clicked

# Create nodes with different priorities
nodes_by_priority = {
    1: [Node(10, 1), Node(20, 1), Node(30, 1)],
    2: [Node(15, 2), Node(25, 2), Node(35, 2)],
    3: [Node(40, 3), Node(50, 3)],
    4: [Node(60, 4), Node(70, 4), Node(80, 4)],
    5: [Node(90, 5), Node(100, 5), Node(110, 5)]
}

# Input fields for target power and tolerance
gr = st.container(border=True)
c1,c2 = gr.columns([1,3])

with c1:
    measure = "**Real Power (kW)**"
    qun = "Kw"
    go = st.container(border=True)
    measure = go.radio("Power Type",
                       ["**Real Power (kW)**","**Reactive Power (KVAR)**"],
                       index=None, help="Select the type of power to optimize for")
    if measure == "**Real Power (kW)**":
        qun = "kw"
    elif measure == "**Reactive Power (KVAR)**":
        qun = "kvar"
        
with c2:
    first = st.container(border=True)

col1, col2 = first.columns(2)
with col1:
    if not measure:
        measure = "**Real Power (kW)**"

    target_real = st.number_input(f"Target {measure}", min_value=0, value=200, step=10, help="Enter the target power value")
with col2:
    tolerance = st.number_input("Tolerance", min_value=0, value=20, step=10, help="Enter the tolerance value")

# Function to plot the network
def plot_network(nodes_by_priority, selected_nodes=None):
    if selected_nodes is None:
        selected_nodes = set()  # Ensure selected_nodes is an empty set if None is passed

    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black", notebook=True)
    
    # Create nodes and edges for the pyvis network
    node_id = 0
    node_map = {}  # Mapping from Node object to pyvis node ID
    
    # Add nodes for each priority
    for priority in range(1, 6):
        for node in nodes_by_priority[priority]:
            node_map[node] = node_id
            node_color = 'red' if node in selected_nodes else '#87CEEB'  # Highlight selected nodes in red
            net.add_node(node_id, label=f'Node {node_id+1}\nRating: {node.real_power} {qun}\nPriority: {node.priority}',
                         title=f'Real Power: {node.real_power} kW\nPriority: {node.priority}', color=node_color)
            node_id += 1
    
    # Connect nodes based on priority (this is just an example, adjust as necessary)
    for priority in range(1, 5):
        for node in nodes_by_priority[priority]:
            for child in nodes_by_priority[priority + 1]:
                net.add_edge(node_map[node], node_map[child], color='#DCDCDC')  # Add edges between priorities
    
    net.set_options(""" 
    var options = {
      "physics": {
        "enabled": false
      },
      "nodes": {
        "shape": "dot",
        "size": 20,
        "font": {
          "size": 14
        }
      }
    }
    """)
    
    return net

# Display the network by default
net = plot_network(nodes_by_priority)

with st.expander(label="Default Layout", expanded=False):
    st.header("Default Network Graph:")
    st.components.v1.html(net.generate_html(), height=600)

# Run button to trigger load shedding algorithm
if st.button("Run Load Shedding 🚀"):
    with st.spinner(text="Computing...."):
        time.sleep(np.random.randint(3,7))
    st.toast("Sucess",icon="✅")
    # Find the combination of nodes
    selected_nodes, selected_power, found_valid_combination = find_combination(nodes_by_priority, target_real, tolerance)

    # Update the network with the selected nodes
    net = plot_network(nodes_by_priority, selected_nodes)
    # Show the updated network
    with st.container(border=True):
        st.header("Updated Network Graph:")
        st.components.v1.html(net.generate_html(), height=600)

        if selected_nodes:
            st.success(f"Selected nodes with total {measure}: {selected_power:.2f} {qun}", icon="💡")
            for node in selected_nodes:
                st.info(f"Node Rating: {node.real_power} {qun} - Priority Level: {node.priority}", icon="⚠")
            
            # Log the result message
            log_message = f"User requested to shed {target_real} {qun} with tolerance {tolerance} {qun}. {selected_power} {qun} was shed successfully."
            log_to_file(log_message)
        else:
            st.warning("No valid combination found within the tolerance. 🤔")
            
            # Log the failure message
            log_message = f"User requested to shed {target_real} {qun} with tolerance {tolerance} kW. No valid combination found."
            log_to_file(log_message)
