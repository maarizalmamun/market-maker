import os
import json
import matplotlib.pyplot as plt
from matplotlib.dates import AutoDateLocator, AutoDateFormatter
from datetime import datetime

def generate_graph():
    """Generate a graph showing the total collateral and unrealized PnL over time."""

    curr_dir = os.path.dirname(os.path.abspath(__file__))
    archive_dir = os.path.join(curr_dir, '../data/archived/user/')
    data_dir = os.path.join(curr_dir, '../data/')

    # Initialize arrays for storing values
    total_collateral_values = []
    free_collateral_values = []
    unrealized_pnl_values = []
    time_values = []

    # Get list of JSON files in the directory
    file_list = os.listdir(archive_dir)

    # Sort the file list by file name 
    file_list.sort()

    # Process each JSON file
    for file_name in file_list:
        if file_name.endswith('.json'):
            file_path = os.path.join(archive_dir, file_name)
            with open(file_path, 'r') as file:
                # Load JSON data
                data = json.load(file)

                # Extract values from JSON
                total_collateral = data['total_collateral']
                free_collateral = data['free_collateral']
                unrealized_pnl = data['unrealized_pnl']

                # Get timestamp from the file name
                timestamp_date = file_name.split('-')[1].replace(':', '')
                timestamp_time = file_name.split('-')[2].replace(':', '').split('.')[0]
                timestamp_str = timestamp_date + '-' + timestamp_time
                timestamp = datetime.strptime(timestamp_str, '%y%m%d-%H%M')
                # Append values to the respective arrays
                total_collateral_values.append(total_collateral)
                free_collateral_values.append(free_collateral)
                unrealized_pnl_values.append(unrealized_pnl)
                time_values.append(timestamp)

    # Add earliest total_collateral value to unrealized_pnl_values
    earliest_total_collateral = total_collateral_values[0]
    unrealized_pnl_values = [pnl + earliest_total_collateral for pnl in unrealized_pnl_values]
    plt.figure(figsize=(12, 6))

    plt.switch_backend('agg')

    # Generate the graph
    plt.clf()  # Clear the current plot

    plt.plot(time_values, total_collateral_values, label='Total Collateral')
    plt.plot(time_values, unrealized_pnl_values, label='Unrealized PnL')
    plt.xlabel('Time (MM DD hh:mm)')  # Update the x-label format
    plt.ylabel('USDC Value')
    plt.title('Collateral and Unrealized PnL Over Time')
    plt.legend()

    # Set the x-axis date formatter
    locator = AutoDateLocator()
    formatter = AutoDateFormatter(locator)
    formatter.scaled[1 / (24.0 * 60.)] = '%b %d %H:%M'  # Set the desired date format
    plt.gca().xaxis.set_major_locator(locator)
    plt.gca().xaxis.set_major_formatter(formatter)
    plt.margins(x=0.02)
    plt.tight_layout()
    plt.savefig(data_dir + 'trading_result_graph.png')