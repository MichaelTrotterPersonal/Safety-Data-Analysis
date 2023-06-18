# Python standard library
import os
import pickle
from collections import OrderedDict

# Additional dependencies
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
import seaborn as sns

# Data paths
DATA_DIR = r"data"
PROCESSED_DATA_PATH = os.path.join(DATA_DIR, r"processed_data.pkl")
SELECTED_DATA_PATH = os.path.join(DATA_DIR, r"selected_data.pkl")
FIXED_Y_AXIS_RANGE = [0, 3.7]

# When set to True, .png plots and .csv tables from the discussion section will be written out to files.
WRITE_PLOTS = False


@st.cache_data
def get_df(filename: str) -> pd.DataFrame:
    """Reads a pandas.DataFrame of pre-processed data from a .pkl file and returns it for use in the streamlit app.

    Returns:
        pd.DataFrame: A DataFrame containing the pre-processed movement and event records as output by data_processing.py
    """
    with open(filename, "rb") as file:
        return pickle.load(file)


def get_plot_orders(df: pd.DataFrame) -> tuple:
    """Returns two lists defining the order of events to plot and the top ~8 events to make visible.

    Args:
        df (pd.DataFrame): the processed data DataFrame with merged event and movement data.

    Returns:
        tuple: (list,list) containing the order of event types to add to the plot, and the ones to have visible.
    """

    # Limit the number of event types displayed by default to a max of 7
    # Filter to the 5 highest event rate event types, plus All Types, LOS and Runway Incursion
    always_show = ["All Types", "Loss of Separation", "Runway Incursion"]
    all_types = list(df.sort_values("event_rate", ascending=False).Event_Type)
    all_types = list(OrderedDict.fromkeys(all_types))

    to_show = [x for x in all_types if x not in always_show][:5]
    to_show = [x for x in always_show if x in all_types] + to_show

    all_types = sorted([x for x in all_types if x not in always_show])
    all_types = (
        always_show + all_types
    )  # Legend order is LOS, Runway Incursion, all others sorted alphabetically

    return all_types, to_show


def get_event_rate_line_plot(
    df: pd.DataFrame, city: str = "All Cities", colour_map: dict = None
) -> go.Figure:
    """This function takes in the DataFrame containing the movement and event data and generates the event type line plots.

    Args:
        df (pd.DataFrame): the processed data DataFrame with merged event and movement data.
        city (str, optional): the city to optionally filter to. Defaults to "All Cities".
        colour_map (dict, optional): a set colour map to specify event type colours. Defaults to None.

    Returns:
        go.Figure: A plotly graph object figure with the line plots.
    """

    # Filter to the specified location
    df = df[df.Location == city]

    all_types, to_show = get_plot_orders(df)

    # Plot the event rates by month and type as a line plot
    layout = go.Layout(
        xaxis_title="Month",
        yaxis_title="Event rate (per 1,000 movements)",
        legend_title="Event Type",
        title=f"2022 {city} Event Rates by Month and Type",
        yaxis_range=FIXED_Y_AXIS_RANGE,
    )
    fig_line = go.Figure(layout=layout)

    for e_type in all_types:
        this_df = df[df.Event_Type == e_type]
        fig_line.add_trace(
            go.Scatter(
                x=this_df.month,
                y=this_df.event_rate,
                visible="legendonly" if e_type not in to_show else None,
                name=e_type,
                marker_color=colour_map[e_type] if colour_map is not None else None,
            )
        )

    return fig_line


def get_event_rate_box_plot(
    df: pd.DataFrame,
    city: str = "All Cities",
    cities_as_data_points: bool = True,
    colour_map: dict = None,
) -> go.Figure:
    """This function takes in the DataFrame containing the movement and event data and generates the event type box plots.

    Args:
        df (pd.DataFrame): the processed data DataFrame with merged event and movement data.
        city (str, optional): the city to optionally filter to. Defaults to "All Cities".
        cities_as_data_points (bool, optional): whether to treat cities as individual data points in the box plots, only used when a city is not specified. Defaults to True.
        colour_map (dict, optional): a set colour map to specify event type colours. Defaults to None.

    Returns:
        go.Figure: A plotly graph object figure with the box plots.
    """

    # Filter to the specified location
    if city == "All Cities" and cities_as_data_points:
        df = df[df.Location != "All Cities"]
    else:
        df = df[df.Location == city]

    all_types, to_show = get_plot_orders(df)

    # Plot the monthly event rate distributions as type box plots
    layout = go.Layout(
        xaxis_title="Event Type",
        yaxis_title="Monthly event rate (per 1,000 movements)",
        legend_title="Event Type",
        title=f"2022 {city} Monthly Event Rate Box Plots by Type",
        yaxis_range=FIXED_Y_AXIS_RANGE,
    )
    fig_box = go.Figure(layout=layout)

    for e_type in all_types:
        this_df = df[df.Event_Type == e_type]
        fig_box.add_trace(
            go.Box(
                y=this_df.event_rate,
                visible="legendonly" if e_type not in to_show else None,
                name=e_type,
                marker_color=colour_map[e_type] if colour_map is not None else None,
            )
        )

    return fig_box


def main():
    """Main function for defining the streamlit web app.
    This includes 2 areas:
        - Exploratory Analysis:
            Generate line and box plots by event type and location
        - Discussion:
            The reponse content as included in the returned PDF outlining my insights.
    """

    if check_password():
        st.set_page_config(layout="wide", page_title="M.Trotter - Analysis")

        # Fake data warning
        st.markdown(
            "<h1 style='text-align: center; color:#8B0000; font-family:Monospace; font-size: 25px;'>// All data shown here is for analysis demonstration purposes only //</h1>",
            unsafe_allow_html=True,
        )

        # Title
        title_container = st.container()
        with title_container:
            name = '<p style="color:white; font-family:Monospace; font-size: 30px; margin-top: auto;">Michael Trotter - Senior Safety Data Analyst application, June 2023</p>'
            title = "Safety Data Analysis Exercise"
            title = f'<p style="color:white; font-family:Monospace; font-size: 20px; margin-top: auto;">{title}</p>'
            st.markdown(name, unsafe_allow_html=True)
            st.markdown(title, unsafe_allow_html=True)

        # Sidebar navigation
        tabs = st.sidebar.radio("Navigation", ("Exploratory Analysis", "Discussion"))

        # Data read from a pre-processed pickle file
        df = get_df(PROCESSED_DATA_PATH)

        # Define the colours to map to event types - this is being done very manually here for control over specific significant types
        e_types = df.Event_Type.unique()
        colours = ["#000000"] + (sns.color_palette().as_hex() * 3)[1:25]
        colour_map = dict(zip(e_types, colours))
        colour_map["Animal Strike"], colour_map["Loss of Separation"] = (
            colour_map["Loss of Separation"],
            colour_map["Animal Strike"],
        )
        colour_map["Laser"], colour_map["Malfunction of Aircraft System"] = (
            colour_map["Malfunction of Aircraft System"],
            colour_map["Laser"],
        )
        colour_map["Laser"], colour_map["Runway Incursion"] = (
            colour_map["Runway Incursion"],
            colour_map["Laser"],
        )

        if tabs == "Exploratory Analysis":
            st.markdown(
                "#### On this page you can freely explore the line and box plots for each location."
            )

            # City selection dropdown
            city_selction = st.selectbox(
                "Which locations would you like to display?",
                ("All Cities", "Blue City", "Green City", "Red City", "Yellow City"),
            )

            st.markdown("What type of plot would you like to display?")

            # Tabs for each plot type
            tab1, tab2 = st.tabs(
                ["Month - Event Type Line Plots", "Event Type Box Plots"]
            )

            display_note = "Note - 'Loss of Seperation' and 'Runway Incursion' events are displayed by default along with the five types with highest event rates. Others can be selected in the legend."

            with tab1:
                # Line plots
                fig_line = get_event_rate_line_plot(
                    df, city=city_selction, colour_map=colour_map
                )
                fig_line.update_layout(height=750, width=1200)
                st.plotly_chart(fig_line)

                st.write(display_note)

            with tab2:
                # Box plots
                if city_selction == "All Cities":
                    cities_as_data_points = st.checkbox(
                        "Treat cities as individual data points?", value=True
                    )
                    fig_box = get_event_rate_box_plot(
                        df,
                        city=city_selction,
                        cities_as_data_points=cities_as_data_points,
                        colour_map=colour_map,
                    )
                else:
                    fig_box = get_event_rate_box_plot(
                        df, city=city_selction, colour_map=colour_map
                    )

                fig_box.update_layout(height=750, width=1200)
                st.plotly_chart(fig_box)

                st.write(display_note)

        # Content for the discussion section of the web app, as covered in the response pdf.
        if tabs == "Discussion":
            '''Request - "Using the ... Reported Event and Aircraft Movement data, provide visualisations on the rate of events (per aircraft movement) at the four locations.
            Provide insight on any two event types and whether they involved civilian aircraft registered in Australia or overseas.
            Only present data for the 2022 calendar year (Jan-Dec)."'''

            st.subheader("Executive Summary")

            """There was a series of five 'Loss of Separation' (LOS) events in Green City on the 25th of February 2022. 
            Three of these events were for Australian registered aircraft, with the other two not recorded. 
            These events alone represent a rate of 0.46 LOS events per 1,000 aircraft movements for that month and location – 
            a monthly rate 56 times higher than the published Airservices' Tower LOS rates for the year to 28 February 2020."""
            """In Red City during May 2022 there were 42 'Facility Issue' events, at a rate of 2.70 events per 1,000 aircraft movements. 
            All events had an Aircraft_Register value of 'Not Applicable' with the exception of one which was for an Australian registered aircraft. 
            This is the single highest monthly event rate of any type across all four locations in 2022."""

            st.subheader("Data Overview")

            # Plot the basic rate of events by city bar chart
            rates_by_city = df[df.Event_Type == "All Types"].groupby(["Location"]).sum()
            rates_by_city.event_rate = rates_by_city.n_events / (
                rates_by_city.n_movements / 1000
            )

            colours = [
                "#646464",
                "#3274A1",
                "#3A923A",
                "#C03D3E",
                "#A7A859",
            ]  # Grey, Blue, Green, Red, Yellow (for the cities)
            labels = [round(r, 3) for r in rates_by_city.event_rate]
            fig_bar = go.Figure(
                data=go.Bar(
                    x=rates_by_city.index,
                    y=rates_by_city.event_rate,
                    marker=dict(color=colours),
                    text=labels,
                    textposition="outside",
                )
            )

            fig_bar.update_layout(
                title="Rate of Events – January to December 2022",
                xaxis=dict(title="Location"),
                yaxis=dict(title="Event rate (per 1,000 movements)"),
                yaxis_range=[0, max(rates_by_city.event_rate) + 0.5],
            )
            st.plotly_chart(fig_bar)

            if WRITE_PLOTS:
                pio.write_image(fig_bar, "fig_bar.png")

            """Shown above are the rates of events per 1,000 aircraft movements across each of the four cities, as well as the combined rate of events. """
            """While the above plot provides an overview of the rate of events by location, it fails to differentiate event type and monthly patterns. 
            On the following page are the box plots for the event rate distributions for each type. The data points contributing to the distributions are the event rates for that type, month, and city. """

            # Plot the monthly event rate distributions as type box plots
            temp_df = df[df.Location != "All Cities"]
            type_order, _ = get_plot_orders(df)

            layout = go.Layout(
                xaxis_title="Event Type",
                yaxis_title="Monthly event rate (per 1,000 movements)",
                legend_title="Event Type",
                title=f"2022 Monthly Event Rate Box Plots – All Locations",
                yaxis_range=[0, 3],
                height=750,
                width=1200,
            )
            fig_box = go.Figure(layout=layout)

            for e_type in type_order[1:]:
                this_df = temp_df[temp_df.Event_Type == e_type]
                fig_box.add_trace(
                    go.Box(
                        y=this_df.event_rate,
                        name=e_type,
                        marker_color=colour_map[e_type],
                    )
                )
            fig_box.update_xaxes(automargin=True)
            st.plotly_chart(fig_box)

            if WRITE_PLOTS:
                fig_box.update_layout(showlegend=False)
                pio.write_image(fig_box, "fig_box.png")

            """Looking at the box plots on the previous page, there is a clear outlier of 2.70 events per 1,000 aircraft movements for 'Facility Issues'. 
            However, there is also a less obvious though more significant outlier at 0.46 events per 1,000 aircraft movements for 'Loss of Separation' (LOS). 
            These values occur in Red City during May 2022 and Green City during February 2022 respectively.\n
            
            From 'AIR NAVIGATION SERVICES OPERATIONAL SAFETY REPORTING AND PERFORMANCE LONG-TERM TRENDS' (May 2020):
                Whilst we use a wide range of metrics to validate our performance, the following two internationally used benchmark metrics are our 
                key indicators of our safety performance:
                • the required separation standard between aircraft or a restricted airspace volume is infringed (Loss of Separations (LOS))
                • an unauthorised aircraft, vehicle or person is on a runway (Runway Incursions)."""

            """Discussed below, because of its relevance as a benchmark and significant safety metric, are the Green City LOS events, 
            as well as the Red City Facility Issue events which represent the most significant outlier."""

            st.subheader("25th of February Loss of Separation Events - Green City")

            # Filter to the specified location
            temp_df = df[df.Location == "Green City"]
            _, to_show = get_plot_orders(temp_df)

            # Plot the event rates by month and type as a line plot
            layout = go.Layout(
                xaxis_title="Month",
                yaxis_title="Event rate (per 1,000 movements)",
                legend_title="Event Type",
                title=f"2022 Green City Event Rates by Month and Type",
                yaxis_range=[0, 2.5],
                height=750,
                width=1200,
            )
            fig_line_green = go.Figure(layout=layout)

            for e_type in to_show:
                this_df = temp_df[temp_df.Event_Type == e_type]
                fig_line_green.add_trace(
                    go.Scatter(
                        x=this_df.month,
                        y=this_df.event_rate,
                        name=e_type,
                        marker_color=colour_map[e_type],
                    )
                )

            st.plotly_chart(fig_line_green)

            if WRITE_PLOTS:
                pio.write_image(fig_line_green, "fig_line_green.png")

            """Shown above are the 2022 event rates per 1,000 aircraft movements for Green City. 
            Displayed are the values for 'All Types', 'Loss of Separation', 'Runway Incursion', and five other types with the next highest single-month event rates."""
            """We can see the February LOS events at a rate of 0.46 in red and in the bottom-left of the plot. 
            If we assume that the events and locations in this data relate to Tower services, 0.46 is approximately 56 times higher than Airservices' Tower LOS rates for the year to 28 February 2020."""

            """Shown below are the 2022 Green City LOS event details selected from the data. Significantly, all occurred on the same date – the 25th of February."""

            # Show the LOS table with events
            selected_df = get_df(SELECTED_DATA_PATH)[
                ["Event_Date", "Event_Type", "Aircraft_Register", "Location"]
            ]
            los_events = selected_df[selected_df.Event_Type == "Loss of Separation"]
            green_los = los_events[los_events.Location == "Green City"]
            st.dataframe(green_los)

            if WRITE_PLOTS:
                green_los.to_csv("green_city_los.csv")

            """Of those events, three have a recorded value for 'Aircraft_Register' and all three were Australian registered."""
            """The obvious conclusion is that there was a break-down in safety processes on that day that would be worth investigating further. """
            """Finally, worth noting is that Yellow City had no LOS events, Red City had only one, while Blue City accounted for 50% of all LOS events in 2022. This makes Blue City’s rate of LOS events ~2.75 times higher than the 2019-2020 published figures."""

            # Show the LOS counts table
            los_counts = (
                los_events.groupby(["Location"])
                .count()[["Event_Date"]]
                .rename(columns={"Event_Date": "LOS Event Count"})
                .reset_index()
            )
            st.dataframe(los_counts)

            if WRITE_PLOTS:
                los_counts.to_csv("los_counts.csv")

            st.subheader("Facility Issues - Red City")

            # Filter to the specified location
            temp_df = df[df.Location == "Red City"]
            _, to_show = get_plot_orders(temp_df)

            # Plot the event rates by month and type as a line plot
            layout = go.Layout(
                xaxis_title="Month",
                yaxis_title="Event rate (per 1,000 movements)",
                legend_title="Event Type",
                title=f"2022 Red City Event Rates by Month and Type",
                yaxis_range=FIXED_Y_AXIS_RANGE,
                height=750,
                width=1200,
            )
            fig_line_red = go.Figure(layout=layout)

            for e_type in to_show:
                this_df = temp_df[temp_df.Event_Type == e_type]
                fig_line_red.add_trace(
                    go.Scatter(
                        x=this_df.month,
                        y=this_df.event_rate,
                        name=e_type,
                        marker_color=colour_map[e_type],
                    )
                )

            st.plotly_chart(fig_line_red)

            if WRITE_PLOTS:
                pio.write_image(fig_line_red, "fig_line_red.png")

            """Shown above are the 2022 event rates per 1,000 aircraft movements for Red City. 
            Displayed are the values for 'All Types', 'Loss of Separation', 'Runway Incursion', 
            and five other types with the next highest single-month event rates. 
            Notable here is the significant increase in ‘Facility Issue’ events during May."""

            """At 2.70 events per 1,000 aircraft movements, this is the single highest monthly event rate of any type across all four locations."""

            """Of the 42 'Facility Issue' events for Red City in May 2022, only one had an Aircraft_Register 
            value of anything other than 'Not Applicable', this was for an Australian registered aircraft."""

            # Show the facility issue table
            fac_events = selected_df[selected_df.Event_Type == "Facility Issue"]
            fac_counts = (
                fac_events.groupby("Aircraft_Register")
                .count()[["Location"]]
                .rename(columns={"Location": "Facility Issue Event Count"})
            )
            st.dataframe(fac_counts)

            if WRITE_PLOTS:
                fac_counts.to_csv("fac_counts.csv")

            """Further information relating to the cause of these figures is not given in the provided data, 
            but presumably this would be worth investigating further. """


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        """Safety Data Analysis Exercise - June 2023"""
        """Please provide the password"""
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True


if __name__ == "__main__":
    main()
