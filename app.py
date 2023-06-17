# Python standard library
import os
import pickle
from collections import OrderedDict

# Additional dependencies
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Data paths
DATA_DIR = r"data"
DATA_PATH = os.path.join(DATA_DIR, r"processed_data.pkl")


@st.cache_data
def get_df() -> pd.DataFrame:
    """Reads a pandas.DataFrame of pre-processed data from a .pkl file and returns it for use in the streamlit app.

    Returns:
        pd.DataFrame: A DataFrame containing the pre-processed movement and event records as output by data_processing.py
    """
    with open(DATA_PATH, "rb") as file:
        return pickle.load(file)


def get_event_rate_plots(df: pd.DataFrame, city: str = "All Cities") -> None:
    """This function takes in the DataFrame containing the movement and event data, as well as an optional city name.
    It then generates two plots breaking down the event rates by months of 2022.

    - The first plot is a line graph with months on the x-axis and event rates per 1,000 movements on the y-axis. Each event type is plotted as a seperate line.
    - The second plot is a series of box plots, one for each event type along the x-axis, with the event rates on the y-axis.

    Args:
        df (pd.DataFrame): The DataFrame containing the calculated event rates for each event type, city, and month of 2022.
        city (str, optional): The city name to filter the data by. Defaults to 'All Cities'.
    """

    # Filter to the specified location
    df = df[df.Location == city]

    # Limit the number of event types displayed by default to a max of 7
    # Filter to the 5 highest event rate event types, plus LOS and Runway Incursion if they are present
    always_show = ["Loss of Separation", "Runway Incursion"]
    all_types = list(df.sort_values("event_rate", ascending=False).Event_Type)
    all_types = list(OrderedDict.fromkeys(all_types))

    to_show = [x for x in all_types if x not in always_show][:5]
    to_show = [x for x in always_show if x in all_types] + to_show

    all_types = sorted([x for x in all_types if x not in always_show])
    all_types = (
        always_show + all_types
    )  # Legend order is LOS, Runway Incursion, all others sorted alphabetically

    # Plot the event rates by month and type as a line plot
    layout = go.Layout(
        xaxis_title="Month",
        yaxis_title="Event rate (per 1,000 movements)",
        legend_title="Event Type",
        title=f"2022 {city} Event Rates by Month and Type",
        yaxis_range=[0, 3],
    )
    fig_line = go.Figure(layout=layout)

    for e_type in all_types:
        this_df = df[df.Event_Type == e_type]
        fig_line.add_trace(
            go.Line(
                x=this_df.month,
                y=this_df.event_rate,
                visible="legendonly" if e_type not in to_show else None,
                name=e_type,
            )
        )

    # Plot the monthly event rate distributions as type box plots
    layout = go.Layout(
        xaxis_title="Event Type",
        yaxis_title="Event rate (per 1,000 movements)",
        legend_title="Event Type",
        title=f"2022 {city} Event Rate Box Plots by Type",
        yaxis_range=[0, 3],
    )
    fig_box = go.Figure(layout=layout)

    for e_type in all_types:
        this_df = df[df.Event_Type == e_type]
        fig_box.add_trace(
            go.Box(
                y=this_df.event_rate,
                visible="legendonly" if e_type not in to_show else None,
                name=e_type,
            )
        )

    return fig_line, fig_box


def main():
    """Main function for defining the streamlit web app"""

    st.set_page_config(layout="wide", page_title="M.Trotter - Analysis")

    # Fake data warning
    st.markdown(
        "<h1 style='text-align: center; color:#8B0000; font-family:Monospace; font-size: 25px;'>// All data shown here is for analysis demonstration purposes only //</h1>",
        unsafe_allow_html=True,
    )

    # Title
    title_container = st.container()
    with title_container:
        
        name = '<p style="color:white; font-family:Monospace; font-size: 30px; margin-top: auto;">Michael Trotter</p>'
        title = "Safety Data Analysis Exercise - Senior Safety Data Analyst application, June 2023"
        title = f'<p style="color:white; font-family:Monospace; font-size: 20px; margin-top: auto;">{title}</p>'
        st.markdown(name, unsafe_allow_html=True)
        st.markdown(title, unsafe_allow_html=True)

    # City selection dropdown
    city_selction = st.selectbox(
        "Which locations would you like to display?",
        ("All Cities", "Blue City", "Green City", "Red City", "Yellow City"),
    )

    # Data read from a pre-processed pickle file
    df = get_df()

    # Tabs for each plot type
    tab1, tab2 = st.tabs(["Month - Event Type Line Plots", "Event Type Box Plots"])
    fig_line, fig_box = get_event_rate_plots(df, city_selction)

    display_note = "Note - 'Loss of Seperation' and 'Runway Incursion' events are displayed by default, along with the five types with highest event rate values. Others can be enabled by clicking on the legend."

    with tab1:
        st.write(display_note)

        # Line plots
        fig_line.update_layout(height=600, width=1200)
        st.plotly_chart(fig_line)

    with tab2:
        st.write(display_note)

        # Box plots
        fig_box.update_layout(height=600, width=1200)
        st.plotly_chart(fig_box)


if __name__ == "__main__":
    main()
